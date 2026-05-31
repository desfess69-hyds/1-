"""
인스타 카드뉴스 카피 생성기 (scriptwriter + media-producer 실행 도구).

directive: directives/create_card_news.md  (톤 마스터: directives/media_brand_tone.md)
결과물: {폴더}/cardnews.md + slide_1.txt ~ slide_N.txt + caption.txt
        (slide_*.txt 는 execution/make_card_image.py 로 PNG 합성용 입력)

사용 예:
    # mock (비용 0)
    python execution/generate_cardnews.py --topic "기도가 어려울 때" --slides 6 --mock

    # 실제 (Claude 1회 호출) — 릴스와 세트면 같은 폴더 cardnews/ 서브폴더로
    python execution/generate_cardnews.py --topic "..." --slides 6 \
        --output ".tmp/media_drafts/{슬러그}/cardnews"
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from execution.media_common import MOCK_BANNER, write_files, split_sections

SYSTEM = (
    "너는 HYDS 미디어 본부의 scriptwriter 겸 media-producer다. "
    "directives/create_card_news.md(구조)와 directives/media_brand_tone.md(톤·금기)를 지킨다. "
    "따뜻하고 차분, 과장·어그로 금지, 정치·이단·교파 비교 금지. 성경 인용은 출처 작게. "
    "1장=후크, 2~N-1장=본문(1장당 1~2문장), N장=CTA. 모든 출력 한국어. "
    "**사실 창작 금지(Hard Rule)**: 브리프에 없는 사실(가격·일정·장소·인명·프로그램·요일·URL)을 절대 지어내지 마라. "
    "모르는 항목은 '미정'으로 쓰고, cardnews.md 맨 위에 '⚠️ 미정 항목 N개: ...'를 표기한다. "
    "제공된 날짜·요일은 그대로 쓰고 임의로 바꾸지 마라."
)


def _mock_files(topic: str, slides: int, tone: str) -> dict[str, str]:
    files = {
        "cardnews.md": MOCK_BANNER + f"""# 카드뉴스 {slides}장 — {topic} ({tone})
[더미] 1장 후크 / 2~{slides-1}장 본문 / {slides}장 CTA
""",
        "caption.txt": f"[MOCK 캡션] {topic}\n저장하고 친구 태그!\n\n#더미 #검증용 #hyds #카드뉴스",
    }
    for i in range(1, slides + 1):
        role = "후크" if i == 1 else ("CTA" if i == slides else f"본문{i-1}")
        files[f"slide_{i}.txt"] = f"[더미 slide {i} / {role}] {topic}"
    return files


def build_cardnews_files(topic: str, slides: int, tone: str, mock: bool, context: str = "") -> dict[str, str]:
    """{파일명: 내용} 반환. mock이면 더미, 아니면 Claude 1회 호출(마커 분할)."""
    if mock:
        return _mock_files(topic, slides, tone)

    from execution.claude_client import ask_claude
    slide_files = [f"slide_{i}.txt" for i in range(1, slides + 1)]
    all_files = ["cardnews.md", *slide_files, "caption.txt"]
    marker_order = "\n".join(f"===FILE:{fn}===" for fn in all_files)
    ctx = f"\n\n[일관성 참고 — 같은 캠페인 릴스의 컨셉/메시지]\n{context}" if context else ""
    prompt = (
        f"주제: {topic}\n카드 수: {slides}장\n톤/컨셉: {tone}{ctx}\n\n"
        f"directives/create_card_news.md를 따라 인스타 카드뉴스 {slides}장을 만들어줘. "
        "각 파일은 반드시 '===FILE:파일명===' 마커 줄로 시작. 마커 외 설명·코드펜스 금지.\n"
        "- cardnews.md: 장별 카피 + 디자인 메모(색·폰트·배치)\n"
        f"- slide_1.txt ~ slide_{slides}.txt: 각 카드에 들어갈 텍스트만(이미지 합성용, 짧게)\n"
        "- caption.txt: 인스타 피드 캡션 + 해시태그 30개\n"
        f"1장=후크, 2~{slides-1}장=본문, {slides}장=CTA(신청/저장 유도).\n\n"
        f"출력 순서(이 마커 그대로):\n{marker_order}"
    )
    raw = ask_claude(prompt, system=SYSTEM, max_tokens=6000)
    data = split_sections(raw, all_files)
    if not data:
        return {"cardnews.md": f"# 파싱 실패 — Claude 원문\n\n{raw}"}
    return data


def main():
    p = argparse.ArgumentParser(description="인스타 카드뉴스 카피 생성")
    p.add_argument("--topic", required=True, help="주제")
    p.add_argument("--slides", type=int, default=6, help="카드 수(5~10)")
    p.add_argument("--tone", default="따뜻하고 차분", help="톤/컨셉")
    p.add_argument("--context", default="", help="릴스 등 같은 캠페인 일관성 참고 텍스트")
    p.add_argument("--mock", action="store_true", help="Claude 호출 없이 더미 출력 (비용 0)")
    p.add_argument("--output", required=True, help="결과 폴더 (예: .tmp/media_drafts/{슬러그}/cardnews)")
    args = p.parse_args()

    slides = max(5, min(10, args.slides))
    base = Path(args.output)
    base.mkdir(parents=True, exist_ok=True)

    mode = "MOCK" if args.mock else "실제(Claude 호출)"
    print(f"🖼  카드뉴스 [{mode}] — {args.topic} ({slides}장, {args.tone})")

    try:
        files = build_cardnews_files(args.topic, slides, args.tone, args.mock, args.context)
    except Exception as e:
        print(f"❌ 카드뉴스 생성 실패: {e}")
        print("   - API 키/잔액/네트워크를 확인하세요. 형식만 보려면 --mock 으로 실행.")
        sys.exit(1)

    written = write_files(base, files)
    print(f"✅ 저장: {base}  ({len(written)}개 파일)")
    for w in written:
        print(f"   - {w.name}")
    if args.mock:
        print("ℹ️  MOCK 출력입니다. 실제 카피는 --mock 빼고 실행 (유료).")


if __name__ == "__main__":
    main()
