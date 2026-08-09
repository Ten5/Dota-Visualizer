import cv2
import numpy as np
import pandas as pd
import subprocess
import os
import platform
import random
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, AudioFileClip, afx, concatenate_videoclips

# Curated palette of 32 vibrant, distinct colors for bar chart races
COLOR_PALETTE = [
    (245, 101, 101), (237, 137, 54), (236, 201, 75), (72, 187, 120),
    (56, 178, 172), (66, 153, 225), (102, 126, 234), (159, 122, 234),
    (237, 100, 166), (245, 158, 11), (16, 185, 129), (59, 130, 246),
    (139, 92, 246), (236, 72, 153), (20, 184, 166), (249, 115, 22),
    (239, 68, 68),   (249, 115, 22), (234, 179, 8),   (132, 204, 22),
    (34, 197, 94),   (6, 182, 212),  (14, 165, 233),  (99, 102, 241),
    (168, 85, 247),  (217, 70, 239), (244, 63, 94),   (251, 146, 60),
    (250, 204, 21),  (74, 222, 128), (45, 212, 191),  (56, 189, 248)
]

def load_font(size, bold=False):
    """Loads clean, scalable TrueType font with fallbacks."""
    font_names = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
        "Arial.ttf",
        "DejaVuSans.ttf"
    ]
    for font_path in font_names:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                pass
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()

def get_hero_image_path(name, folder="assets/hero_images"):
    """Finds image file for a hero name."""
    if not name or not isinstance(name, str): return None
    path = os.path.join(folder, f"{name}.png")
    if os.path.exists(path): return path
    safe_name = name.replace("/", "_")
    path = os.path.join(folder, f"{safe_name}.png")
    if os.path.exists(path): return path
    return None

def get_best_ffmpeg_codec():
    """Detects hardware accelerated video encoder based on OS."""
    system = platform.system()
    if system == "Darwin":
        return "h264_videotoolbox"
    return "libx264"

from src.data.strategies import get_dota_patch_name

COLOR_THEMES = {
    "Dire Crimson": {
        "bg": (15, 23, 42, 255),
        "text_header": (255, 255, 255, 255),
        "text_sub": (148, 163, 184, 255),
        "date_color": (248, 250, 252, 255),
        "patch_color": (239, 68, 68, 255)
    },
    "Radiant Gold": {
        "bg": (15, 23, 42, 255),
        "text_header": (255, 255, 255, 255),
        "text_sub": (148, 163, 184, 255),
        "date_color": (248, 250, 252, 255),
        "patch_color": (245, 158, 11, 255)
    },
    "Midnight Cyberpunk": {
        "bg": (11, 14, 20, 255),
        "text_header": (255, 255, 255, 255),
        "text_sub": (148, 163, 184, 255),
        "date_color": (248, 250, 252, 255),
        "patch_color": (244, 63, 94, 255)
    }
}

class VideoEngine:
    @staticmethod
    def render_race(df, output_path, title, avatar_img=None, n_bars=10, progress_callback=None,
                    steps_per_period=20, period_length=1500, dpi=100,
                    aspect_ratio="16:9", theme_name="Dire Crimson", patch_overlay=True):
        """
        Blazing-fast native OpenCV renderer for Bar Chart Race animations.
        Pipes BGR frames directly to FFmpeg with Hardware Acceleration.
        Supports 16:9 Landscape and 9:16 Vertical Shorts layouts with UI Themes.
        """
        if df.empty or len(df) < 2:
            raise ValueError("DataFrame must contain at least 2 periods for animation.")

        if aspect_ratio == "9:16":
            width, height = 720, 1280
            chart_top, chart_bottom = 260, 1200
            chart_left, chart_right = 40, 680
        else:
            width, height = 1280, 720
            chart_top, chart_bottom = 205, 685
            chart_left, chart_right = 60, 1100

        chart_width = chart_right - chart_left
        slot_height = (chart_bottom - chart_top) / n_bars
        bar_height = int(slot_height * 0.74)
        fps = 30

        theme = COLOR_THEMES.get(theme_name, COLOR_THEMES["Dire Crimson"])
        cols = list(df.columns)
        color_map = {col: COLOR_PALETTE[i % len(COLOR_PALETTE)] for i, col in enumerate(cols)}

        font_title = load_font(30 if aspect_ratio == "9:16" else 32, bold=True)
        font_subtitle = load_font(16 if aspect_ratio == "9:16" else 18, bold=False)
        font_date = load_font(26 if aspect_ratio == "9:16" else 30, bold=True)
        font_patch = load_font(20 if aspect_ratio == "9:16" else 24, bold=True)
        font_bar_name = load_font(18 if aspect_ratio == "9:16" else 20, bold=True)
        font_val = load_font(18 if aspect_ratio == "9:16" else 20, bold=True)

        icon_cache = {}
        for col in cols:
            img_path = get_hero_image_path(str(col))
            if img_path:
                try:
                    img = Image.open(img_path).convert("RGBA")
                    img = img.resize((32, 32), Image.Resampling.LANCZOS)
                    icon_cache[col] = img
                except Exception:
                    pass

        avatar_cv = None
        if avatar_img:
            try:
                av = avatar_img.convert("RGBA").resize((70, 70), Image.Resampling.LANCZOS)
                avatar_cv = np.array(av)
            except Exception:
                pass

        codec = get_best_ffmpeg_codec()
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-s', f'{width}x{height}',
            '-pix_fmt', 'bgr24',
            '-r', str(fps),
            '-i', '-',
            '-c:v', codec,
            '-pix_fmt', 'yuv420p',
            output_path
        ]

        try:
            proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
        except Exception:
            ffmpeg_cmd[13] = 'libx264'
            proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

        num_periods = len(df) - 1
        raw_dates = list(df.index)
        date_labels = [idx.strftime('%B %Y') if hasattr(idx, 'strftime') else str(idx) for idx in raw_dates]

        period_steps_list = []
        for p in range(num_periods):
            v1 = df.iloc[p].values.astype(float)
            v2 = df.iloc[p + 1].values.astype(float)
            delta_val = np.sum(np.abs(v2 - v1))
            
            if delta_val < 1e-4:
                st = max(int(steps_per_period * 0.25), 4)
            elif delta_val < 5.0:
                st = max(int(steps_per_period * 0.60), 8)
            elif delta_val > 35.0:
                st = int(steps_per_period * 1.5)
            else:
                st = steps_per_period
            period_steps_list.append(st)

        total_frames = sum(period_steps_list)
        frame_index = 0

        for p in range(num_periods):
            v_start = df.iloc[p].values.astype(float)
            v_end = df.iloc[p + 1].values.astype(float)
            date_str = date_labels[p + 1].upper()
            patch_str = get_dota_patch_name(raw_dates[p + 1]) if patch_overlay else ""
            curr_steps = period_steps_list[p]

            order_start = np.argsort(-v_start)
            ranks_start = np.empty_like(order_start, dtype=float)
            ranks_start[order_start] = np.arange(len(v_start), dtype=float)

            order_end = np.argsort(-v_end)
            ranks_end = np.empty_like(order_end, dtype=float)
            ranks_end[order_end] = np.arange(len(v_end), dtype=float)

            for s in range(curr_steps):
                alpha = s / float(curr_steps)
                ease_alpha = 3.0 * (alpha ** 2) - 2.0 * (alpha ** 3)

                v_curr = v_start * (1.0 - alpha) + v_end * alpha
                ranks_curr = ranks_start * (1.0 - ease_alpha) + ranks_end * ease_alpha

                active_indices = [idx for idx in range(len(cols)) if min(ranks_start[idx], ranks_end[idx]) < n_bars + 1.5]
                active_indices.sort(key=lambda idx: ranks_curr[idx])

                max_val = max(v_curr[active_indices[:n_bars]].max(), 1e-5) if active_indices else 1.0

                canvas_img = Image.new("RGBA", (width, height), theme["bg"])
                draw = ImageDraw.Draw(canvas_img)

                # Draw Avatar Image (Left of Title)
                title_x = 30 if aspect_ratio == "9:16" else 40
                if avatar_cv is not None:
                    av_pil = Image.fromarray(avatar_cv)
                    canvas_img.paste(av_pil, (title_x, 20), av_pil)
                    title_x += 85

                title_lines = title.split('\n')
                draw.text((title_x, 15), title_lines[0], font=font_title, fill=theme["text_header"])
                if len(title_lines) > 1:
                    draw.text((title_x, 50), title_lines[1], font=font_subtitle, fill=theme["text_sub"])

                # Date & Patch Overlay (Stacked vertically with generous buffer space above top bar)
                date_x = title_x
                if patch_str:
                    draw.text((date_x, 82 if aspect_ratio == "9:16" else 78), patch_str, font=font_patch, fill=theme["patch_color"])
                    draw.text((date_x, 112 if aspect_ratio == "9:16" else 105), date_str, font=font_date, fill=theme["date_color"])
                else:
                    draw.text((date_x, 90 if aspect_ratio == "9:16" else 85), date_str, font=font_date, fill=theme["date_color"])

                for idx in active_indices:
                    rank_pos = ranks_curr[idx]
                    if rank_pos > n_bars + 0.5:
                        continue

                    val = v_curr[idx]
                    col_name = str(cols[idx])
                    rgb_color = color_map[cols[idx]]

                    y_pos = int(chart_top + rank_pos * slot_height)
                    bar_w = int((max(val, 0) / max_val) * chart_width)
                    bar_w = max(bar_w, 4)

                    bar_box = [chart_left, y_pos, chart_left + bar_w, y_pos + bar_height]
                    draw.rectangle(bar_box, fill=rgb_color + (255,))

                    icon_present = col_name in icon_cache
                    if icon_present:
                        icon = icon_cache[col_name]
                        canvas_img.paste(icon, (chart_left + 8, y_pos + (bar_height - 32) // 2), icon)

                    text_x = chart_left + (46 if icon_present else 16)
                    text_y = y_pos + (bar_height - 24) // 2
                    
                    draw.text((text_x + 1, text_y + 1), col_name, font=font_bar_name, fill=(0, 0, 0, 220))
                    draw.text((text_x, text_y), col_name, font=font_bar_name, fill=(255, 255, 255, 255))

                    if "%" in title or "Win Rate" in title:
                        label_txt = f"{val:.1f}%"
                    elif "KDA" in title or "Efficiency" in title:
                        label_txt = f"{val:.2f}"
                    elif "Millions" in title or "Damage" in title or "Gold" in title:
                        label_txt = f"{val:.2f}M"
                    elif "Thousands" in title or "Tower" in title:
                        label_txt = f"{val:.1f}k"
                    else:
                        label_txt = f"{val:,.0f}"

                    val_x = chart_left + bar_w + 12
                    draw.text((val_x, text_y), label_txt, font=font_val, fill=(255, 255, 255, 255))

                frame_bgr = cv2.cvtColor(np.array(canvas_img), cv2.COLOR_RGBA2BGR)
                proc.stdin.write(frame_bgr.tobytes())

                frame_index += 1
                if progress_callback and total_frames > 0:
                    progress_callback(min(frame_index / total_frames, 1.0))

        proc.stdin.close()
        proc.wait()

    @staticmethod
    def generate_preview_frame(df, frame_idx=-1, title="Preview", avatar_img=None, n_bars=10,
                               theme_name="Dire Crimson", aspect_ratio="16:9", patch_overlay=True):
        """Generates a single PIL Image frame for real-time GUI previewing."""
        if df.empty:
            return Image.new("RGBA", (400, 225), (20, 20, 28, 255))

        if aspect_ratio == "9:16":
            width, height = 720, 1280
            chart_top, chart_bottom = 220, 1150
            chart_left, chart_right = 40, 680
        else:
            width, height = 1280, 720
            chart_top, chart_bottom = 130, 650
            chart_left, chart_right = 60, 1100

        chart_width = chart_right - chart_left
        slot_height = (chart_bottom - chart_top) / n_bars
        bar_height = int(slot_height * 0.74)

        theme = COLOR_THEMES.get(theme_name, COLOR_THEMES["Dire Crimson"])
        cols = list(df.columns)
        color_map = {col: COLOR_PALETTE[i % len(COLOR_PALETTE)] for i, col in enumerate(cols)}

        font_title = load_font(32 if aspect_ratio == "9:16" else 34, bold=True)
        font_subtitle = load_font(18 if aspect_ratio == "9:16" else 20, bold=False)
        font_date = load_font(44 if aspect_ratio == "9:16" else 54, bold=True)
        font_patch = load_font(20 if aspect_ratio == "9:16" else 24, bold=True)
        font_bar_name = load_font(18 if aspect_ratio == "9:16" else 20, bold=True)
        font_val = load_font(18 if aspect_ratio == "9:16" else 20, bold=True)

        idx = frame_idx if frame_idx >= 0 else len(df) - 1
        row = df.iloc[idx]
        raw_date = df.index[idx]
        date_str = raw_date.strftime('%B %Y').upper() if hasattr(raw_date, 'strftime') else str(raw_date).upper()
        patch_str = get_dota_patch_name(raw_date) if patch_overlay else ""

        ranks = np.argsort(-row.values)
        sorted_indices = ranks[:n_bars]
        max_val = max(row.values[sorted_indices].max(), 1e-5) if len(sorted_indices) > 0 else 1.0

        canvas_img = Image.new("RGBA", (width, height), theme["bg"])
        draw = ImageDraw.Draw(canvas_img)

        title_lines = title.split('\n')
        draw.text((30 if aspect_ratio == "9:16" else 50, 25), title_lines[0], font=font_title, fill=theme["text_header"])
        if len(title_lines) > 1:
            draw.text((30 if aspect_ratio == "9:16" else 50, 70), title_lines[1], font=font_subtitle, fill=theme["text_sub"])

        date_x = width - (320 if aspect_ratio == "9:16" else 420)
        date_y = height - (110 if aspect_ratio == "9:16" else 95)
        draw.text((date_x, date_y), date_str, font=font_date, fill=theme["date_color"])
        if patch_str:
            draw.text((date_x, date_y - 28), patch_str, font=font_patch, fill=theme["patch_color"])

        for rank_pos, col_idx in enumerate(sorted_indices):
            val = row.values[col_idx]
            col_name = str(cols[col_idx])
            rgb_color = color_map[cols[col_idx]]

            y_pos = int(chart_top + rank_pos * slot_height)
            bar_w = int((max(val, 0) / max_val) * chart_width)
            bar_w = max(bar_w, 4)

            draw.rectangle([chart_left, y_pos, chart_left + bar_w, y_pos + bar_height], fill=rgb_color + (255,))
            text_x = chart_left + 16
            text_y = y_pos + (bar_height - 24) // 2
            draw.text((text_x + 1, text_y + 1), col_name, font=font_bar_name, fill=(0, 0, 0, 220))
            draw.text((text_x, text_y), col_name, font=font_bar_name, fill=(255, 255, 255, 255))
            draw.text((chart_left + bar_w + 12, text_y), f"{val:,.0f}", font=font_val, fill=(255, 255, 255, 255))

        return canvas_img

    @staticmethod
    def add_audio(video_path, final_path, music_file=None, music_dir="assets/music"):
        """Extends video with 2-second result buffer and layers background audio."""
        os.makedirs(music_dir, exist_ok=True)
        audio_path = None
        if music_file and os.path.exists(music_file):
            audio_path = music_file
        else:
            music_files = [f for f in os.listdir(music_dir) if f.endswith(".mp3")]
            if music_files:
                audio_path = os.path.join(music_dir, random.choice(music_files))
        
        original_clip = VideoFileClip(video_path)
        last_frame = original_clip.to_ImageClip(t=max(original_clip.duration - 0.05, 0)).set_duration(2)
        extended_clip = concatenate_videoclips([original_clip, last_frame])
        
        if audio_path:
            audio_clip = AudioFileClip(audio_path)
            if audio_clip.duration < extended_clip.duration:
                audio_clip = afx.audio_loop(audio_clip, duration=extended_clip.duration)
            audio_clip = audio_clip.subclip(0, extended_clip.duration).audio_fadeout(3)
            final_clip = extended_clip.set_audio(audio_clip)
            final_clip.write_videofile(final_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)
            audio_clip.close()
            final_clip.close()
        else:
            extended_clip.write_videofile(final_path, codec="libx264", verbose=False, logger=None)
            extended_clip.close()
            
        original_clip.close()