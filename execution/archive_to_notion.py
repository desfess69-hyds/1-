"""
수련회 종료 시 노션 DB로 자동 정리.

대상: status='done' 이면서 아직 노션에 안 올라간 수련회.

실행:
    python execution/archive_to_notion.py            # 자동 스캔
    python execution/archive_to_notion.py --retreat-id 5   # 특정 1건
    python execution/archive_to_notion.py --dry-run  # 노션 안 쓰고 미리보기

상태: data/notion_archive_state.json — 이미 올린 retreat_id 목록
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))
from execution.db_client import get_connection
from execution.claude_client import ask_claude
from execution.notion_client import get_notion, get_database_id
from execution.utils import read_json, write_json

STATE_FILE = "data/notion_archive_state.json"


def fetch_completed_retreats() -> list[dict]:
    """status='done' & deletedAt is null 수련회 + 보고서/체크리스트 첨부."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT * FROM retreats
            WHERE deletedAt IS NULL AND status = 'done'
            ORDER BY endAt DESC
        """)
        retreats = cur.fetchall()

        for r in retreats:
            cur.execute("""
                SELECT phase, title, isChecked FROM retreat_checklist_items
                WHERE retreatId = %s ORDER BY phase, sortOrder
            """, (r["id"],))
            r["checklist"] = cur.fetchall()

            cur.execute("""
                SELECT currentStatus, teamStatus, venueStatus, worshipStatus,
                       programStatus, issues, content, createdAt
                FROM retreat_reports WHERE retreatId = %s ORDER BY createdAt
            """, (r["id"],))
            r["reports"] = cur.fetchall()

            cur.execute("""
                SELECT fileName, fileUrl, description, tag, itemType
                FROM retreat_files WHERE retreatId = %s
            """, (r["id"],))
            r["files"] = cur.fetchall()
        return retreats


def make_summary(retreat: dict) -> str:
    """Claude가 종합 후기 요약 생성."""
    chk = retreat.get("checklist") or []
    total = len(chk)
    checked = sum(1 for c in chk if c["isChecked"])
    progress = round(checked / total * 100) if total else 0

    report_lines = []
    for r in retreat.get("reports") or []:
        parts = []
        for label, key in [("현황", "currentStatus"), ("팀", "teamStatus"),
                           ("장소", "venueStatus"), ("예배", "worshipStatus"),
                           ("프로그램", "programStatus"), ("이슈", "issues")]:
            v = (r.get(key) or "").strip()
            if v:
                parts.append(f"{label}: {v}")
        if parts:
            report_lines.append("; ".join(parts))

    prompt = f"""다음은 종료된 수련회의 전 과정 데이터입니다.
HYDS 아카이브용으로 한국어 요약을 작성하세요.

수련회: {retreat.get('churchName')} ({retreat.get('theme') or '주제 없음'})
기간: {datetime.fromtimestamp(retreat['startAt']/1000).strftime('%Y-%m-%d') if retreat.get('startAt') else '?'} ~ {datetime.fromtimestamp(retreat['endAt']/1000).strftime('%Y-%m-%d') if retreat.get('endAt') else '?'}
장소: {retreat.get('location') or '?'}
예상 참가: {retreat.get('expectedParticipants') or '?'}명
최종 체크리스트 진척률: {progress}% ({checked}/{total})

보고서 이력:
{chr(10).join(f'- {l}' for l in report_lines[-10:]) or '(보고서 없음)'}

다음 4개 섹션을 한국어로, 각 50~100자 이내:
1. **잘된 점** —
2. **아쉬운 점** —
3. **다음에 적용할 교훈** —
4. **재섭외 가치** — (강사·장소 다시 쓸지 한 줄)
"""
    return ask_claude(prompt, max_tokens=800)


def to_iso_date(ts_ms: int | None) -> str | None:
    if not ts_ms:
        return None
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone(timedelta(hours=9))).date().isoformat()


def build_notion_props(retreat: dict, summary: str, progress: int) -> dict:
    """노션 DB 속성 만들기. 사용자가 DB에 같은 이름 컬럼 만들어둬야 함."""
    files_text = ""
    for f in (retreat.get("files") or [])[:10]:
        url = f.get("fileUrl") or ""
        files_text += f"- {f.get('fileName', '?')}: {url}\n"

    start = to_iso_date(retreat.get("startAt"))
    end = to_iso_date(retreat.get("endAt"))

    # 노션 속성. 컬럼 타입은 사용자가 만들 때 정함.
    return {
        "교회명": {"title": [{"text": {"content": retreat.get("churchName", "?")}}]},
        "주제": {"rich_text": [{"text": {"content": retreat.get("theme") or ""}}]},
        "기간": {"date": ({"start": start, "end": end} if start else None)},
        "장소": {"rich_text": [{"text": {"content": retreat.get("location") or ""}}]},
        "참가 인원": {"number": retreat.get("expectedParticipants")},
        "최종 진척률": {"number": progress},
        "팀장": {"rich_text": [{"text": {"content": retreat.get("teamLeader") or ""}}]},
        "원본 ID": {"number": retreat["id"]},
        "후기 요약": {"rich_text": [{"text": {"content": summary[:1900]}}]},
        "파일/링크": {"rich_text": [{"text": {"content": files_text[:1900]}}]},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--retreat-id", type=int, help="특정 1건만")
    parser.add_argument("--dry-run", action="store_true", help="노션 안 쓰고 미리보기")
    parser.add_argument("--force", action="store_true",
                        help="이미 올린 것도 다시 (중복 생성됨, 주의)")
    args = parser.parse_args()

    print("📚 HYDS 노션 아카이브 시작")
    state = read_json(STATE_FILE)
    archived_ids = set(state.get("archived_ids", []) if isinstance(state, dict) else [])

    retreats = fetch_completed_retreats()
    if args.retreat_id:
        retreats = [r for r in retreats if r["id"] == args.retreat_id]

    targets = [r for r in retreats if r["id"] not in archived_ids or args.force]
    print(f"   완료된 수련회 {len(retreats)}건 / 미아카이브 {len(targets)}건")

    if not targets:
        print("   (이번엔 새로 올릴 게 없음)")
        return

    if not args.dry_run:
        notion = get_notion()
        db_id = get_database_id()

    for r in targets:
        print(f"\n📌 수련회 #{r['id']}: {r.get('churchName')}")
        chk = r.get("checklist") or []
        total = len(chk)
        progress = round(sum(1 for c in chk if c["isChecked"]) / total * 100) if total else 0

        print(f"   Claude로 후기 요약 생성 중...")
        try:
            summary = make_summary(r)
        except Exception as e:
            summary = f"(요약 실패: {e})"

        props = build_notion_props(r, summary, progress)

        if args.dry_run:
            print(f"   [DRY-RUN] 노션에 올릴 내용 (제목={r.get('churchName')}):")
            print(f"   요약 첫 200자: {summary[:200]}")
            continue

        try:
            notion.pages.create(parent={"database_id": db_id}, properties=props)
            print(f"   ✅ 노션 페이지 생성")
            archived_ids.add(r["id"])
        except Exception as e:
            print(f"   ❌ 노션 저장 실패: {e}")
            print(f"   힌트: DB 컬럼명/타입이 코드와 일치하는지 확인 (NOTION_SETUP.md 참고)")

    if not args.dry_run:
        write_json(STATE_FILE, {
            "archived_ids": sorted(archived_ids),
            "last_run_at": datetime.now().isoformat(),
        })
        print("\n✅ 상태 저장 완료")


if __name__ == "__main__":
    main()
