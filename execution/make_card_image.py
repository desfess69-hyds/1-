"""
인스타 카드뉴스 이미지 생성기 (1080×1080).

Phase 2에서 본격 구현. 지금은 뼈대.

사용 예 (예정):
    python execution/make_card_image.py \
        --text "기도가 어려울 때\n읽어볼 시편" \
        --slide 1 \
        --output ".tmp/card_drafts/test/slide_01.png"
"""
import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("❌ Pillow 가 설치되지 않았어요. pip install Pillow")
    sys.exit(1)


PROJECT_ROOT = Path(__file__).parent.parent
CANVAS_SIZE = (1080, 1080)
SAFE_MARGIN = 80


def make_card(text: str, output_path: Path, bg_color=(245, 240, 230), text_color=(40, 40, 40)):
    """단일 카드 이미지 생성 (가장 단순 버전)."""
    img = Image.new("RGB", CANVAS_SIZE, bg_color)
    draw = ImageDraw.Draw(img)

    # TODO: templates/fonts/Pretendard-Bold.ttf 사용
    # 지금은 시스템 기본 폰트로 대체
    try:
        font_path = PROJECT_ROOT / "templates" / "fonts" / "Pretendard-Bold.ttf"
        if font_path.exists():
            font = ImageFont.truetype(str(font_path), 60)
        else:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    # 중앙 정렬 텍스트 (간단 버전 — 줄바꿈 처리는 Phase 2에서 개선)
    lines = text.split("\\n")
    line_height = 80
    total_height = len(lines) * line_height
    y = (CANVAS_SIZE[1] - total_height) // 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (CANVAS_SIZE[0] - text_width) // 2
        draw.text((x, y), line, font=font, fill=text_color)
        y += line_height

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", optimize=True)
    print(f"✅ 저장됨: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="HYDS 카드뉴스 이미지 생성기")
    parser.add_argument("--text", required=True, help="카드에 들어갈 텍스트 (\\n으로 줄바꿈)")
    parser.add_argument("--output", required=True, help="저장 경로 (.png)")
    args = parser.parse_args()

    make_card(args.text, Path(args.output))


if __name__ == "__main__":
    main()
