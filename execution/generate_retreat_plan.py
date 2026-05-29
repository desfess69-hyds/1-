"""
수련회 기획안 초안 생성기.

사용 예:
    python execution/generate_retreat_plan.py \
        --church "○○교회" \
        --target "청년 30명" \
        --period "2026-08-15~17, 2박 3일" \
        --budget 2500000 \
        --message "회복"

→ .tmp/dossiers/{교회명}_{날짜}_기획안.md 파일로 저장됨
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# 같은 폴더의 claude_client.py 사용
sys.path.insert(0, str(Path(__file__).parent.parent))
from execution.claude_client import ask_claude


PROJECT_ROOT = Path(__file__).parent.parent


def load_json_safe(path: Path) -> list:
    """JSON 파일이 있으면 읽고, 없으면 빈 리스트."""
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def load_template() -> str:
    """기획안 양식 읽기."""
    template_path = PROJECT_ROOT / "templates" / "retreat_template.md"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return "(템플릿 파일 없음 — Claude가 자유 양식으로 작성)"


def build_prompt(args, speakers: list, venues: list, template: str) -> str:
    """Claude에게 보낼 프롬프트 구성."""
    speakers_summary = (
        json.dumps(speakers, ensure_ascii=False, indent=2)
        if speakers else "(아직 데이터 없음 — 외부 추천이 필요하면 명시)"
    )
    venues_summary = (
        json.dumps(venues, ensure_ascii=False, indent=2)
        if venues else "(아직 데이터 없음 — 외부 추천이 필요하면 명시)"
    )

    return f"""당신은 한국 교회의 수련회를 10년 기획해온 베테랑 기획자입니다.
HYDS의 수련회 기획 AI로서, 아래 의뢰에 맞춰 **기획안 초안**을 작성하세요.

## 의뢰 정보
- 교회/단체: {args.church}
- 대상: {args.target}
- 기간: {args.period}
- 예산: {args.budget:,}원
- 주요 메시지: {args.message or "(미지정 — 적절히 제안)"}
- 특별 요청: {args.note or "(없음)"}

## 참고: 보유 강사 풀
{speakers_summary}

## 참고: 보유 장소 풀
{venues_summary}

## 작성 양식 (이 양식 그대로 따르세요)
{template}

## 작성 규칙
- 모든 내용은 **한국어**로 작성
- 예산표는 합계가 의뢰 예산({args.budget:,}원) 이내가 되도록
- 강사/장소 후보는 반드시 **3개씩** 제시 (보유 풀에 없으면 외부 추천으로 제안하되 명시)
- 위험 요소 섹션을 솔직하게 작성 (예산 빠듯하면 솔직히 적기)
- 시간표는 **30분 단위**로 구체적으로
- 기독교 수련회임을 고려해 예배·말씀·교제 시간 균형 있게
"""


def main():
    parser = argparse.ArgumentParser(description="HYDS 수련회 기획안 생성기")
    parser.add_argument("--church", required=True, help="교회/단체명")
    parser.add_argument("--target", required=True, help="대상 (예: 청년 30명)")
    parser.add_argument("--period", required=True, help="기간 (예: 2026-08-15~17)")
    parser.add_argument("--budget", type=int, required=True, help="예산 (원, 정수)")
    parser.add_argument("--message", default="", help="주요 메시지/방향")
    parser.add_argument("--note", default="", help="특별 요청")
    parser.add_argument(
        "--output", default="",
        help="출력 파일 경로 (기본: .tmp/dossiers/{교회명}_{날짜}_기획안.md)"
    )
    args = parser.parse_args()

    # 출력 경로 결정
    if args.output:
        output_path = Path(args.output)
    else:
        today = datetime.now().strftime("%Y%m%d")
        safe_name = args.church.replace("/", "_").replace(" ", "_")
        output_path = PROJECT_ROOT / ".tmp" / "dossiers" / f"{safe_name}_{today}_기획안.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 자료 로드
    speakers = load_json_safe(PROJECT_ROOT / "data" / "speakers.json")
    venues = load_json_safe(PROJECT_ROOT / "data" / "venues.json")
    template = load_template()

    print(f"🤖 {args.church} 기획안 생성 중...")
    print(f"   예산: {args.budget:,}원 / 대상: {args.target} / 기간: {args.period}")

    prompt = build_prompt(args, speakers, venues, template)
    plan = ask_claude(
        prompt,
        system="너는 한국 기독교 수련회 기획 전문가다. 실용적이고 솔직하며, 추상적 표현 대신 구체적인 숫자와 이름을 쓴다.",
        max_tokens=8000,
    )

    output_path.write_text(plan, encoding="utf-8")
    print()
    print(f"✅ 기획안 저장됨: {output_path}")
    print(f"   → 검토 후 수정하고 클라이언트에게 전달하세요.")


if __name__ == "__main__":
    main()
