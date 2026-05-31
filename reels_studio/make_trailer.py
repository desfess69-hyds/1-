"""영화 예고편(트레일러) 빌더 — 기존 씬 클립을 짧게 잘라 긴박한 시퀀스로 재편집.

사용법:
    python make_trailer.py <output_dir>
    # 예: python make_trailer.py "output/백홍준_-_찢겨진_성경의_첫_순교자"
"""
import json
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

KOREAN_FONT = os.environ.get(
    "KOREAN_FONT",
    "/System/Library/Fonts/Supplemental/AppleMyungjo.ttf",  # 명조체 (시네마틱)
)
BGM_DIR = Path(__file__).parent / "bgm"
W, H = 1920, 1080
FPS = 30
BGM_VOLUME = float(os.environ.get("BGM_VOLUME", "0.50"))


def _run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed:\nCMD: {' '.join(cmd)}\nSTDERR:\n{r.stderr[:1000]}"
        )


def _ffprobe_dur(p: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(p)],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())


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


def _make_cut(src: Path, start: float, dur: float, dst: Path, speed: float = 1.0) -> None:
    """Trim + cinematic teal/orange grade + normalize to W×H @ FPS. speed<1=slow-mo, >1=fast."""
    speed_filter = ""
    real_dur = dur
    if speed != 1.0:
        speed_filter = f"setpts=PTS/{speed:.3f},"
        real_dur = dur / speed
    _run([
        "ffmpeg", "-y",
        "-ss", f"{start:.3f}",
        "-i", str(src),
        "-t", f"{real_dur:.3f}",
        "-vf",
        f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
        f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"{speed_filter}"
        f"eq=contrast=1.10:saturation=0.85:gamma=1.05:brightness=0.04,"
        f"colorbalance=rs=-0.06:gs=-0.03:bs=0.10:rm=0.04:gm=0:bm=-0.03:rh=0.06:gh=0:bh=-0.03,"
        f"vignette=PI/9,"
        f"fps={FPS},setsar=1,format=yuv420p",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-an",
        str(dst),
    ])


def _make_text(text: str, dur: float, dst: Path, scale: float = 0.072) -> None:
    """White serif Korean text on near-black, quick fade in/out. Auto-shrinks if too wide."""
    img = Image.new("RGB", (W, H), (4, 4, 6))
    draw = ImageDraw.Draw(img)
    start_size = max(40, int(W * scale))
    max_w = int(W * 0.88)
    font = _fit_font(draw, text.replace("\n", " "), KOREAN_FONT, start_size, max_w)
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=2)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = W // 2 - tw // 2 - bbox[0]
    y = H // 2 - th // 2 - bbox[1]
    draw.text(
        (x, y), text, font=font,
        fill=(248, 242, 225),
        stroke_width=2, stroke_fill=(0, 0, 0),
    )
    png = dst.with_suffix(".png")
    img.save(png)
    fade_d = min(0.15, dur / 4)
    _run([
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", str(FPS),
        "-i", str(png),
        "-t", f"{dur:.3f}",
        "-vf",
        f"fade=t=in:st=0:d={fade_d},"
        f"fade=t=out:st={max(0, dur-fade_d):.3f}:d={fade_d},format=yuv420p",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(dst),
    ])
    png.unlink(missing_ok=True)


def _make_black(dur: float, dst: Path) -> None:
    _run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=black:s={W}x{H}:r={FPS}:d={dur:.3f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(dst),
    ])


def _fit_font(draw, text, font_path, start_size, max_width):
    size = start_size
    while size > 24:
        font = ImageFont.truetype(font_path, size)
        bbox = draw.textbbox((0, 0), text, font=font)
        if bbox[2] - bbox[0] <= max_width:
            return font
        size -= 4
    return ImageFont.truetype(font_path, size)


def _make_title(title: str, subtitle: str, dur: float, dst: Path) -> None:
    img = Image.new("RGB", (W, H), (3, 3, 5))
    draw = ImageDraw.Draw(img)
    cx = W // 2
    max_w = int(W * 0.86)

    title_font = _fit_font(draw, title, KOREAN_FONT, int(W * 0.055), max_w)
    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    ty = int(H * 0.36)
    draw.text(
        (cx - tw // 2 - bbox[0], ty - bbox[1]),
        title, font=title_font, fill=(248, 240, 220),
    )

    line_y = ty + th + int(H * 0.04)
    draw.line(
        [(cx - int(W * 0.16), line_y), (cx + int(W * 0.16), line_y)],
        fill=(180, 150, 100), width=2,
    )

    if subtitle:
        sub_font = _fit_font(draw, subtitle, KOREAN_FONT, int(W * 0.024), max_w)
        sub_bbox = draw.textbbox((0, 0), subtitle, font=sub_font)
        sw, sh = sub_bbox[2] - sub_bbox[0], sub_bbox[3] - sub_bbox[1]
        sy = line_y + int(H * 0.035)
        draw.text(
            (cx - sw // 2 - sub_bbox[0], sy - sub_bbox[1]),
            subtitle, font=sub_font, fill=(185, 175, 155),
        )

    png = dst.with_suffix(".png")
    img.save(png)
    fade_in = 1.0
    fade_out = 1.2
    _run([
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", str(FPS),
        "-i", str(png),
        "-t", f"{dur:.3f}",
        "-vf",
        f"fade=t=in:st=0:d={fade_in},"
        f"fade=t=out:st={dur-fade_out:.3f}:d={fade_out},format=yuv420p",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(dst),
    ])
    png.unlink(missing_ok=True)


def _concat(clips: list[Path], dst: Path) -> None:
    concat_file = dst.parent / "_trailer_concat.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for c in clips:
            f.write(f"file '{c.absolute()}'\n")
    _run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-an",
        str(dst),
    ])
    concat_file.unlink(missing_ok=True)


def _add_bgm(video: Path, bgm: Path, dst: Path) -> None:
    dur = _ffprobe_dur(video)
    fade_out = max(0.0, dur - 2.5)
    _run([
        "ffmpeg", "-y",
        "-i", str(video),
        "-stream_loop", "-1", "-i", str(bgm),
        "-filter_complex",
        f"[1:a]volume={BGM_VOLUME},"
        f"afade=t=in:st=0:d=0.8,"
        f"afade=t=out:st={fade_out:.3f}:d=2.5[aout]",
        "-map", "0:v:0", "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(dst),
    ])


# ─────────────────────────────────────────────────────────────────────
# 스토리별 트레일러 비트 정의
# 각 항목: ("cut"|"text"|"black"|"title", args, label)
#   cut:   (scene_path, start_sec, dur_sec[, speed])
#   text:  (text, dur_sec, font_scale)
#   black: (dur_sec,)
#   title: (title, subtitle, dur_sec)
# ─────────────────────────────────────────────────────────────────────


def _beats_baekhongjun(scn, title, subtitle):
    """백홍준 — 찢겨진 성경의 첫 순교자."""
    return [
        # 콜드 오픈
        ("black", (1.0,), "00_open_blk"),
        ("cut",   (scn(5), 5.0, 4.5, 0.85), "01_cold_border"),
        ("black", (0.4,), "02_blk"),
        # 미스터리 던지기
        ("text",  ("1879년", 1.5, 0.055), "03_year"),
        ("cut",   (scn(2), 3.0, 2.5), "04_meeting"),
        ("cut",   (scn(3), 4.0, 2.5), "05_baptism"),
        ("text",  ("한 청년이", 1.2, 0.055), "06_t1"),
        ("text",  ("말씀을 만났다", 1.5, 0.055), "07_t2"),
        # 결단
        ("cut",   (scn(4), 4.0, 2.2), "08_bible"),
        ("cut",   (scn(5), 6.0, 2.0), "09_border_close"),
        ("text",  ("조선으로", 0.9, 0.055), "10_t3"),
        ("text",  ("돌아가야 한다", 1.1, 0.055), "11_t4"),
        ("black", (0.25,), "12_blkflash"),
        # 위기 + 결단
        ("cut",   (scn(8), 0.5, 1.8), "13_guards1"),
        ("cut",   (scn(8), 3.0, 1.5), "14_guards2"),
        ("cut",   (scn(6), 1.0, 1.8), "15_tear1"),
        ("cut",   (scn(6), 5.5, 1.4), "16_tear2"),
        ("text",  ("그는 성경을 찢었다", 1.6, 0.046), "17_t5"),
        # 가속
        ("cut",   (scn(7), 1.0, 1.4), "18_rope1"),
        ("cut",   (scn(7), 3.5, 1.2), "19_rope2"),
        ("cut",   (scn(7), 6.0, 1.4), "20_rope3"),
        ("cut",   (scn(8), 6.0, 1.5), "21_guards_pass"),
        ("cut",   (scn(9), 1.5, 1.5), "22_restore1"),
        ("cut",   (scn(9), 5.0, 1.5), "23_restore2"),
        # 침묵 + 부활
        ("black", (0.5,), "24_silence"),
        ("text",  ("성경이 다시 살아났다", 2.0, 0.045), "25_t6"),
        # 결말
        ("cut",   (scn(10), 2.0, 4.0, 0.85), "26_martyr"),
        ("text",  ("그리고 그는", 1.2, 0.055), "27_t7"),
        ("text",  ("이 땅의 첫 순교자가 되었다", 2.5, 0.040), "28_t8"),
        # 타이틀 리빌
        ("black", (0.8,), "29_blk_pre_title"),
        ("title", (title, subtitle, 6.0), "30_title"),
        ("black", (0.6,), "31_endblk"),
    ]


def _beats_seosangryun(scn, title, subtitle):
    """서상륜 — 위대한 밀수꾼, 한국 교회의 가슴 벅찬 출발점."""
    return [
        # 콜드 오픈: 짧고 미스터리한 실루엣
        ("black", (0.5,), "00_open_blk"),
        ("cut",   (scn(1), 1.0, 2.5, 0.85), "01_cold_silhouette"),
        ("black", (0.3,), "02_blk"),
        # 미스터리: 1870년대 만주
        ("text",  ("1879년 만주", 1.5, 0.050), "03_year"),
        ("cut",   (scn(2), 3.0, 2.5), "04_merchant"),         # 홍삼 장수
        ("text",  ("죽음 앞에서", 1.3, 0.055), "06_t1"),
        # 구원과 회심 (선교사가 아픈 그를 돌보는 장면 = 아파하는 모습)
        ("cut",   (scn(4), 4.0, 2.3), "07_rescue"),           # 선교사 치료
        ("cut",   (scn(5), 5.0, 2.3), "08_conversion"),       # 회심
        ("text",  ("한 청년이", 1.2, 0.055), "09_t2"),
        ("text",  ("다시 살아났다", 1.5, 0.055), "10_t3"),
        # 결단: 한글 성경 → 조선으로
        ("cut",   (scn(6), 4.0, 2.2), "11_translate"),        # 한글성경 1882
        ("text",  ("이 말씀을 가지고", 1.2, 0.050), "12_t4"),
        ("text",  ("조선으로 돌아가야 한다", 1.5, 0.050), "13_t5"),
        ("black", (0.25,), "14_blkflash"),
        # 위기: 압록강 발각
        ("cut",   (scn(7), 1.0, 1.8), "15_border1"),          # 발각 순간
        ("cut",   (scn(7), 5.5, 1.5), "16_border2"),          # 성경 드러남
        ("text",  ("발각되었다", 1.4, 0.055), "17_t6"),
        # 감옥
        ("cut",   (scn(8), 2.0, 2.2), "18_prison"),           # 감옥 칼
        ("text",  ("절체절명의 위기", 1.5, 0.050), "19_t7"),
        # 기적의 탈출 (가속)
        ("cut",   (scn(9), 1.0, 1.5), "20_escape1"),          # 김효순 옥 풀기
        ("cut",   (scn(9), 4.0, 1.4), "21_escape2"),          # 도주
        ("cut",   (scn(9), 6.5, 1.3), "22_escape3"),          # 어둠 속
        ("text",  ("기적이 일어났다", 1.8, 0.050), "23_t8"),
        # 결말: 소래교회 (image-to-video, slow natural movement)
        ("black", (1.5,), "24_silence"),
        ("cut",   (scn(10), 0.5, 4.0, 0.90), "25_sorae"),     # 소래교회
        ("text",  ("그는 한국 최초의", 1.3, 0.050), "26_t9"),
        ("text",  ("교회를 세웠다", 1.8, 0.055), "27_t10"),
        # 타이틀 리빌
        ("black", (0.8,), "28_blk_pre_title"),
        ("title", (title, subtitle, 6.0), "29_title"),
        ("black", (0.6,), "30_endblk"),
    ]


def _select_beats(script, scn, title, subtitle):
    template = (script.get("trailer_template") or "").lower()
    if template == "seosangryun" or "서상륜" in title:
        return _beats_seosangryun(scn, title, subtitle)
    return _beats_baekhongjun(scn, title, subtitle)


def main():
    if len(sys.argv) < 2:
        print("Usage: python make_trailer.py <output_dir>")
        sys.exit(1)

    out_dir = Path(sys.argv[1]).resolve()
    if not out_dir.exists():
        print(f"❌ 디렉토리 없음: {out_dir}")
        sys.exit(1)

    script = json.loads((out_dir / "script.json").read_text(encoding="utf-8"))
    title = script.get("title", "제목")
    subtitle = script.get("subtitle", "")
    video_dir = out_dir / "videos"

    def scn(n: int) -> Path:
        return video_dir / f"scene_{n:02d}.mp4"

    work = out_dir / "_trailer_work"
    work.mkdir(exist_ok=True)

    print(f"=== 트레일러 빌드: '{title}' ===")
    print(f"출력: {out_dir}\n")

    # ─────────────────────────────────────────────────────────────────
    # Beat 정의: 각 항목은 ("cut"|"text"|"black"|"title", args, label)
    # cut:   (scene_path, start_sec, dur_sec)
    # text:  (text, dur_sec, scale)
    # black: (dur_sec,)
    # title: (title, subtitle, dur_sec)
    # ─────────────────────────────────────────────────────────────────
    beats = _select_beats(script, scn, title, subtitle)

    print(f"비트: {len(beats)}개\n")

    clips: list[Path] = []
    total = 0.0
    for i, (kind, args, label) in enumerate(beats, start=1):
        dst = work / f"{label}.mp4"
        if kind == "cut":
            if len(args) == 4:
                src, start, dur, speed = args
            else:
                src, start, dur = args
                speed = 1.0
            if not src.exists():
                raise FileNotFoundError(f"필요한 클립 없음: {src}")
            _make_cut(src, start, dur, dst, speed=speed)
        elif kind == "text":
            if len(args) == 3:
                text, dur, scale = args
            else:
                text, dur = args
                scale = 0.072
            _make_text(text, dur, dst, scale=scale)
        elif kind == "black":
            (dur,) = args
            _make_black(dur, dst)
        elif kind == "title":
            t, sub, dur = args
            _make_title(t, sub, dur, dst)
        else:
            raise ValueError(f"unknown beat kind: {kind}")

        clip_dur = _ffprobe_dur(dst)
        total += clip_dur
        print(f"  [{i:02d}] {label:20s} → {clip_dur:5.2f}s (running {total:.2f}s)")
        clips.append(dst)

    print(f"\n총 길이: {total:.2f}s")

    print("\n[합치는 중] 하드 컷 concat...")
    merged = work / "_merged.mp4"
    _concat(clips, merged)

    print("[BGM 믹스]")
    bgm = _find_bgm()
    final = out_dir / "trailer.mp4"
    if bgm:
        print(f"  BGM: {bgm.name} (volume={BGM_VOLUME})")
        _add_bgm(merged, bgm, final)
    else:
        merged.rename(final)

    # cleanup
    merged.unlink(missing_ok=True)
    for c in clips:
        c.unlink(missing_ok=True)
    work.rmdir()

    print(f"\n✅ 완료: {final}")


if __name__ == "__main__":
    main()
