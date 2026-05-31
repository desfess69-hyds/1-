"""Step 4: FFmpeg로 씬 영상 합치고 내레이션 + 상단 1/3 자막 burn-in + BGM 믹스."""
import os
import re
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

KOREAN_FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
BGM_DIR = Path(__file__).parent / "bgm"
BGM_VOLUME = float(os.environ.get("BGM_VOLUME", "0.18"))


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed:\nCMD: {' '.join(cmd)}\nSTDERR:\n{result.stderr}"
        )


def _ffprobe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def _ffprobe_size(path: Path) -> tuple[int, int]:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0:s=x",
            str(path),
        ],
        capture_output=True, text=True, check=True,
    )
    w, h = result.stdout.strip().split("x")
    return int(w), int(h)


def _concat_videos(video_paths: list[Path], output: Path) -> None:
    concat_file = output.parent / "_video_concat.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for p in video_paths:
            f.write(f"file '{p.absolute()}'\n")
    _run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-an",
        str(output),
    ])
    concat_file.unlink(missing_ok=True)


def _trim_or_pad_clip(src: Path, target_sec: float, dst: Path) -> None:
    src_sec = _ffprobe_duration(src)
    if target_sec <= src_sec + 0.05:
        # trim
        _run([
            "ffmpeg", "-y",
            "-i", str(src),
            "-t", f"{target_sec:.3f}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-pix_fmt", "yuv420p", "-an",
            str(dst),
        ])
    else:
        # extend by holding the final frame
        hold = target_sec - src_sec
        _run([
            "ffmpeg", "-y",
            "-i", str(src),
            "-vf",
            f"tpad=stop_mode=clone:stop_duration={hold:.3f}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-pix_fmt", "yuv420p", "-an",
            str(dst),
        ])


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    chunks = re.split(r"(\s+)", text)
    lines: list[str] = []
    current = ""
    for chunk in chunks:
        candidate = current + chunk
        bbox = draw.textbbox((0, 0), candidate, font=font)
        w = bbox[2] - bbox[0]
        if w > max_width and current.strip():
            lines.append(current.strip())
            current = chunk.lstrip()
        else:
            current = candidate
    if current.strip():
        lines.append(current.strip())

    # If a single chunk is still too wide (long unbroken Korean run), hard-wrap by character.
    final: list[str] = []
    for ln in lines:
        bbox = draw.textbbox((0, 0), ln, font=font)
        if bbox[2] - bbox[0] <= max_width:
            final.append(ln)
            continue
        buf = ""
        for ch in ln:
            test = buf + ch
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] > max_width and buf:
                final.append(buf)
                buf = ch
            else:
                buf = test
        if buf:
            final.append(buf)
    return final


def _render_subtitle_png(text: str, video_w: int, video_h: int, out_path: Path) -> None:
    band_h = video_h // 3  # top 1/3 of frame
    img = Image.new("RGBA", (video_w, band_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_size = max(36, int(video_w * 0.058))
    font = ImageFont.truetype(KOREAN_FONT, font_size)

    max_text_width = int(video_w * 0.86)
    lines = _wrap_text(draw, text, font, max_text_width)

    line_gap = int(font_size * 0.35)
    line_h = font_size + line_gap
    total_h = len(lines) * line_h - line_gap
    y_start = (band_h - total_h) // 2

    stroke_w = max(3, font_size // 10)
    for i, ln in enumerate(lines):
        bbox = draw.textbbox((0, 0), ln, font=font, stroke_width=stroke_w)
        text_w = bbox[2] - bbox[0]
        x = (video_w - text_w) // 2 - bbox[0]
        y = y_start + i * line_h - bbox[1]
        draw.text(
            (x, y), ln, font=font,
            fill=(255, 255, 255, 255),
            stroke_width=stroke_w,
            stroke_fill=(0, 0, 0, 255),
        )

    img.save(out_path)


def _build_subtitle_timeline(script: dict, audio_dir: Path) -> list[tuple[str, float, float]]:
    """Returns list of (text, start_sec, end_sec) keyed to audio segment durations."""
    entries: list[tuple[str, Path]] = []
    if script.get("hook"):
        entries.append((script["hook"], audio_dir / "00_hook.mp3"))
    for scene in script["scenes"]:
        entries.append((scene["narration"], audio_dir / f"{scene['scene_id']:02d}_scene.mp3"))
    if script.get("cta"):
        entries.append((script["cta"], audio_dir / "99_cta.mp3"))

    timeline: list[tuple[str, float, float]] = []
    cursor = 0.0
    for text, path in entries:
        dur = _ffprobe_duration(path)
        timeline.append((text, cursor, cursor + dur))
        cursor += dur
    return timeline


def _find_bgm() -> Path | None:
    if not BGM_DIR.exists():
        return None
    for ext in ("*.mp3", "*.m4a", "*.wav"):
        candidates = sorted(BGM_DIR.glob(ext))
        if candidates:
            return candidates[0]
    return None


def _mux_with_subtitles(
    video: Path,
    audio: Path,
    subtitle_pngs: list[tuple[Path, float, float]],
    output: Path,
    bgm: Path | None = None,
) -> None:
    inputs: list[str] = ["-i", str(video)]
    for png, _, _ in subtitle_pngs:
        inputs += ["-i", str(png)]
    inputs += ["-i", str(audio)]
    if bgm is not None:
        inputs += ["-stream_loop", "-1", "-i", str(bgm)]

    filter_parts: list[str] = []
    last_label = "0:v"
    for i, (_, start, end) in enumerate(subtitle_pngs, start=1):
        out_label = f"v{i}"
        filter_parts.append(
            f"[{last_label}][{i}:v]overlay=x=0:y=0:"
            f"enable='between(t,{start:.3f},{end:.3f})'[{out_label}]"
        )
        last_label = out_label

    audio_index = len(subtitle_pngs) + 1
    if bgm is not None:
        narration_dur = _ffprobe_duration(audio)
        fade_out_start = max(0.0, narration_dur - 1.5)
        bgm_index = audio_index + 1
        filter_parts.append(
            f"[{bgm_index}:a]volume={BGM_VOLUME},"
            f"afade=t=in:st=0:d=1.0,"
            f"afade=t=out:st={fade_out_start:.3f}:d=1.5[bgm]"
        )
        filter_parts.append(
            f"[{audio_index}:a][bgm]amix=inputs=2:duration=first:dropout_transition=0[aout]"
        )
        audio_map = "[aout]"
    else:
        audio_map = f"{audio_index}:a:0"

    filter_complex = ";".join(filter_parts)

    _run([
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", f"[{last_label}]",
        "-map", audio_map,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(output),
    ])


def _mux_plain(video: Path, audio: Path, output: Path) -> None:
    _run([
        "ffmpeg", "-y",
        "-i", str(video),
        "-i", str(audio),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(output),
    ])


def _sync_clips_to_audio(
    video_paths: list[Path], script: dict, audio_dir: Path, work_dir: Path
) -> list[Path]:
    """Trim/pad each scene video to match its scene's audio duration."""
    work_dir.mkdir(exist_ok=True)
    synced: list[Path] = []
    for scene, src in zip(script["scenes"], video_paths):
        scene_audio = audio_dir / f"{scene['scene_id']:02d}_scene.mp3"
        if not scene_audio.exists():
            synced.append(src)
            continue
        target = _ffprobe_duration(scene_audio)
        dst = work_dir / f"sync_{scene['scene_id']:02d}.mp4"
        _trim_or_pad_clip(src, target, dst)
        synced.append(dst)
    return synced


def edit_final(video_paths: list[Path], audio_path: Path, script: dict, output_dir: Path) -> Path:
    audio_dir = audio_path.parent / "audio"
    if not audio_dir.exists():
        audio_dir = output_dir / "audio"

    sync_dir = output_dir / "_synced_clips"
    try:
        clips = _sync_clips_to_audio(video_paths, script, audio_dir, sync_dir)
    except (FileNotFoundError, subprocess.CalledProcessError):
        clips = video_paths

    merged_video = output_dir / "_merged_video.mp4"
    _concat_videos(clips, merged_video)

    final_path = output_dir / "final_reel.mp4"
    try:
        timeline = _build_subtitle_timeline(script, audio_dir)
    except (FileNotFoundError, subprocess.CalledProcessError):
        timeline = []

    if not timeline:
        _mux_plain(merged_video, audio_path, final_path)
        merged_video.unlink(missing_ok=True)
        return final_path

    video_w, video_h = _ffprobe_size(merged_video)
    subs_dir = output_dir / "subtitles"
    subs_dir.mkdir(exist_ok=True)

    subtitle_pngs: list[tuple[Path, float, float]] = []
    for idx, (text, start, end) in enumerate(timeline, start=1):
        png = subs_dir / f"sub_{idx:02d}.png"
        _render_subtitle_png(text, video_w, video_h, png)
        subtitle_pngs.append((png, start, end))

    bgm = _find_bgm()
    if bgm:
        print(f"      [bgm] using {bgm.name} at volume={BGM_VOLUME}")
    _mux_with_subtitles(merged_video, audio_path, subtitle_pngs, final_path, bgm=bgm)
    merged_video.unlink(missing_ok=True)
    if sync_dir.exists():
        for f in sync_dir.glob("*.mp4"):
            f.unlink(missing_ok=True)
        sync_dir.rmdir()
    return final_path
