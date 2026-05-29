"""
노션 API 공통 모듈.

직접 실행: 연결 + DB 접근 확인.
다른 스크립트:
    from execution.notion_client import get_notion, get_database_schema
"""
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

try:
    from notion_client import Client
except ImportError:
    print("❌ notion-client 설치 필요: pip install notion-client")
    sys.exit(1)


def get_notion() -> Client:
    token = os.getenv("NOTION_TOKEN", "").strip()
    if not token or token.startswith("secret_여기에"):
        print("❌ NOTION_TOKEN 이 .env에 없음")
        print("   1) https://www.notion.so/my-integrations 에서 Integration 만들기")
        print("   2) 'Internal Integration Token' 복사")
        print("   3) .env 에 NOTION_TOKEN=secret_... 추가")
        sys.exit(1)
    return Client(auth=token)


def get_database_id() -> str:
    db_id = os.getenv("NOTION_DATABASE_ID", "").strip()
    if not db_id or db_id.startswith("노션_DB_ID"):
        print("❌ NOTION_DATABASE_ID 가 .env에 없음")
        print("   노션 DB 페이지 URL의 마지막 32자가 ID (하이픈 무시 가능)")
        sys.exit(1)
    return db_id


def main():
    print("🔌 노션 연결 테스트...")
    notion = get_notion()
    db_id = get_database_id()
    try:
        db = notion.databases.retrieve(db_id)
        title = "".join(t.get("plain_text", "") for t in db.get("title", []))
        print(f"   ✅ DB 연결 성공: '{title}'")
        print()
        print("   현재 스키마(컬럼):")
        for name, prop in db.get("properties", {}).items():
            print(f"     - {name} ({prop.get('type')})")
    except Exception as e:
        print(f"   ❌ DB 접근 실패: {e}")
        print("   해결: DB 페이지에서 ... → Connections → Integration 추가")
        sys.exit(1)


if __name__ == "__main__":
    main()
