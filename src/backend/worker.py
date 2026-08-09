import os
import uuid
import json
from datetime import timedelta
from celery import Celery
from sqlalchemy.orm import Session

from src.backend.core.config import settings
from src.backend.core.database import SessionLocal
from src.backend.core.logging import get_logger
from src.backend.models.renders import RenderJobModel
from src.backend.models.matches import MatchModel
from src.backend.models.base import utc_now
from src.backend.services.ingestion import MatchIngestionService

import ssl

logger = get_logger("dota.worker")

redis_url = settings.normalized_redis_url

# Initialize Celery app
celery_app = Celery(
    "dota_worker",
    broker=redis_url,
    backend=redis_url
)

celery_conf = {
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "timezone": "UTC",
    "enable_utc": True,
    "task_track_started": True,
}

if redis_url.startswith("rediss://"):
    ssl_opts = {"ssl_cert_reqs": ssl.CERT_REQUIRED}
    celery_conf["broker_use_ssl"] = ssl_opts
    celery_conf["redis_backend_use_ssl"] = ssl_opts

celery_app.conf.update(**celery_conf)

def process_render_job(job_id: str, db: Session):
    """
    Core render processing logic executed by worker or fallback thread.
    Renders video, updates progress, and saves output MP4 file.
    """
    job = db.query(RenderJobModel).filter_by(job_id=job_id).first()
    if not job:
        logger.error(f"Render job {job_id} not found in database.")
        return

    try:
        logger.info(f"Starting render job {job_id} for player {job.player_id}")
        job.status = "PROCESSING"
        job.progress = 15
        db.commit()

        # Ensure output directory exists
        output_dir = settings.EPHEMERAL_STORAGE_DIR
        os.makedirs(output_dir, exist_ok=True)
        output_filename = f"{job.job_id}.mp4"
        output_filepath = os.path.abspath(os.path.join(output_dir, output_filename))

        # Check if matches exist, else sync
        matches_count = db.query(MatchModel).filter_by(player_id=job.player_id).count()
        if matches_count == 0:
            logger.info(f"No matches cached for player {job.player_id}, syncing from OpenDota...")
            MatchIngestionService.sync_player_matches(db, job.player_id)

        job.progress = 40
        db.commit()

        matches_raw = db.query(MatchModel).filter_by(player_id=job.player_id).order_by(MatchModel.start_time.asc()).all()
        matches_dicts = [json.loads(m.raw_json) for m in matches_raw if m.raw_json]

        if not matches_dicts:
            raise ValueError(f"No match history found for player {job.player_id}")

        job.progress = 60
        db.commit()

        from src.data.api import DotaAPI
        from src.data.strategies import (
            MatchesPlayedStrategy, WinsStrategy, WinRateStrategy, Top20WinRateStrategy,
            ItemRaceStrategy, RoleEvolutionStrategy, KDAStrategy, TowerDamageStrategy, 
            LaneStrategy, DamageDealtStrategy, TotalDeathsStrategy, TotalGoldStrategy,
            HeroImpactStrategy, MultiKillStrategy, FarmingEfficiencyStrategy,
            WinStreakStrategy, RoshanClaimsStrategy, BlitzWinsStrategy
        )
        from src.visualizer.engine import VideoEngine

        strategy_map = {
            "Matches Played": MatchesPlayedStrategy,
            "Hero Masteries": MatchesPlayedStrategy,
            "Total Wins": WinsStrategy,
            "Win Rate % (Top 20 Mains)": Top20WinRateStrategy,
            "Most Purchased Items": ItemRaceStrategy,
            "Role Evolution": RoleEvolutionStrategy,
            "KDA Ratio (Efficiency)": KDAStrategy,
            "Tower Damage (Thousands)": TowerDamageStrategy,
            "Laning Preference": LaneStrategy,
            "Total Damage (Millions)": DamageDealtStrategy,
            "Total Deaths": TotalDeathsStrategy,
            "Total Gold (Millions)": TotalGoldStrategy,
            "Hero Impact Score": HeroImpactStrategy,
            "Multi-Kill & Rampage Race": MultiKillStrategy,
            "GPM Farming Efficiency": FarmingEfficiencyStrategy,
            "Win Streak Master": WinStreakStrategy,
            "Roshan & Aegis Claims": RoshanClaimsStrategy,
            "Blitz Stomper (Fastest Victory)": BlitzWinsStrategy
        }

        metric_name = job.metric or "Hero Impact Score"
        strategy_class = strategy_map.get(metric_name, HeroImpactStrategy)
        strategy = strategy_class()

        hero_map = DotaAPI.get_hero_map()
        df, start_year = strategy.process(matches_dicts, hero_map)

        if df.empty or len(df) < 2:
            raise ValueError(f"Insufficient time-series data for '{metric_name}'. At least 2 active months required.")

        job.progress = 75
        db.commit()

        # Render video using VideoEngine
        aspect_ratio = job.aspect_ratio or "9:16"
        theme = job.theme or "Midnight Cyberpunk"
        
        quality_settings = {
            "Draft":  {"steps": 10, "period": 1000, "dpi": 80},
            "Normal": {"steps": 20, "period": 1500, "dpi": 100},
            "High":   {"steps": 40, "period": 2000, "dpi": 120},
            "Ultra":  {"steps": 60, "period": 2500, "dpi": 144}
        }.get(job.quality or "Normal", {"steps": 20, "period": 1500, "dpi": 100})

        from src.backend.models.matches import PlayerProfileModel
        profile_obj = db.query(PlayerProfileModel).filter_by(player_id=job.player_id).first()
        player_name = profile_obj.personaname if (profile_obj and profile_obj.personaname) else f"Player #{job.player_id}"

        temp_path = os.path.abspath(os.path.join(output_dir, f"temp_{output_filename}"))
        video_title = f"{player_name}\n{strategy.name} ({start_year}-Present)"

        def worker_progress(p):
            # Map progress p (0.0 to 1.0) to 75% -> 95%
            job.progress = min(95, int(75 + p * 20))
            try:
                db.commit()
            except Exception:
                pass

        VideoEngine.render_race(
            df,
            temp_path,
            title=video_title,
            progress_callback=worker_progress,
            steps_per_period=quality_settings['steps'],
            period_length=quality_settings['period'],
            dpi=quality_settings['dpi'],
            aspect_ratio=aspect_ratio,
            theme_name=theme,
            patch_overlay=True
        )

        # Add Audio & Finalize Video
        VideoEngine.add_audio(temp_path, output_filepath, music_file=job.custom_audio_id)
        if os.path.exists(temp_path):
            os.remove(temp_path)

        # Set job completion details
        expires_at = utc_now() + timedelta(seconds=settings.EPHEMERAL_TTL_SECONDS)
        
        job.status = "COMPLETED"
        job.progress = 100
        job.file_path = output_filepath
        job.video_url = f"/api/v1/render/media/{output_filename}"
        job.expires_at = expires_at
        db.commit()

        logger.info(f"Render job {job_id} successfully completed. Output: {output_filepath}")

    except Exception as e:
        logger.error(f"Render job {job_id} failed: {e}", exc_info=True)
        job.status = "FAILED"
        job.progress = 0
        job.error_message = str(e)
        db.commit()

@celery_app.task(name="dota.render_video_task")
def render_video_task(job_id: str):
    """Celery async task wrapper."""
    db = SessionLocal()
    try:
        process_render_job(job_id, db)
    finally:
        db.close()
