"""
수련회 점검 스크립트 (뼈대).

기획안 파일을 읽고 단계별(D-30/D-7/D-1/당일/사후) 체크리스트 결과를 보고서로.
Phase 2에서 본격 구현.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from execution.claude_client import ask_claude


def main():
    parser = argparse.ArgumentParser(description="HYDS 수련회 점검")
    parser.add_argument("--plan", required=True, help="점검할 기획안 .md 파일")
    parser.add_argument("--stage", required=True, choices=["D-30", "D-7", "D-1", "당일", "사후"])
    args = parser.parse_args()

    plan_text = Path(args.plan).read_text(encoding="utf-8")

    prompt = f"""다음은 수련회 기획안입니다:

---
{plan_text}
---

현재 점검 시점: {args.stage}

`directives/review_retreat.md`의 {args.stage} 체크리스트를 기반으로,
각 항목을 ✅ / ⚠️ / ❌로 평가하고 한 줄 코멘트를 달아 보고서로 작성하세요.
빠진 정보가 있으면 솔직히 '확인 필요'로 표시하세요.
"""
    report = ask_claude(prompt, max_tokens=4000)
    print(report)


if __name__ == "__main__":
    main()
