#!/bin/bash
# HYDS 자동 셋업 — 한 번만 실행하면 됨
# 사용: bash setup.sh

set -e  # 에러 나면 즉시 중단

cd "$(dirname "$0")"
echo "🚀 HYDS 셋업 시작..."
echo ""

# 1. Python 버전 확인
echo "1️⃣  Python 확인..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 가 설치되지 않았어요. https://python.org 에서 설치 후 다시 실행."
    exit 1
fi
PY_VERSION=$(python3 --version)
echo "   ✅ $PY_VERSION"
echo ""

# 2. 가상환경 생성
echo "2️⃣  가상환경(venv) 생성..."
if [ -d "venv" ]; then
    echo "   ⚠️  venv 이미 있음 — 건너뜀"
else
    python3 -m venv venv
    echo "   ✅ venv 생성 완료"
fi
echo ""

# 3. 패키지 설치
echo "3️⃣  패키지 설치 중 (anthropic, Pillow, python-dotenv, requests)..."
./venv/bin/pip install --quiet --upgrade pip
./venv/bin/pip install --quiet -r requirements.txt
echo "   ✅ 패키지 설치 완료"
echo ""

# 4. .env 파일 준비
echo "4️⃣  .env 파일 확인..."
if [ -f ".env" ]; then
    echo "   ⚠️  .env 이미 있음 — 건너뜀"
else
    cp .env.example .env
    echo "   ✅ .env 생성 (.env.example에서 복사)"
fi
echo ""

# 5. API 키 체크
echo "5️⃣  API 키 확인..."
if grep -q "sk-ant-여기에" .env 2>/dev/null; then
    echo ""
    echo "⚠️  마지막 한 가지: .env 파일을 열어서 API 키를 넣어주세요."
    echo ""
    echo "   1. https://console.anthropic.com → API Keys 에서 키 발급"
    echo "   2. .env 파일 열고 ANTHROPIC_API_KEY=sk-ant-... 채우기"
    echo "   3. 다음 명령으로 연결 테스트:"
    echo ""
    echo "      source venv/bin/activate"
    echo "      python execution/claude_client.py"
    echo ""
else
    echo "   ✅ API 키 설정된 것으로 보임"
    echo ""
    echo "🎉 셋업 완료! 다음 명령으로 테스트:"
    echo "      source venv/bin/activate"
    echo "      python execution/claude_client.py"
fi
