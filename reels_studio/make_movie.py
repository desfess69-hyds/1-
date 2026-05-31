"""영화 스타일 비주얼 영상 빌더 (TTS 없음, BGM + 타이틀 카드 + 크로스페이드).

사용법:
    python make_movie.py script.json [aspect_ratio]
    # aspect_ratio 기본값: 16:9
"""
import json
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

from step3_video_generator import generate_videos

KOREAN_SERIF = os.environ.get(
    "KOREAN_FONT",
    "/System/Library/Fonts/Supplemental/AppleMyungjo.ttf",  # 명조체 (시네마틱)
)
BGM_DIR = Path(__file__).parent / "bgm"
BGM_VOLUME = float(os.environ.get("BGM_VOLUME", "0.35"))

INTRO_SECONDS = 5.0
OUTRO_SECONDS = 6.0
CHAPTER_MARKER_SECONDS = 2.5
CROSSFADE_SECONDS = 0.6

W_169 = 1920
H_169 = 1080


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed:\nCMD: {' '.join(cmd)}\nSTDERR:\n{result.stderr}"
        )


def _ffprobe_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def _draw_centered(draw, text, font, x_center, y, fill, stroke=0, stroke_fill=(0, 0, 0)):
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
    w = bbox[2] - bbox[0]
    draw.text(
        (x_center - w // 2 - bbox[0], y - bbox[1]),
        text, font=font, fill=fill,
        stroke_width=stroke, stroke_fill=stroke_fill,
    )
    return bbox[3] - bbox[1]


def _make_intro_png(title: str, subtitle: str, out: Path, w: int, h: int) -> None:
    img = Image.new("RGB", (w, h), (8, 8, 10))
    draw = ImageDraw.Draw(img)
    title_font = ImageFont.truetype(KOREAN_SERIF, int(w * 0.06))
    sub_font = ImageFont.truetype(KOREAN_SERIF, int(w * 0.028))

    cx = w // 2
    _draw_centered(draw, title, title_font, cx, int(h * 0.40), (245, 235, 215))
    _draw_centered(draw, subtitle, sub_font, cx, int(h * 0.55), (180, 170, 150))

    line_y = int(h * 0.52)
    draw.line([(cx - int(w * 0.18), line_y), (cx + int(w * 0.18), line_y)],
              fill=(120, 105, 80), width=2)
    img.save(out)


def _make_chapter_png(chapter: str, title: str, out: Path, w: int, h: int) -> None:
    img = Image.new("RGB", (w, h), (6, 8, 12))
    draw = ImageDraw.Draw(img)
    ch_font = ImageFont.truetype(KOREAN_SERIF, int(w * 0.026))
    title_font = ImageFont.truetype(KOREAN_SERIF, int(w * 0.05))

    cx = w // 2
    _draw_centered(draw, chapter, ch_font, cx, int(h * 0.42), (210, 180, 130))
    line_y = int(h * 0.48)
    draw.line([(cx - int(w * 0.10), line_y), (cx + int(w * 0.10), line_y)],
              fill=(140, 110, 70), width=2)
    _draw_centered(draw, title, title_font, cx, int(h * 0.52), (245, 240, 230))
    img.save(out)


def _make_outro_png(lines: list[str], out: Path, w: int, h: int) -> None:
    img = Image.new("RGB", (w, h), (5, 5, 7))
    draw = ImageDraw.Draw(img)
    big = ImageFont.truetype(KOREAN_SERIF, int(w * 0.045))
    small = ImageFont.truetype(KOREAN_SERIF, int(w * 0.025))

    cx = w // 2
    y = int(h * 0.30)
    for i, line in enumerate(lines):
        font = big if i == 0 else small
        color = (245, 230, 200) if i == 0 else (170, 160, 140)
        _draw_centered(draw, line, font, cx, y, color)
        y += int(h * (0.08 if i == 0 else 0.05))
    img.save(out)


def _png_to_video(png: Path, duration: float, out: Path, fps: int = 30) -> None:
    fade_d = min(0.8, duration / 3)
    fade_out_start = max(0.0, duration - fade_d)
    _run([
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", str(fps),
        "-i", str(png),
        "-t", f"{duration:.3f}",
        "-vf", f"fade=t=in:st=0:d={fade_d},fade=t=out:st={fade_out_start:.3f}:d={fade_d},format=yuv420p",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(out),
    ])


def _normalize_clip(src: Path, out: Path, w: int, h: int, fps: int = 30) -> None:
    """Re-encode + scale + pad to target W×H, drop audio, uniform codec params."""
    _run([
        "ffmpeg", "-y", "-i", str(src),
        "-vf",
        f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"fps={fps},setsar=1,format=yuv420p",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-an",
        str(out),
    ])


def _add_chapter_overlay(clip: Path, chapter_png: Path, out: Path, w: int, h: int) -> None:
    """Overlay chapter title on top-left for first 3 seconds with fade in/out."""
    _run([
        "ffmpeg", "-y",
        "-i", str(clip),
        "-i", str(chapter_png),
        "-filter_complex",
        f"[1:v]format=yuva420p,fade=t=in:st=0:d=0.5:alpha=1,"
        f"fade=t=out:st=2.5:d=0.5:alpha=1[ov];"
        f"[0:v][ov]overlay=0:0:enable='between(t,0,3)'[v]",
        "-map", "[v]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-an",
        str(out),
    ])


def _make_chapter_overlay_png(chapter: str, title: str, out: Path, w: int, h: int) -> None:
    """Smaller overlay (top-left corner) on a transparent background."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    ch_font = ImageFont.truetype(KOREAN_SERIF, int(w * 0.020))
    title_font = ImageFont.truetype(KOREAN_SERIF, int(w * 0.034))

    pad_x = int(w * 0.045)
    pad_y = int(h * 0.06)
    box_w = int(w * 0.36)

    bg_color = (0, 0, 0, 170)
    box_h = int(h * 0.13)
    draw.rectangle(
        [(pad_x, pad_y), (pad_x + box_w, pad_y + box_h)],
        fill=bg_color,
    )
    accent_y = pad_y + int(h * 0.04)
    draw.line(
        [(pad_x + int(w * 0.012), accent_y), (pad_x + int(w * 0.055), accent_y)],
        fill=(210, 175, 120, 255), width=2,
    )
    draw.text((pad_x + int(w * 0.016), pad_y + int(h * 0.012)),
              chapter, font=ch_font, fill=(210, 180, 130, 255))
    draw.text((pad_x + int(w * 0.016), pad_y + int(h * 0.055)),
              title, font=title_font, fill=(245, 240, 230, 255))
    img.save(out)


def _concat_with_crossfade(clips: list[Path], out: Path, fade: float = CROSSFADE_SECONDS) -> None:
    if len(clips) == 1:
        _run(["ffmpeg", "-y", "-i", str(clips[0]), "-c", "copy", str(out)])
        return

    durations = [_ffprobe_duration(c) for c in clips]
    inputs: list[str] = []
    for c in clips:
        inputs += ["-i", str(c)]

    filter_parts = []
    last_label = "0:v"
    offset = 0.0
    for i in range(1, len(clips)):
        offset += durations[i - 1] - fade
        label = f"v{i}"
        filter_parts.append(
            f"[{last_label}][{i}:v]xfade=transition=fade:duration={fade:.3f}:"
            f"offset={offset:.3f}[{label}]"
        )
        last_label = label

    _run([
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", ";".join(filter_parts),
        "-map", f"[{last_label}]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-an",
        str(out),
    ])


def _add_bgm(video: Path, bgm: Path, out: Path) -> None:
    dur = _ffprobe_duration(video)
    fade_out_start = max(0.0, dur - 2.0)
    _run([
        "ffmpeg", "-y",
        "-i", str(video),
        "-stream_loop", "-1", "-i", str(bgm),
        "-filter_complex",
        f"[1:a]volume={BGM_VOLUME},"
        f"afade=t=in:st=0:d=1.5,"
        f"afade=t=out:st={fade_out_start:.3f}:d=2.0[aout]",
        "-map", "0:v:0", "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(out),
    ])


def _find_bgm() -> Path | None:
    if not BGM_DIR.exists():
        return None
    explicit = os.environ.get("BGM_FILE")
    if explicit:
        p = BGM_DIR / explicit
        if p.exists():
            return p
    for ext in ("*.mp3", "*.m4a", "*.wav"):
        files = sorted(BGM_DIR.glob(ext))
        if files:
            return files[0]
    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python make_movie.py <script.json> [aspect_ratio]")
        sys.exit(1)

    load_dotenv()

    script_path = Path(sys.argv[1]).resolve()
    aspect = sys.argv[2] if len(sys.argv) >= 3 else "16:9"
    script = json.loads(script_path.read_text(encoding="utf-8"))

    if aspect == "16:9":
        W, H = 1920, 1080
    elif aspect == "9:16":
        W, H = 1080, 1920
    elif aspect == "1:1":
        W, H = 1080, 1080
    else:
        W, H = 1920, 1080

    title = script.get("title", "제목 없음")
    subtitle = script.get("subtitle", "")
    safe_title = title.replace(" ", "_").replace("/", "_")
    output_dir = Path(__file__).parent / "output" / safe_title
    output_dir.mkdir(parents=True, exist_ok=True)

    saved = output_dir / "script.json"
    saved.write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"=== 영화 모드 빌드: '{title}' ({aspect}) ===")
    print(f"출력: {output_dir}")
    print(f"씬: {len(script['scenes'])}개\n")

    print("[1/4] Kling 영상 생성 (기존 클립은 재사용)...")
    raw_clips = generate_videos(script, aspect, output_dir)
    print()

    cards_dir = output_dir / "_cards"
    cards_dir.mkdir(exist_ok=True)
    clips_dir = output_dir / "_movie_clips"
    clips_dir.mkdir(exist_ok=True)

    print("[2/4] 타이틀 카드 + 챕터 오버레이 생성...")

    intro_png = cards_dir / "intro.png"
    _make_intro_png(title, subtitle, intro_png, W, H)
    intro_clip = clips_dir / "00_intro.mp4"
    _png_to_video(intro_png, INTRO_SECONDS, intro_clip)

    overlay_clips: list[Path] = []
    for i, (scene, raw) in enumerate(zip(script["scenes"], raw_clips), start=1):
        norm = clips_dir / f"{i:02d}_norm.mp4"
        _normalize_clip(raw, norm, W, H)

        ch = scene.get("chapter", "")
        t = scene.get("title", "")
        if ch or t:
            overlay_png = cards_dir / f"chap_{i:02d}.png"
            _make_chapter_overlay_png(ch, t, overlay_png, W, H)
            withov = clips_dir / f"{i:02d}_ov.mp4"
            _add_chapter_overlay(norm, overlay_png, withov, W, H)
            overlay_clips.append(withov)
        else:
            overlay_clips.append(norm)

    outro_lines = script.get("outro_lines") or [
        "그 위대한 밀수 사건은",
        "한국 교회의 가슴 벅찬 출발점이 되었습니다.",
        "",
        "당신은 지금, 무엇을 짊어지고 걸어가고 계십니까?",
    ]
    outro_png = cards_dir / "outro.png"
    _make_outro_png(outro_lines, outro_png, W, H)
    outro_clip = clips_dir / "99_outro.mp4"
    _png_to_video(outro_png, OUTRO_SECONDS, outro_clip)

    print("[3/4] 크로스페이드로 합치는 중...")
    all_clips = [intro_clip, *overlay_clips, outro_clip]
    merged = output_dir / "_movie_merged.mp4"
    _concat_with_crossfade(all_clips, merged)

    print("[4/4] BGM 믹스 + 최종 출력...")
    bgm = _find_bgm()
    final = output_dir / "movie.mp4"
    if bgm:
        print(f"      BGM: {bgm.name}")
        _add_bgm(merged, bgm, final)
    else:
        print("      (BGM 없음)")
        merged.rename(final)

    merged.unlink(missing_ok=True)
    for p in clips_dir.glob("*.mp4"):
        p.unlink(missing_ok=True)
    clips_dir.rmdir()

    print(f"\n✅ 완료: {final}")


if __name__ == "__main__":
    main()
