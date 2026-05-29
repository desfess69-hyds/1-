"""
HYDS 주간 리뷰 — 매주 일요일 22:00 자동 실행 (launchd).

지난 한 주의 자동화 로그(일일 모니터링·주간 To-Do·실시간 체크·결정)를 모아
요약하고, 배운 점을 directives/learnings.md 에 한 줄 기록한다. (부장 7원칙 #7 학습)

[뼈대 상태]
- 기본 실행: 로그 집계 + 요약 출력 + learnings.md 한 줄 추가 (무료, 외부 호출 없음)
- --ai     : Claude로 심층 회고 1문단 생성 (유료, opt-in)  ← TODO 고도화
- --notify : 텔레그램으로 주간 요약 발송 (opt-in)          ← TODO 고도화

사용 예:
    python execution/weekly_review.py
    python execution/weekly_review.py --ai --notify
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))
from execution.utils import read_json, write_json  # noqa: E402

PROJECT_ROOT = Path(__file__).parent.parent
LEARNINGS = PROJECT_ROOT / "directives" / "learnings.md"


def _parse_ts(value: str):
    """ISO 문자열 → datetime (실패 시 None)."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def collect_week(now: datetime) -> dict:
    """지난 7일간의 자동화 활동을 집계."""
    since = now - timedelta(days=7)

    monitor_log = read_json("data/monitor_log.json") or []
    weekly_log = read_json("data/weekly_todos_log.json") or []
    decisions = read_json("data/decisions.json") or []
    realtime = read_json("data/realtime_state.json") or {}

    def in_window(entry):
        ts = _parse_ts(entry.get("ran_at") or entry.get("ts") or entry.get("at") or "")
        return ts is not None and ts >= since

    monitor_runs = [e for e in monitor_log if isinstance(e, dict) and in_window(e)]
    weekly_runs = [e for e in weekly_log if isinstance(e, dict) and in_window(e)]
    week_decisions = [d for d in decisions if isinstance(d, dict) and in_window(d)]

    return {
        "since": since,
        "now": now,
        "monitor_runs": monitor_runs,
        "weekly_runs": weekly_runs,
        "decisions": week_decisions,
        "total_decisions": len(decisions),
        "last_realtime_check": (realtime or {}).get("last_check_at"),
    }


def build_summary(data: dict) -> str:
    """집계 → 마크다운 주간 요약."""
    now = data["now"]
    monitor_runs = data["monitor_runs"]
    weekly_runs = data["weekly_runs"]
    decisions = data["decisions"]

    total_red = sum(int(r.get("red_count", 0)) for r in monitor_runs)
    max_red = max((int(r.get("red_count", 0)) for r in monitor_runs), default=0)

    lines = [
        f"# HYDS 주간 리뷰 ({now.strftime('%Y-%m-%d')})",
        f"_기간: {data['since'].strftime('%Y-%m-%d')} ~ {now.strftime('%Y-%m-%d')}_",
        "",
        "## 자동화 활동",
        f"- 일일 모니터링 실행: **{len(monitor_runs)}회** (🔴 위험 누적 {total_red}건, 최대 {max_red}건)",
        f"- 주간 To-Do 생성: **{len(weekly_runs)}회**",
        f"- 마지막 실시간 체크: {data['last_realtime_check'] or '기록 없음'}",
        f"- 이번 주 기록된 결정: **{len(decisions)}건** (누적 {data['total_decisions']}건)",
        "",
        "## 이번 주 결정 (data/decisions.json)",
    ]
    if decisions:
        for d in decisions:
            when = (d.get("ran_at") or d.get("ts") or "")[:10]
            lines.append(f"- [{when}] {d.get('summary') or d.get('decision') or d}")
    else:
        lines.append("- (기록된 결정 없음)")

    # TODO: --ai 시 Claude 심층 회고 1문단을 여기에 삽입
    lines += ["", "## 다음 주 제안", "- TODO: 임박한 D-day·미해결 이슈 기반 우선순위 (능동적 제안)"]
    return "\n".join(lines)


def append_learning(now: datetime, data: dict) -> None:
    """learnings.md 에 한 줄 추가 (없으면 헤더 만들고 추가)."""
    line = (
        f"- {now.strftime('%Y-%m-%d')} | [주간리뷰] "
        f"모니터링 {len(data['monitor_runs'])}회·주간To-Do {len(data['weekly_runs'])}회·"
        f"결정 {len(data['decisions'])}건 → 자동 집계 기록"
    )
    if not LEARNINGS.exists():
        LEARNINGS.parent.mkdir(parents=True, exist_ok=True)
        LEARNINGS.write_text("# HYDS 학습 로그 (Learnings)\n\n", encoding="utf-8")
    with LEARNINGS.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def main():
    parser = argparse.ArgumentParser(description="HYDS 주간 리뷰")
    parser.add_argument("--ai", action="store_true", help="Claude 심층 회고 (유료) — TODO")
    parser.add_argument("--notify", action="store_true", help="텔레그램 발송 — TODO")
    args = parser.parse_args()

    now = datetime.now()
    print(f"🗓  HYDS 주간 리뷰 — {now.strftime('%Y-%m-%d %H:%M')}")

    data = collect_week(now)
    summary = build_summary(data)

    out = PROJECT_ROOT / ".tmp" / "dossiers" / f"weekly_review_{now.strftime('%Y%m%d')}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(summary, encoding="utf-8")
    print(f"   ✅ 요약 저장: {out}")

    append_learning(now, data)
    print(f"   📝 learnings.md 한 줄 추가")

    if args.ai:
        # TODO: from execution.claude_client import ask_claude → 심층 회고 생성
        print("   ⚠️  --ai 는 아직 뼈대 (Claude 회고 미구현)")
    if args.notify:
        # TODO: from execution.telegram_notify import send_telegram → 요약 발송
        print("   ⚠️  --notify 는 아직 뼈대 (텔레그램 발송 미구현)")

    print("\n" + summary)


if __name__ == "__main__":
    main()
