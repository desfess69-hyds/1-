"""
인스타 카드뉴스 이미지 생성기 (1080×1080).

directive: directives/create_card_news.md (디자인 규칙: 1080²·사방 80px 여백·한글 Pretendard)
generate_cardnews.py 가 만든 slide_N.txt 를 입력으로 PNG 합성.

사용 예:
    # 텍스트 직접 (\\n 또는 실제 줄바꿈)
    python execution/make_card_image.py --text "이번 여름,\\n우리 다시 만나" --output out.png

    # 파일에서 (slide_N.txt — 실제 줄바꿈 그대로)
    python execution/make_card_image.py --text-file cardnews/slide_1.txt --output slide_1.png

    # 파스텔 배경/글자색 지정 (기본: 연하늘 배경 + 네이비 글자)
    python execution/make_card_image.py --text-file s.txt --output s.png --bg EAF4FB --fg 1E3A5F
"""
import argparse
import re
import sys
from pathlib import Path

# 컬러 이모지 글리프 없는 한글 폰트에서 □(두부)로 깨지므로 카드 텍스트에서 제거.
# (slide_N.txt 원본은 그대로 두고, 렌더 직전에만 벗겨낸다.)
_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U00002B00-\U00002BFF"
    "\U0001F1E6-\U0001F1FF\U0000FE00-\U0000FE0F\U0000200D\U000023E9-\U000023FA]"
)


def strip_emoji(s: str) -> str:
    """이모지·변형 셀렉터 제거 후 남는 군더더기 공백 정리."""
    s = _EMOJI_RE.sub("", s)
    s = re.sub(r"[ \t]{2,}", " ", s)        # 이모지 빠진 자리 이중 공백 → 한 칸
    return "\n".join(line.strip() for line in s.split("\n"))

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("❌ Pillow 가 설치되지 않았어요. pip install Pillow")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.parent
CANVAS = 1080
SAFE_MARGIN = 80                       # 사방 안전 영역
MAX_TEXT_WIDTH = CANVAS - 2 * SAFE_MARGIN   # 920px

# 한글 렌더 가능한 폰트 후보 (위에서부터 시도). 번들 폰트 없으면 macOS 시스템 폰트로.
FONT_CANDIDATES = [
    PROJECT_ROOT / "templates" / "fonts" / "Pretendard-Bold.ttf",
    Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
    Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf"),
    Path("/Library/Fonts/NanumGothic.ttf"),
]


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """한글 가능한 첫 폰트를 size로 로드. 없으면 기본(한글 깨짐 경고)."""
    for fp in FONT_CANDIDATES:
        if fp.exists():
            try:
                return ImageFont.truetype(str(fp), size)
            except Exception:
                continue
    print("⚠️ 한글 폰트를 못 찾음 → 기본 폰트(한글 깨질 수 있음). templates/fonts/Pretendard-Bold.ttf 권장.")
    return ImageFont.load_default()


def _hex(c: str, fallback) -> tuple:
    """'EAF4FB' → (234,244,251). 실패 시 fallback."""
    try:
        c = c.lstrip("#")
        return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return fallback


def _wrap(draw, line: str, font, max_w: int) -> list[str]:
    """한 줄을 max_w 픽셀 안에 들어가도록 래핑. 공백 우선, 길면 글자 단위."""
    if draw.textlength(line, font=font) <= max_w:
        return [line]
    out, cur = [], ""
    # 공백이 있으면 단어 단위, 없으면(한글 등) 글자 단위로 쌓는다
    tokens = line.split(" ") if " " in line else list(line)
    sep = " " if " " in line else ""
    for tok in tokens:
        trial = (cur + sep + tok).strip() if cur else tok
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                out.append(cur)
            # 토큰 자체가 너무 길면 글자 단위로 쪼갬
            if draw.textlength(tok, font=font) > max_w:
                piece = ""
                for ch in tok:
                    if draw.textlength(piece + ch, font=font) <= max_w:
                        piece += ch
                    else:
                        out.append(piece)
                        piece = ch
                cur = piece
            else:
                cur = tok
    if cur:
        out.append(cur)
    return out


def make_card(text: str, output_path: Path, bg=(234, 244, 251), fg=(30, 58, 95), size: int = 64):
    """단일 카드 PNG. 실제 줄바꿈/래핑/여백/세로중앙 처리."""
    img = Image.new("RGB", (CANVAS, CANVAS), bg)
    draw = ImageDraw.Draw(img)
    font = _load_font(size)

    # 입력의 \n(리터럴) 과 실제 줄바꿈 모두 줄로 인식 → 이모지 제거 → 폭에 맞춰 래핑
    raw_lines = strip_emoji(text.replace("\\n", "\n")).split("\n")
    lines: list[str] = []
    for ln in raw_lines:
        ln = ln.rstrip()
        if ln == "":
            lines.append("")          # 빈 줄 = 문단 간격 유지
        else:
            lines.extend(_wrap(draw, ln, font, MAX_TEXT_WIDTH))

    line_h = int(size * 1.5)
    total_h = len(lines) * line_h
    y = max(SAFE_MARGIN, (CANVAS - total_h) // 2)

    for ln in lines:
        w = draw.textlength(ln, font=font)
        x = (CANVAS - w) // 2
        draw.text((x, y), ln, font=font, fill=fg)
        y += line_h

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", optimize=True)
    print(f"✅ {output_path.name} ({len(lines)}줄)")


def main():
    p = argparse.ArgumentParser(description="HYDS 카드뉴스 이미지 생성기 (1080×1080)")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--text", help="카드 텍스트 (\\n 또는 실제 줄바꿈)")
    src.add_argument("--text-file", help="텍스트 파일 경로 (slide_N.txt)")
    p.add_argument("--output", required=True, help="저장 경로 (.png)")
    p.add_argument("--bg", default="EAF4FB", help="배경색 hex (기본 연하늘)")
    p.add_argument("--fg", default="1E3A5F", help="글자색 hex (기본 네이비)")
    p.add_argument("--size", type=int, default=64, help="폰트 크기 (기본 64)")
    args = p.parse_args()

    text = Path(args.text_file).read_text(encoding="utf-8") if args.text_file else args.text
    make_card(text, Path(args.output),
              bg=_hex(args.bg, (234, 244, 251)),
              fg=_hex(args.fg, (30, 58, 95)),
              size=args.size)


if __name__ == "__main__":
    main()
