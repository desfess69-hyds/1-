"""
HYDS Ministry App MySQL DB 클라이언트.

DATABASE_URL 파싱해서 연결, 수련회/체크리스트/보고서 조회.

사용 예 (다른 스크립트에서):
    from execution.db_client import list_active_retreats, get_retreat_full
    rows = list_active_retreats()

직접 실행하면 연결 테스트 + 활성 수련회 목록 출력.
"""
import os
import sys
from pathlib import Path
from urllib.parse import urlparse, unquote
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

try:
    import pymysql
    from pymysql.cursors import DictCursor
except ImportError:
    print("❌ pymysql 이 설치되지 않았어요.")
    print("   다음 명령: pip install pymysql cryptography")
    sys.exit(1)


def get_connection():
    """DATABASE_URL 파싱 → pymysql 연결 객체 반환."""
    url = os.getenv("DATABASE_URL", "")
    if not url:
        print("❌ DATABASE_URL 이 .env에 설정되지 않았어요.")
        print("   Railway → Variables 탭에서 복사해서 .env에 추가하세요.")
        sys.exit(1)

    # mysql://user:pass@host:port/db?ssl=...
    parsed = urlparse(url)
    if parsed.scheme not in ("mysql", "mysql+pymysql"):
        print(f"❌ DATABASE_URL 형식이 mysql:// 가 아님: {parsed.scheme}")
        sys.exit(1)

    # ssl 옵션 — TiDB Cloud는 SSL 필수
    use_ssl = "ssl=" in url or "ssl-" in url
    kwargs = {
        "host": parsed.hostname,
        "port": parsed.port or 3306,
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "database": parsed.path.lstrip("/") if parsed.path else None,
        "charset": "utf8mb4",
        "cursorclass": DictCursor,
        "autocommit": True,
    }
    if use_ssl:
        kwargs["ssl"] = {"ssl_disabled": False}

    return pymysql.connect(**kwargs)


# ─── 데이터 조회 함수 ─────────────────────────────────────────

def list_active_retreats() -> list[dict]:
    """진행 중인 수련회(done/deleted 제외) 목록 + 진척률.

    Returns: [{id, churchName, theme, startAt, endAt, status,
               checklistTotal, checklistChecked, progress, daysUntil}]
    """
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT id, churchName, theme, teamLeader, startAt, endAt,
                   location, expectedParticipants, status, createdAt
            FROM retreats
            WHERE deletedAt IS NULL AND status != 'done'
            ORDER BY startAt ASC
        """)
        retreats = cur.fetchall()

        # 각 수련회별 체크리스트 진척률
        for r in retreats:
            cur.execute("""
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN isChecked THEN 1 ELSE 0 END) AS checked
                FROM retreat_checklist_items WHERE retreatId = %s
            """, (r["id"],))
            stats = cur.fetchone() or {"total": 0, "checked": 0}
            total = int(stats.get("total") or 0)
            checked = int(stats.get("checked") or 0)
            r["checklistTotal"] = total
            r["checklistChecked"] = checked
            r["progress"] = round(checked / total * 100) if total else 0

            # D-day 계산
            if r["startAt"]:
                start = datetime.fromtimestamp(r["startAt"] / 1000)
                delta = (start - datetime.now()).days
                r["daysUntil"] = delta
            else:
                r["daysUntil"] = None

        return retreats


def get_retreat_full(retreat_id: int) -> dict:
    """수련회 1건의 전체 정보 (기본 + 체크리스트 + 최근 보고서 3건)."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM retreats WHERE id = %s", (retreat_id,))
        retreat = cur.fetchone()
        if not retreat:
            return None

        cur.execute("""
            SELECT id, phase, title, isChecked, checkedAt, sortOrder
            FROM retreat_checklist_items
            WHERE retreatId = %s ORDER BY phase, sortOrder
        """, (retreat_id,))
        retreat["checklist"] = cur.fetchall()

        cur.execute("""
            SELECT id, currentStatus, teamStatus, venueStatus,
                   worshipStatus, programStatus, issues, content, createdAt
            FROM retreat_reports
            WHERE retreatId = %s ORDER BY createdAt DESC LIMIT 5
        """, (retreat_id,))
        retreat["recent_reports"] = cur.fetchall()

        return retreat


# ─── 직접 실행 시 연결 테스트 ─────────────────────────────────

def main():
    print("🔌 HYDS Ministry App DB 연결 테스트...")
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT VERSION() AS v")
            ver = cur.fetchone()
            print(f"   ✅ 연결 성공! MySQL: {ver['v']}")
        conn.close()
    except Exception as e:
        print(f"   ❌ 연결 실패: {e}")
        print("   - DATABASE_URL 형식 확인")
        print("   - Railway에서 SSL 옵션이 필요한지 확인")
        sys.exit(1)

    print()
    print("📋 진행 중인 수련회 목록 조회...")
    retreats = list_active_retreats()
    if not retreats:
        print("   (없음 — 아직 등록된 수련회 없음)")
        return

    print(f"   총 {len(retreats)}건")
    print()
    print(f"{'ID':<4} {'교회':<20} {'주제':<25} {'D-day':<8} {'진척률':<6} {'상태':<10}")
    print("─" * 80)
    for r in retreats:
        d = f"D-{r['daysUntil']}" if r['daysUntil'] is not None and r['daysUntil'] >= 0 \
            else f"D+{-r['daysUntil']}" if r['daysUntil'] is not None else "?"
        print(f"{r['id']:<4} {(r['churchName'] or '?')[:18]:<20} {(r['theme'] or '?')[:23]:<25} {d:<8} {r['progress']}%{'':<3} {r['status']:<10}")


if __name__ == "__main__":
    main()
