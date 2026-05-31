"""
미디어 패키지 묶음 생성기 (media-director 본부 산출물 한 폴더로).

scout_trends + generate_reels_script 결과를 한 폴더에 모으고 concept.md를 더해
PLAN.md §4의 9종 결과물을 완성한 뒤, 텔레그램으로 요약 발송한다.

9종: trend_brief.md(선택) · concept.md · script.md · vrew_script.txt ·
     capcut_guide.md · caption.txt · bgm.md · thumbnail_brief.md · assets/

사용 예:
    # mock (Claude·텔레그램 호출 없음 — 폴더/9종 형식 검증)
    python execution/generate_media_package.py --topic "기도가 어려울 때" --with-trend --mock

    # 실제 (Claude 호출 + 텔레그램 발송)
    python execution/generate_media_package.py --topic "평택교회 수련회 홍보" \
        --with-trend --keywords "도착 챌린지" --length 30
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from execution.media_common import MOCK_BANNER, draft_dir, write_files, write_file
from execution.scout_trends import build_trend_brief
from execution.generate_reels_script import build_reels_files


def _mock_concept(topic: str, tone: str) -> str:
    return MOCK_BANNER + f"""# 컨셉 [더미] — {topic}
- 톤앤매너: {tone} (HYDS 차분·따뜻)
- 핵심 메시지 1개: "[더미] {topic}"
- 시리즈 위치: 더미 시리즈 #1
- 타깃: 기독 청년 20대
"""


def build_concept(topic: str, tone: str, mock: bool, trend_brief: str = "") -> str:
    if mock:
        return _mock_concept(topic, tone)
    from execution.claude_client import ask_claude
    ctx = f"\n\n[trend-scout 브리프]\n{trend_brief}" if trend_brief else ""
    prompt = (
        f"주제: {topic}\n톤/컨셉: {tone}{ctx}\n\n"
        "directives/media_brand_tone.md 톤을 지켜, 이 릴스의 concept.md를 작성해줘. "
        "톤앤매너·핵심 메시지 1개·시리즈 위치·타깃을 간결한 마크다운으로."
    )
    return ask_claude(prompt, system="너는 HYDS concept-planner다. 한국어, 과장 금지.", max_tokens=1200)


def main():
    p = argparse.ArgumentParser(description="미디어 패키지 9종 묶음 생성 + 텔레그램")
    p.add_argument("--topic", required=True, help="주제")
    p.add_argument("--length", type=int, default=30, help="릴스 길이(초)")
    p.add_argument("--tone", default="공감형", help="컨셉/톤")
    p.add_argument("--platform", default="인스타 릴스", help="플랫폼")
    p.add_argument("--keywords", default="", help="트렌드 키워드 (쉼표 구분, 선택)")
    p.add_argument("--with-trend", action="store_true", help="trend-scout 정찰 포함 (가장 먼저)")
    p.add_argument("--mock", action="store_true", help="Claude·텔레그램 호출 없이 더미 (비용 0)")
    p.add_argument("--no-telegram", action="store_true", help="텔레그램 발송 생략")
    p.add_argument("--output", help="결과 폴더 직접 지정 (선택)")
    args = p.parse_args()

    base = Path(args.output) if args.output else draft_dir(args.topic)
    (base / "assets").mkdir(parents=True, exist_ok=True)

    mode = "MOCK" if args.mock else "실제(Claude 호출)"
    print(f"📦 미디어 패키지 [{mode}] — {args.topic}")

    files: dict[str, str] = {}
    trend_brief = ""

    try:
        # 1) trend-scout 가장 먼저 (선택) → 브리프를 다운스트림에 전달
        if args.with_trend:
            keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
            print("   ① trend-scout 정찰...")
            tf = build_trend_brief(args.topic, keywords, args.platform, args.mock)
            files.update(tf)
            trend_brief = tf.get("trend_brief.md", "")

        # 2) concept-planner → 컨셉
        print("   ② concept-planner 컨셉...")
        files["concept.md"] = build_concept(args.topic, args.tone, args.mock, trend_brief)

        # 3) scriptwriter + media-producer → 6종 (트렌드 브리프 반영)
        print("   ③ scriptwriter+producer 대본·자료 6종...")
        files.update(build_reels_files(
            args.topic, args.length, args.tone, args.platform, args.mock, trend_brief,
        ))
    except Exception as e:
        print(f"❌ 패키지 생성 실패: {e}")
        print("   - API 키/잔액/네트워크를 확인하세요. 형식만 보려면 --mock 으로 실행.")
        sys.exit(1)

    # 4) assets/ 안내 파일 (빈 폴더가 커밋/표시되도록)
    write_file(base / "assets" / "README.txt",
               "여기에 CapCut/Vrew에 넣을 이미지·로고를 둡니다. (mock에서는 비어 있음)\n")

    written = write_files(base, files)
    total = len(written) + 1  # assets/README.txt 포함
    print(f"✅ 저장: {base}  (파일 {total}개 + assets/)")
    for w in written:
        print(f"   - {w.relative_to(base.parent)}")

    # 5) 텔레그램 요약 (mock·--no-telegram이면 생략)
    summary = (
        f"🎬 미디어 패키지 완성: {args.topic}\n"
        f"📂 {base.name}\n"
        f"파일: {', '.join(sorted(files.keys()))}\n"
        f"→ Vrew/CapCut에서 5분 편집 후 업로드"
    )
    if args.mock or args.no_telegram:
        print("ℹ️  텔레그램 발송 생략 (mock 또는 --no-telegram).")
        print("---- (발송될 요약 미리보기) ----")
        print(summary)
    else:
        try:
            from execution.telegram_notify import send_telegram
            ok = send_telegram(summary)
            print("📨 텔레그램 발송 " + ("성공" if ok else "실패(로컬엔 저장됨)"))
        except Exception as e:
            print(f"⚠️  텔레그램 발송 예외(로컬엔 저장됨): {e}")


if __name__ == "__main__":
    main()
