"""
팀장 종합 체크리스트 → 텔레그램 발송.

1. directives/retreat_team_leader_checklist.md → 영구 자산
2. 매번 .docx 새로 생성 (.tmp/dossiers/) → 텔레그램 첨부
3. 본문 요약 텍스트도 같이 발송

사용 예:
    python execution/send_team_checklist.py             # docx 생성 + 텔레그램 발송
    python execution/send_team_checklist.py --skip-docx # 기존 docx 그대로 발송
    python execution/send_team_checklist.py --no-send   # docx만 만들고 텔레그램 안 보냄
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

import requests
from execution.telegram_notify import send_telegram

PROJECT_ROOT = Path(__file__).parent.parent
DOCX_PATH = PROJECT_ROOT / ".tmp" / "dossiers" / "HYDS_팀장_종합_체크리스트.docx"


def regenerate_docx():
    """make_team_checklist_docx.py 호출."""
    from execution.make_team_checklist_docx import main as build
    build()


def send_document(file_path: Path, caption: str = "") -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "").strip()
    if not token or not chat_id:
        print("❌ 텔레그램 환경변수 없음")
        return False

    url = f"https://api.telegram.org/bot{token}/sendDocument"
    with open(file_path, "rb") as f:
        files = {"document": (file_path.name, f,
                              "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        data = {"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"}
        try:
            res = requests.post(url, data=data, files=files, timeout=30)
            if res.status_code != 200:
                print(f"❌ sendDocument 실패: {res.status_code} {res.text[:300]}")
                return False
            return True
        except Exception as e:
            print(f"❌ 네트워크 오류: {e}")
            return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-docx", action="store_true", help="docx 재생성 건너뛰기")
    parser.add_argument("--no-send", action="store_true", help="텔레그램 발송 안 함")
    args = parser.parse_args()

    if not args.skip_docx:
        print("📝 Word 파일 생성 중...")
        regenerate_docx()

    if not DOCX_PATH.exists():
        print(f"❌ Word 파일 없음: {DOCX_PATH}")
        sys.exit(1)

    if args.no_send:
        print(f"✅ Word 파일만 생성 완료: {DOCX_PATH}")
        print(f"   → 본인이 직접 열어서 Word/Pages에서 'PDF로 내보내기' 가능")
        return

    summary = """<b>📋 HYDS 팀장 종합 체크리스트</b>

기존 양식 + 누락되기 쉬운 8개 영역 보강 (66개 신규 항목):

<b>A.</b> 팀장 5단계
<b>B.</b> 운영 (장소·캠프·세부)
<b>C.</b> 예배 (설교자·팀장·음향)
<b>D.</b> 프로그램
<b>E.</b> 🆕 안전·법·교통·참가자·예산·홍보·기록·사후
<b>F.</b> D-day별 핵심 (D-90 → D+14)

→ 첨부 Word 파일 열어서 확인.
→ PDF 필요하면: Word/Pages에서 '파일 → 내보내기 → PDF'."""

    print("📤 텔레그램 본문 발송...")
    ok1 = send_telegram(summary)
    print("   ✅" if ok1 else "   ❌")

    print("📤 Word 파일 첨부 발송...")
    ok2 = send_document(DOCX_PATH, caption="HYDS 팀장 종합 체크리스트")
    print("   ✅" if ok2 else "   ❌")

    if ok1 and ok2:
        print("\n🎉 텔레그램 확인하세요.")


if __name__ == "__main__":
    main()
