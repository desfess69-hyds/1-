"""
릴스 대본·자료 생성기 (media-producer + scriptwriter 실행 도구).

directive: directives/create_reels.md
결과물 6종 (PLAN.md §3.1):
    script.md, vrew_script.txt, capcut_guide.md, caption.txt, bgm.md, thumbnail_brief.md

사용 예:
    # mock (비용 0)
    python execution/generate_reels_script.py --topic "기도가 어려울 때" --mock

    # 실제 (Claude 1회 호출)
    python execution/generate_reels_script.py --topic "기도가 어려울 때" --length 30 --tone 공감형
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from execution.media_common import MOCK_BANNER, draft_dir, write_files, extract_json

SYSTEM = (
    "너는 HYDS 미디어 본부의 scriptwriter 겸 media-producer다. "
    "directives/create_reels.md의 30초 표준 구조(후크 0~3초 / 본문 3~25초 / CTA 25~30초)와 "
    "directives/media_brand_tone.md의 톤·금기를 지킨다. 따뜻하고 차분, 과장·어그로 금지. "
    "성경 인용은 출처 작게. 모든 출력 한국어."
)

# 생성할 6개 파일의 키 (JSON 키 = 파일명 stem)
FILE_KEYS = ["script", "vrew_script", "capcut_guide", "caption", "bgm", "thumbnail_brief"]
KEY_TO_FILE = {
    "script": "script.md",
    "vrew_script": "vrew_script.txt",
    "capcut_guide": "capcut_guide.md",
    "caption": "caption.txt",
    "bgm": "bgm.md",
    "thumbnail_brief": "thumbnail_brief.md",
}


def _mock_files(topic: str, length: int, tone: str) -> dict[str, str]:
    b = MOCK_BANNER
    return {
        "script.md": b + f"""# 릴스 대본 — {topic} ({length}초, {tone})
## 컷 시트 [더미]
| 시간 | 컷 | 자막 |
|------|----|------|
| 0~3초 | 후크 | "[더미] 요즘 {topic}?" |
| 3~25초 | 본문 | "[더미] 메시지 1개만, 컷 5~7개" |
| 25~30초 | CTA | "[더미] 저장하세요" |
""",
        "vrew_script.txt": f"""[MOCK] 한 줄 = 한 컷 (Vrew 자동 분할)
요즘 {topic}, 힘드시죠.
잠깐 멈춰서 숨을 쉬어요.
[#더미 #검증용]
오늘 1분만, 그저 앉아보세요.
@hyds.official
""",
        "capcut_guide.md": b + f"""# CapCut 가이드 [더미] — {topic}
## Step 1 템플릿 선택 → 검색 "더미 챌린지"
## Step 2 assets/ 이미지 3장 import
## Step 3 텍스트 인서트 (후크/본문/CTA)
## Step 4 BGM 라이브러리 검색
## Step 5 출력 1080×1920 30fps
""",
        "caption.txt": f"""[MOCK 캡션] {topic} — 첫 줄 후크 더미.
본문 2~4문장 더미. 저장하고 하루 한 번 보세요.

#기도 #말씀 #신앙 #기독청년 #청년부 #20대 #릴스 #shorts #일상릴스
#hyds #하이즈 #기독교 #예수님 #하나님사랑 #묵상 #큐티 #신앙생활
#청년사역 #교회 #수련회 #회복 #쉼 #위로 #더미해시태그 #검증용
#릴스추천 #explore #faith #christian #youth
""",
        "bgm.md": b + f"""# BGM 추천 [더미] — {topic}
- 분위기: 잔잔/따뜻
- 곡 후보 3: "Hope" / "Calm Piano" / "Morning" (모두 더미)
- 무료 출처: CapCut 라이브러리 / YouTube Audio Library
""",
        "thumbnail_brief.md": b + f"""# 썸네일 브리프 [더미] — {topic}
- 메인 카피: "[더미] {topic}"
- 색: HYDS 차분 톤 / 폰트: Pretendard
- 1080×1920 상단 1/3 안전영역에 텍스트
""",
    }


def build_reels_files(topic: str, length: int, tone: str, platform: str,
                      mock: bool, trend_brief: str = "") -> dict[str, str]:
    """6종 파일 {파일명: 내용} 반환. mock이면 더미, 아니면 Claude 1회 호출."""
    if mock:
        return _mock_files(topic, length, tone)

    from execution.claude_client import ask_claude
    trend_ctx = f"\n\n[trend-scout 트렌드 브리프 — 반영할 것]\n{trend_brief}" if trend_brief else ""
    prompt = (
        f"주제: {topic}\n길이: {length}초\n톤/컨셉: {tone}\n플랫폼: {platform}{trend_ctx}\n\n"
        "directives/create_reels.md를 따라 아래 6개를 만들어 JSON으로만 출력해줘 "
        "(다른 텍스트 금지). 키: script(대본+컷시트 마크다운), "
        "vrew_script(한 줄=한 컷 + [#키워드]), capcut_guide(단계별), "
        "caption(캡션+해시태그 30개), bgm(분위기·곡3·출처), thumbnail_brief(썸네일).\n"
        '{"script":"...","vrew_script":"...","capcut_guide":"...","caption":"...","bgm":"...","thumbnail_brief":"..."}'
    )
    raw = ask_claude(prompt, system=SYSTEM, max_tokens=4000)
    data = extract_json(raw)
    if not data:
        # 파싱 실패 → 형식은 유지하되 raw를 script.md에 담아 사람이 확인
        return {"script.md": f"# 파싱 실패 — Claude 원문\n\n{raw}"}
    return {KEY_TO_FILE[k]: str(data.get(k, "")).strip() for k in FILE_KEYS if data.get(k)}


def main():
    p = argparse.ArgumentParser(description="릴스 대본·자료 6종 생성")
    p.add_argument("--topic", required=True, help="주제 (예: 기도가 어려울 때)")
    p.add_argument("--length", type=int, default=30, help="길이(초): 15/30/60")
    p.add_argument("--tone", default="공감형", help="컨셉: 공감형/궁금형/챌린지형")
    p.add_argument("--platform", default="인스타 릴스", help="플랫폼")
    p.add_argument("--mock", action="store_true", help="Claude 호출 없이 더미 출력 (비용 0)")
    p.add_argument("--output", help="결과 폴더 직접 지정 (선택)")
    args = p.parse_args()

    base = Path(args.output) if args.output else draft_dir(args.topic)
    if args.output:
        (base / "assets").mkdir(parents=True, exist_ok=True)

    mode = "MOCK" if args.mock else "실제(Claude 호출)"
    print(f"🎬 릴스 대본 [{mode}] — {args.topic} ({args.length}초, {args.tone})")

    files = build_reels_files(args.topic, args.length, args.tone, args.platform, args.mock)
    written = write_files(base, files)
    print(f"✅ 저장: {base}  ({len(written)}개 파일)")
    for w in written:
        print(f"   - {w.relative_to(base.parent)}")
    if args.mock:
        print("ℹ️  MOCK 출력입니다. 실제 대본은 --mock 빼고 실행 (유료).")


if __name__ == "__main__":
    main()
