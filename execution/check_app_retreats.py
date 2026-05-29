"""
HYDS Ministry App 활성 수련회 자동 모니터링.

진행 중인 모든 수련회를 스캔해서 Claude로 위험도 분석 보고서 생성.

사용 예:
    python execution/check_app_retreats.py
    python execution/check_app_retreats.py --retreat-id 5   # 특정 1건만
    python execution/check_app_retreats.py --output report.md
"""
import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from execution.db_client import list_active_retreats, get_retreat_full
from execution.claude_client import ask_claude

PROJECT_ROOT = Path(__file__).parent.parent


def format_retreat_context(retreat: dict) -> str:
    """수련회 1건 → Claude 분석용 컨텍스트 문자열."""
    days_until = "?"
    if retreat.get("startAt"):
        start = datetime.fromtimestamp(retreat["startAt"] / 1000)
        days_until = (start - datetime.now()).days

    # 체크리스트 단계별 그룹핑
    checklist = retreat.get("checklist", [])
    by_phase = {}
    for item in checklist:
        by_phase.setdefault(item["phase"], []).append(item)

    checklist_summary = []
    for phase, items in by_phase.items():
        total = len(items)
        checked = sum(1 for i in items if i["isChecked"])
        checklist_summary.append(f"  - {phase}: {checked}/{total}")

    # 최근 보고서
    reports = retreat.get("recent_reports", [])
    report_lines = []
    for r in reports[:3]:
        ts = r["createdAt"].strftime("%Y-%m-%d") if r.get("createdAt") else "?"
        report_lines.append(f"  [{ts}] 현황: {(r.get('currentStatus') or '').strip()[:100]}")
        if r.get("issues"):
            report_lines.append(f"        이슈: {r['issues'].strip()[:100]}")

    return f"""## 수련회 #{retreat['id']} — {retreat.get('churchName', '?')}
- 주제: {retreat.get('theme') or '미정'}
- 팀장: {retreat.get('teamLeader') or '?'}
- D-day: D{'-' if days_until is not None and days_until >= 0 else '+'}{abs(days_until) if isinstance(days_until, int) else '?'}
- 상태: {retreat.get('status')}
- 예상 인원: {retreat.get('expectedParticipants') or '?'}명
- 장소: {retreat.get('location') or '미정'}

체크리스트 진척:
{chr(10).join(checklist_summary) if checklist_summary else '  (없음)'}

최근 보고서:
{chr(10).join(report_lines) if report_lines else '  (없음)'}
"""


def analyze_all(retreats: list[dict]) -> str:
    """모든 수련회를 Claude에게 한 번에 분석 요청."""
    contexts = "\n\n".join(format_retreat_context(r) for r in retreats)
    today = datetime.now().strftime("%Y-%m-%d")

    prompt = f"""너는 HYDS의 수련회 운영 매니저다.
아래는 현재 진행 중인 모든 수련회의 데이터다.
각 수련회를 점검하고 위험도 판정 + 즉시 조치 사항을 보고서로 정리하라.

## 위험 판정 기준
- **🔴 높음**: D-7 이내인데 진척률 < 70%, 또는 미해결 이슈 존재
- **🟡 중간**: D-30 이내인데 진척률 < 50%, 또는 최근 7일간 보고 없음
- **🟢 낮음**: 정상 페이스

## 출력 형식
```
# HYDS 수련회 모니터링 보고서 ({today})

## 한눈에 요약
| 수련회 | D-day | 진척률 | 위험도 | 즉시 조치 |
|--------|-------|--------|--------|-----------|
| ... |

## 🔴 즉시 대응 필요
(위험도 높음 수련회별 상세 — 무엇이 문제이고 누가 어떻게 해야 하는지)

## 🟡 주의 관찰
(위험도 중간)

## 🟢 정상 진행
(위험도 낮음 — 한 줄씩만)
```

## 데이터
{contexts}
"""
    return ask_claude(
        prompt,
        system="너는 한국 교회 수련회 운영 베테랑 매니저다. 실용적이고 솔직하며, 추상적 표현 대신 누가/언제/무엇을 명시한다.",
        max_tokens=6000,
    )


def main():
    parser = argparse.ArgumentParser(description="HYDS Ministry App 수련회 모니터링")
    parser.add_argument("--retreat-id", type=int, help="특정 수련회 1건만 분석")
    parser.add_argument("--output", default="", help="출력 파일 경로")
    args = parser.parse_args()

    print("📡 HYDS Ministry App DB에서 수련회 데이터 가져오는 중...")
    if args.retreat_id:
        r = get_retreat_full(args.retreat_id)
        if not r:
            print(f"❌ 수련회 #{args.retreat_id} 없음")
            sys.exit(1)
        retreats = [r]
    else:
        retreats_summary = list_active_retreats()
        if not retreats_summary:
            print("   (활성 수련회 없음)")
            sys.exit(0)
        retreats = [get_retreat_full(r["id"]) for r in retreats_summary]

    print(f"   {len(retreats)}건 분석 중...")
    report = analyze_all(retreats)

    # 출력 경로
    if args.output:
        output_path = Path(args.output)
    else:
        today = datetime.now().strftime("%Y-%m-%d")
        output_path = PROJECT_ROOT / ".tmp" / "dossiers" / f"app_monitor_{today}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print()
    print(f"✅ 보고서 저장: {output_path}")
    print()
    print("─" * 60)
    print(report[:2000])
    if len(report) > 2000:
        print(f"\n... (전체 보고서는 파일에서 확인: {output_path})")


if __name__ == "__main__":
    main()
