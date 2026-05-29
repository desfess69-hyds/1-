"""
HYDS 실시간 알림 (5분 폴링).

지난 실행 이후 새로 올라온 'retreat_reports'와 변경된 'retreat_checklist_items'을
스캔해서, 긴급한 것만 텔레그램으로 즉시 알림.

긴급도 판정 (결정론적 우선):
1. retreat_reports.issues 비어있지 않음 → 🔴 즉시
2. currentStatus 등에 위험 키워드 (취소/지연/문제/사고 등) → 🔴 즉시
3. D-day ≤ 7 인 수련회의 새 보고 → 🟡 주의

상태 보존: data/realtime_state.json
실행 주기: 5분 (launchd)

사용 예:
    python execution/realtime_check.py
    python execution/realtime_check.py --reset    # 상태 초기화 (모든 기존 데이터를 본 것으로 처리)
"""
import argparse
import sys
import re
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from execution.db_client import get_connection
from execution.claude_client import ask_claude
from execution.telegram_notify import send_telegram
from execution.utils import read_json, write_json

PROJECT_ROOT = Path(__file__).parent.parent
STATE_FILE = "data/realtime_state.json"

# 결정론적 위험 키워드 (한국어 + 영어)
RISK_KEYWORDS = [
    "취소", "연기", "지연", "사고", "문제", "위험", "긴급", "응급",
    "안 됨", "안됨", "못 함", "못함", "불가", "이슈", "오류", "에러",
    "cancel", "delay", "issue", "problem", "urgent", "emergency",
]


def has_risk_keyword(text: str | None) -> str | None:
    """텍스트에서 위험 키워드 발견 시 그 키워드 반환, 없으면 None."""
    if not text:
        return None
    lower = text.lower()
    for kw in RISK_KEYWORDS:
        if kw.lower() in lower:
            return kw
    return None


def is_urgent_report(report: dict, retreat: dict) -> tuple[bool, str]:
    """결정론적 긴급 여부 판정. (urgent, reason)"""
    # 1) issues 채워져 있으면 무조건 긴급
    issues = (report.get("issues") or "").strip()
    if issues:
        return True, f"이슈 보고됨: {issues[:80]}"

    # 2) 각 상태 필드에 위험 키워드
    for field in ["currentStatus", "teamStatus", "venueStatus",
                  "worshipStatus", "programStatus", "content"]:
        kw = has_risk_keyword(report.get(field))
        if kw:
            return True, f"'{field}'에 위험 키워드 감지: '{kw}'"

    # 3) D-day ≤ 7 인 수련회의 신규 보고는 노랑이지만 알림
    if retreat.get("startAt"):
        days_until = (datetime.fromtimestamp(retreat["startAt"] / 1000) - datetime.now()).days
        if 0 <= days_until <= 7:
            return True, f"D-{days_until} 수련회의 새 보고"

    return False, ""


def summarize_for_alert(retreat: dict, report: dict, reason: str) -> str:
    """Claude로 알림용 한 줄 요약 + 조치 권고."""
    fields = []
    for label, key in [
        ("현황", "currentStatus"), ("팀", "teamStatus"), ("장소", "venueStatus"),
        ("예배", "worshipStatus"), ("프로그램", "programStatus"),
        ("이슈", "issues"), ("메모", "content"),
    ]:
        val = (report.get(key) or "").strip()
        if val:
            fields.append(f"- {label}: {val}")
    body = "\n".join(fields) or "(빈 보고)"

    prompt = f"""아래는 HYDS Ministry App에 방금 올라온 팀장 보고입니다.

수련회: {retreat.get('churchName')} ({retreat.get('theme') or '주제 미정'})
팀장: {retreat.get('teamLeader') or '?'}
긴급 사유: {reason}

보고 내용:
{body}

다음 형식으로 한국어 답변하세요 (전체 200자 이내):
1. 한 줄 요약 (무엇이 문제인지)
2. 즉시 조치 1~2개 (누가 무엇을 해야 하는지)
"""
    return ask_claude(prompt, max_tokens=400)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true",
                        help="현재 시점까지를 '본 것'으로 처리 (첫 셋업 시 권장)")
    args = parser.parse_args()

    state = read_json(STATE_FILE)
    if not isinstance(state, dict):
        state = {}

    with get_connection() as conn, conn.cursor() as cur:
        # 첫 실행 또는 --reset → 현재 최대 ID를 기록하고 종료
        if args.reset or "last_report_id" not in state:
            cur.execute("SELECT COALESCE(MAX(id), 0) AS max_id FROM retreat_reports")
            max_id = cur.fetchone()["max_id"]
            state["last_report_id"] = int(max_id)
            state["last_check_at"] = datetime.now().isoformat()
            write_json(STATE_FILE, state)
            print(f"✅ 상태 초기화 — 마지막 report_id={max_id}. 다음 실행부터 새 보고만 추적.")
            return

        last_id = int(state.get("last_report_id", 0))
        print(f"📡 마지막 본 report_id={last_id} 이후 신규 보고 조회...")

        cur.execute("""
            SELECT * FROM retreat_reports
            WHERE id > %s ORDER BY id ASC
        """, (last_id,))
        new_reports = cur.fetchall()

        if not new_reports:
            print("   (신규 보고 없음)")
            state["last_check_at"] = datetime.now().isoformat()
            write_json(STATE_FILE, state)
            return

        print(f"   신규 {len(new_reports)}건 발견")

        urgent_alerts = []
        for rep in new_reports:
            cur.execute("SELECT * FROM retreats WHERE id = %s", (rep["retreatId"],))
            retreat = cur.fetchone()
            if not retreat:
                continue

            urgent, reason = is_urgent_report(rep, retreat)
            print(f"   - report#{rep['id']} ({retreat['churchName']}): {'🔴 긴급' if urgent else '⚪ 정상'} — {reason or '특이사항 없음'}")

            if urgent:
                # Claude 요약 (실패해도 알림은 보냄)
                try:
                    summary = summarize_for_alert(retreat, rep, reason)
                except Exception as e:
                    summary = f"(Claude 요약 실패: {e})"
                urgent_alerts.append({
                    "retreat": retreat,
                    "report": rep,
                    "reason": reason,
                    "summary": summary,
                })

        # 알림 발송 (한 메시지에 묶음)
        if urgent_alerts:
            def esc(s): return str(s or '').replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            parts = [f"<b>🚨 HYDS 긴급 알림 ({len(urgent_alerts)}건)</b>\n"]
            for a in urgent_alerts:
                r, rep, reason, summary = a["retreat"], a["report"], a["reason"], a["summary"]
                d_day = "?"
                if r.get("startAt"):
                    d_day = (datetime.fromtimestamp(r["startAt"]/1000) - datetime.now()).days
                    d_day = f"D-{d_day}" if d_day >= 0 else f"D+{-d_day}"

                parts.append(
                    f"\n<b>• {esc(r['churchName'])} ({d_day})</b>\n"
                    f"팀장: {esc(r.get('teamLeader') or '?')} | 사유: {esc(reason)}\n"
                    f"<pre>{esc(summary)}</pre>"
                )
            msg = "".join(parts)
            ok = send_telegram(msg)
            print(f"   {'✅' if ok else '❌'} 텔레그램 발송")
        else:
            print("   (긴급 없음 — 알림 스킵)")

        # 상태 갱신
        state["last_report_id"] = int(new_reports[-1]["id"])
        state["last_check_at"] = datetime.now().isoformat()
        state["last_run_alerts"] = len(urgent_alerts)
        write_json(STATE_FILE, state)


if __name__ == "__main__":
    main()
