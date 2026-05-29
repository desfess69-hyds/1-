"""
인스타그램 업로드 (Phase 3에서 본격 구현).

현재는 placeholder — 카드뉴스 폴더의 PNG들을 수동 업로드하라고 안내.
"""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", required=True, help="카드뉴스 폴더 (.tmp/card_drafts/...)")
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.exists():
        print(f"❌ 폴더 없음: {folder}")
        return

    pngs = sorted(folder.glob("*.png"))
    caption_file = folder / "caption.txt"

    print("📦 인스타 업로드 안내 (Phase 3 API 연동 전까지 수동)")
    print(f"   폴더: {folder}")
    print(f"   슬라이드: {len(pngs)}장")
    if caption_file.exists():
        print(f"   캡션 파일: {caption_file}")
    print()
    print("👉 인스타 앱에서 캐러셀 게시물로 다음 순서대로 업로드하세요:")
    for p in pngs:
        print(f"   - {p.name}")


if __name__ == "__main__":
    main()
