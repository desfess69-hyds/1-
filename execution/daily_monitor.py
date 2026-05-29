"""
HYDS 일일 모니터링 자동화.

1. 모든 활성 수련회 스캔 (DB)
2. Claude로 위험도 분석
3. 빨강 위험 발견 시 텔레그램 알림 + 보고서 저장
4. 로그 남기기 (data/monitor_log.json)

매일 cron/launchd로 자동 실행 권장.

사용 예:
    python execution/daily_monitor.py
    python execution/daily_monitor.py --force-notify   # 빨강 없어도 요약 발송
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from execution.db_client import list_active_retreats, get_retreat_full
from execution.check_app_retreats import analyze_all, format_retreat_context
from execution.telegram_notify import send_telegram
from execution.utils import read_json, write_json

PROJECT_ROOT = Path(__file__).parent.parent


def extract_red_count(report: str) -> int:
    """보고서에서 🔴 위험도 높음 건수 추정."""
    return report.count("🔴")


def build_telegram_summary(report: str, retreats_count: int) -> str:
    """텔레그램용 요약 메시지 (HTML)."""
    today = datetime.now().strftime("%Y-%m-%d")
    red = extract_red_count(report)

    # 보고서에서 "한눈에 요약" 표 부분만 추출
    table_section = ""
    if "## 한눈에 요약" in report:
        start = report.index("## 한눈에 요약")
        end_marker = next(
            (report.index(m) for m in ["## 🔴", "## 🟡", "## 🟢"] if m in report[start:]),
            len(report)
        )
        if isinstance(end_marker, int) and end_marker > start:
            table_section = report[start:end_marker].strip()

    # HTML로 안전하게 변환 (특수문자 escape)
    def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    msg = f"<b>📡 HYDS 일일 모니터링 ({today})</b>\n\n"
    msg += f"활성 수련회: <b>{retreats_count}건</b>\n"
    if red > 0:
        msg += f"🔴 위험 높음: <b>{red}건</b> — 즉시 확인 필요\n\n"
    else:
        msg += "✅ 모든 수련회 안정적 진행 중\n\n"

    if table_section:
        msg += "<pre>" + esc(table_section[:2500]) + "</pre>\n\n"

    msg += f"<i>전체 보고서는 HYDS .tmp/dossiers/ 폴더 확인</i>"
    return msg


def main():
    parser = argparse.ArgumentParser(description="HYDS 일일 모니터링")
    parser.add_argument(
        "--force-notify", action="store_true",
        help="빨강 없어도 요약 알림 발송"
    )
    parser.add_argument(
        "--no-notify", action="store_true",
        help="알림 안 보내고 보고서만 생성"
    )
    args = parser.parse_args()

    today = datetime.now().strftime("%Y-%m-%d")
    print(f"📡 HYDS 일일 모니터링 시작 — {today}")

    # 1) 데이터 수집
    summary = list_active_retreats()
    if not summary:
        print("   활성 수련회 없음 — 종료")
        return
    retreats = [get_retreat_full(r["id"]) for r in summary]
    print(f"   {len(retreats)}건 분석 중...")

    # 2) Claude 분석
    report = analyze_all(retreats)
    output_path = PROJECT_ROOT / ".tmp" / "dossiers" / f"app_monitor_{today}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"   ✅ 보고서: {output_path}")

    # 3) 위험도 판단
    red_count = extract_red_count(report)
    print(f"   🔴 위험 높음: {red_count}건")

    # 4) 알림
    should_notify = (not args.no_notify) and (red_count > 0 or args.force_notify)
    notified = False
    if should_notify:
        msg = build_telegram_summary(report, len(retreats))
        print("   📤 텔레그램 발송...")
        notified = send_telegram(msg)
        if notified:
            print("   ✅ 알림 발송 성공")
        else:
            print("   ⚠️  알림 발송 실패 (텔레그램 설정 확인)")
    else:
        print(f"   (알림 스킵 — 빨강 0건이거나 --no-notify)")

    # 5) 로그 기록
    log = read_json("data/monitor_log.json") or []
    if not isinstance(log, list):
        log = []
    log.append({
        "date": today,
        "ran_at": datetime.now().isoformat(),
        "retreats_total": len(retreats),
        "red_count": red_count,
        "notified": notified,
        "report_path": str(output_path.relative_to(PROJECT_ROOT)),
    })
    # 최근 90일치만 보관
    log = log[-90:]
    write_json("data/monitor_log.json", log)
    print(f"   📝 로그 기록 완료")


if __name__ == "__main__":
    main()
