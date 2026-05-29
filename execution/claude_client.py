"""
Claude API 공통 모듈.

이 파일은 다른 execution 스크립트들이 import해서 쓰는 헬퍼다.
직접 실행하면 "연결 테스트"를 수행한다.

사용 예:
    from execution.claude_client import ask_claude
    answer = ask_claude("수련회 한 줄 컨셉 추천해줘. 주제: 회복")
"""
import os
import sys
from pathlib import Path

# .env 자동 로드
try:
    from dotenv import load_dotenv
    # 프로젝트 루트의 .env 찾기
    project_root = Path(__file__).parent.parent
    load_dotenv(project_root / ".env")
except ImportError:
    pass  # python-dotenv 없어도 환경변수로 직접 설정 가능

try:
    from anthropic import Anthropic
except ImportError:
    print("❌ anthropic 패키지가 설치되지 않았어요.")
    print("   다음 명령을 실행하세요: pip install -r requirements.txt")
    sys.exit(1)


# 기본 모델 — 필요시 .env의 ANTHROPIC_MODEL로 덮어쓰기
DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")


def get_client() -> Anthropic:
    """Claude 클라이언트 생성. API 키 없으면 친절한 에러."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key.startswith("sk-ant-여기에"):
        print("❌ ANTHROPIC_API_KEY 가 설정되지 않았어요.")
        print("   1) .env.example을 .env로 복사")
        print("   2) https://console.anthropic.com 에서 키 발급")
        print("   3) .env 파일의 ANTHROPIC_API_KEY=sk-ant-... 채우기")
        sys.exit(1)
    return Anthropic(api_key=api_key)


def ask_claude(
    prompt: str,
    system: str = "",
    model: str = DEFAULT_MODEL,
    max_tokens: int = 4096,
) -> str:
    """Claude에게 한 번 물어보고 텍스트만 받는다.

    Args:
        prompt: 사용자 메시지 (한국어 OK)
        system: 시스템 프롬프트 (역할 지정용, 선택)
        model: 모델명 (기본: claude-sonnet-4-5)
        max_tokens: 최대 응답 토큰 수

    Returns:
        Claude의 응답 텍스트
    """
    client = get_client()
    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system

    response = client.messages.create(**kwargs)
    # 텍스트 블록만 모아 합치기
    return "".join(
        block.text for block in response.content if block.type == "text"
    )


def main():
    """직접 실행 시 연결 테스트."""
    print("🤖 HYDS Claude 연결 테스트")
    print(f"   모델: {DEFAULT_MODEL}")
    print()
    print("Claude에게 '안녕'이라고 물어보는 중...")
    try:
        answer = ask_claude(
            "한국어로 '안녕! HYDS 시스템이 정상 작동합니다'라고만 짧게 답해줘.",
            max_tokens=100,
        )
        print()
        print("✅ 응답:")
        print(answer)
        print()
        print("🎉 연결 성공! 이제 다른 스크립트들도 동작합니다.")
    except Exception as e:
        print()
        print(f"❌ 에러 발생: {e}")
        print("   - API 키가 맞는지 확인하세요")
        print("   - 인터넷 연결 확인")
        print("   - https://console.anthropic.com 에서 잔액 확인")
        sys.exit(1)


if __name__ == "__main__":
    main()
