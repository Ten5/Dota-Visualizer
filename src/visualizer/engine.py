import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import bar_chart_race as bcr
from matplotlib.animation import FFMpegWriter
import os
import random
from PIL import Image
from moviepy.editor import VideoFileClip, AudioFileClip, afx, concatenate_videoclips

class ProgressVideoWriter(FFMpegWriter):
    def __init__(self, total_frames, on_progress, **kwargs):
        super().__init__(**kwargs)
        self.total_frames = total_frames
        self.on_progress = on_progress
        self.frame_count = 0

    def grab_frame(self, **kwargs):
        super().grab_frame(**kwargs)
        self.frame_count += 1
        if self.on_progress:
            percent = min(self.frame_count / self.total_frames, 1.0)
            self.on_progress(percent)

class VideoEngine:
    @staticmethod
    def render_race(df, output_path, title, avatar_img=None, n_bars=20, progress_callback=None,
                    steps_per_period=50, 
                    period_length=2500, 
                    dpi=120):
        STEPS_PER_PERIOD = steps_per_period 
        PERIOD_LENGTH = period_length
        DPI = dpi
        plt.style.use('dark_background')
        
        fig, ax = plt.subplots(figsize=(10, 6), dpi=DPI)
        fig.patch.set_facecolor('#1b1b1b')
        ax.set_facecolor('#1b1b1b')
        
        # Shift left margin to make room for Icons + Names
        plt.subplots_adjust(left=0.30, right=0.95, top=0.9, bottom=0.1)
        
        if avatar_img:
            avatar_img.thumbnail((100, 100), Image.Resampling.LANCZOS)
            fig.figimage(avatar_img, xo=fig.bbox.xmax - 130, yo=fig.bbox.ymax - 130, zorder=10)

        df.index = df.index.strftime('%B %Y')
        total_estimated_frames = len(df) * STEPS_PER_PERIOD
        
        writer = ProgressVideoWriter(
            total_frames=total_estimated_frames,
            on_progress=progress_callback,
            fps=20
        )

        bcr.bar_chart_race(
            df=df,
            filename=output_path,
            orientation='h',
            sort='desc',
            n_bars=n_bars,
            steps_per_period=STEPS_PER_PERIOD,
            period_length=PERIOD_LENGTH,
            title=title,
            fig=fig,
            writer=writer,
            filter_column_colors=True,
            # REMOVED: 'cmap' (Causes crash on standard lib)
            # REMOVED: 'img_label_folder' (Handled by our patch now)
            
            period_fmt='{x}',
            period_label={'x': 0.99, 'y': 0.25, 'ha': 'right', 'va': 'center', 'size': 12, 'weight': 'bold', 'color': 'white'},
            bar_size=0.9,
            bar_label_size=8,
            tick_label_size=8,
            shared_fontdict={'family': 'DejaVu Sans', 'weight': 'normal', 'color': 'white'}
        )
        plt.close(fig)

    @staticmethod
    def add_audio(video_path, final_path, music_dir="assets/music"):
        os.makedirs(music_dir, exist_ok=True)
        music_files = [f for f in os.listdir(music_dir) if f.endswith(".mp3")]
        
        original_clip = VideoFileClip(video_path)
        last_frame = original_clip.to_ImageClip(t=original_clip.duration - 0.05).set_duration(2)
        extended_clip = concatenate_videoclips([original_clip, last_frame])
        
        if music_files:
            track = random.choice(music_files)
            audio_path = os.path.join(music_dir, track)
            audio_clip = AudioFileClip(audio_path)
            if audio_clip.duration < extended_clip.duration:
                audio_clip = afx.audio_loop(audio_clip, duration=extended_clip.duration)
            audio_clip = audio_clip.subclip(0, extended_clip.duration).audio_fadeout(3)
            final_clip = extended_clip.set_audio(audio_clip)
            final_clip.write_videofile(final_path, codec="libx264", audio_codec="aac")
            audio_clip.close()
            final_clip.close()
        else:
            extended_clip.write_videofile(final_path, codec="libx264")
            extended_clip.close()
            
        original_clip.close()