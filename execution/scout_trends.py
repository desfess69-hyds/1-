"""
트렌드 정찰 → trend_brief.md 생성기 (trend-scout 실행 도구).

directive: directives/scout_trends.md
결과물:   .tmp/media_drafts/{YYYYMMDD}_{slug}/trend_brief.md

사용 예:
    # mock (Claude 호출 없음, 비용 0 — 형식/폴더 검증용)
    python execution/scout_trends.py --topic "평택교회 수련회 홍보" --mock

    # 실제 (Claude 호출 — 유료)
    python execution/scout_trends.py --topic "평택교회 수련회 홍보" \
        --keywords "도착 챌린지,Y2K" --platform "인스타 릴스"

    # 주간 자동 (data/trend_keywords.json 기준 자율 검색)
    python execution/scout_trends.py --weekly --mock
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from execution.media_common import (
    MOCK_BANNER, draft_dir, write_files, extract_json, PROJECT_ROOT,
)

SYSTEM = (
    "너는 HYDS 미디어 본부의 trend-scout다. 인스타·틱톡·CapCut 트렌드를 발견해 "
    "기독교 청년 콘텐츠에 맞게 필터·번역한다. directives/scout_trends.md의 3중 필터"
    "(톤·금기 / 수명 라벨 / 적합도 점수)를 적용하고, CapCut 검색어는 정확한 문자열로 준다. "
    "모든 출력은 한국어. 과장·어그로·정치·이단·교파 비교 금지."
)


def _mock_brief(topic: str, keywords: list[str]) -> str:
    kw = ", ".join(keywords) if keywords else "(자율 선정)"
    return MOCK_BANNER + f"""# 이번 주 트렌드 5개 — 2026-XX-XX  ·  주제: {topic}
> 입력 키워드: {kw}

## 1. [더미] 도착 챌린지 🟢
- **원본 출처**: 인스타 @example (링크 더미)
- **CapCut 검색어**: "도착 챌린지" (arrival challenge)
- **수명 라벨**: 🟢 성숙 (등장 ~14일)
- **적합도 점수**: 8/10 — 청년3·톤3·적용2·시간0
- **우리 적용 방안**:
  - 어디에: {topic}
  - 어떻게: "도착해보니 ○○○" 포맷에 수련회 장소 사진 끼워넣기
  - 필요 자료: 장소 사진 3장, 텍스트 1줄
- **필요 자료 리스트**:
  - [ ] 장소 사진 (가로 3장)
  - [ ] 텍스트 카피 (15자 이내)
  - [ ] BGM (CapCut 라이브러리)
- **예상 소요**: CapCut 작업 4분

## 2. [더미] 잔잔한 전환 ⚪
- (형식 검증용 더미 항목)
- **적합도 점수**: 7/10

## 3~5. [더미] ...

## 종합 의견
- 추천 1순위: 1번(도착 챌린지)
- 식는 중 경고: 없음
- ⚠️ 이 파일은 MOCK입니다. 실제 트렌드 아님.
"""


def build_trend_brief(topic: str, keywords: list[str], platform: str, mock: bool) -> dict[str, str]:
    """{'trend_brief.md': 내용} 반환. mock이면 더미, 아니면 Claude 호출."""
    if mock:
        return {"trend_brief.md": _mock_brief(topic, keywords)}

    from execution.claude_client import ask_claude
    kw = ", ".join(keywords) if keywords else "(네가 자율적으로 5개 선정)"
    prompt = (
        f"주제: {topic}\n키워드: {kw}\n플랫폼: {platform}\n\n"
        "directives/scout_trends.md의 3중 필터를 적용해, 적합도 5점 이상 트렌드만 "
        "3~5개 골라 아래 마크다운 양식 그대로 trend_brief.md를 작성해줘. "
        "각 항목에 CapCut 검색어(정확한 문자열)·수명 라벨·적합도 점수·우리 적용 방안·예상 소요를 포함."
    )
    return {"trend_brief.md": ask_claude(prompt, system=SYSTEM, max_tokens=2500)}


def main():
    p = argparse.ArgumentParser(description="트렌드 정찰 → trend_brief.md")
    p.add_argument("--topic", help="주제 (예: 평택교회 수련회 홍보)")
    p.add_argument("--keywords", default="", help="쉼표 구분 키워드 (선택)")
    p.add_argument("--platform", default="인스타 릴스", help="적용 플랫폼")
    p.add_argument("--weekly", action="store_true", help="주간 자동 모드 (trend_keywords.json 기준)")
    p.add_argument("--mock", action="store_true", help="Claude 호출 없이 더미 출력 (비용 0)")
    p.add_argument("--output", help="결과 폴더 직접 지정 (선택)")
    args = p.parse_args()

    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]

    # 주간 모드: 관심 키워드 풀에서 자율 선정
    if args.weekly and not keywords:
        kw_file = PROJECT_ROOT / "data" / "trend_keywords.json"
        if kw_file.exists():
            import json
            try:
                keywords = json.loads(kw_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, ValueError):
                keywords = []

    topic = args.topic or ("주간 트렌드" if args.weekly else None)
    if not topic:
        print("❌ --topic 이 필요합니다 (또는 --weekly).")
        sys.exit(1)

    base = Path(args.output) if args.output else draft_dir(topic, "trends" if args.weekly else "")
    if args.output:
        (base / "assets").mkdir(parents=True, exist_ok=True)

    mode = "MOCK" if args.mock else "실제(Claude 호출)"
    print(f"🕵️  트렌드 정찰 [{mode}] — 주제: {topic} / 키워드: {keywords or '자율'}")

    files = build_trend_brief(topic, keywords, args.platform, args.mock)
    written = write_files(base, files)
    print(f"✅ 저장: {base}")
    for w in written:
        print(f"   - {w.relative_to(base.parent)}")
    if args.mock:
        print("ℹ️  MOCK 출력입니다. 실제 트렌드를 받으려면 --mock 빼고 실행 (유료).")


if __name__ == "__main__":
    main()
