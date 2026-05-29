"""
텔레그램 알림 공통 모듈.

직접 실행: 환경변수 확인 + 테스트 메시지 발송.
    python execution/telegram_notify.py
    python execution/telegram_notify.py --text "사용자 정의 메시지"

다른 스크립트에서 사용:
    from execution.telegram_notify import send_telegram
    send_telegram("🔴 위험 감지: ...")
"""
import argparse
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

try:
    import requests
except ImportError:
    print("❌ requests 패키지 없음. pip install requests")
    sys.exit(1)


def send_telegram(text: str, parse_mode: str = "HTML", chat_id: str | None = None) -> bool:
    """텔레그램 메시지 발송.

    Args:
        text: 메시지 내용 (HTML 태그 허용: <b>, <i>, <code>, <pre>)
        parse_mode: HTML 또는 MarkdownV2
        chat_id: 대상 chat ID. 비워두면 TELEGRAM_ADMIN_CHAT_ID 사용

    Returns:
        True: 성공, False: 실패
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    target = (chat_id or os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")).strip()

    if not token:
        print("❌ TELEGRAM_BOT_TOKEN 이 .env에 없음")
        return False
    if not target:
        print("❌ TELEGRAM_ADMIN_CHAT_ID 가 .env에 없음")
        return False

    # 텔레그램 메시지 길이 제한 4096자 — 안전하게 분할
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    all_ok = True
    for chunk in chunks:
        try:
            res = requests.post(
                url,
                json={"chat_id": target, "text": chunk, "parse_mode": parse_mode},
                timeout=10,
            )
            if res.status_code != 200:
                print(f"❌ 발송 실패 (HTTP {res.status_code}): {res.text[:200]}")
                all_ok = False
        except Exception as e:
            print(f"❌ 네트워크 오류: {e}")
            all_ok = False
    return all_ok


def main():
    parser = argparse.ArgumentParser(description="텔레그램 알림 테스트")
    parser.add_argument(
        "--text", default="<b>🤖 HYDS 텔레그램 테스트</b>\n알림 시스템 정상 작동 중!",
        help="발송할 메시지 (HTML 허용)",
    )
    args = parser.parse_args()

    print("📤 텔레그램 발송 시도...")
    if send_telegram(args.text):
        print("✅ 발송 성공! 텔레그램 확인하세요.")
    else:
        print()
        print("디버그:")
        print(f"  TELEGRAM_BOT_TOKEN: {'있음' if os.getenv('TELEGRAM_BOT_TOKEN') else '없음'}")
        print(f"  TELEGRAM_ADMIN_CHAT_ID: {'있음' if os.getenv('TELEGRAM_ADMIN_CHAT_ID') else '없음'}")
        sys.exit(1)


if __name__ == "__main__":
    main()
