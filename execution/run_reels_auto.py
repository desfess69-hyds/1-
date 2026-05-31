"""릴스 auto 모드 wrapper — HYDS 미디어 산출물 → reels_studio 자동 영상 제작.

directive: directives/create_reels.md (mode: auto)

HYDS 미디어 본부가 만든 `vrew_script.txt`(+선택 `script.md`)를 reels_studio가
이해하는 `script.json` 스키마로 변환한 뒤, reels_studio/run_manual.py(step 2~4)를
호출해 음성·영상·편집 파이프라인을 돌린다.

왜 run_all.py가 아니라 run_manual.py인가:
    run_all.py는 step1에서 Ollama로 대본을 **새로 생성**하므로 우리가 공들여
    변환한 script.json을 버린다. run_manual.py는 기존 script.json을 그대로 받아
    step 2~4(음성→영상→편집)만 실행하므로 변환 결과가 보존된다.

⚠️ 유료 API 안전장치:
    영상 파이프라인은 ElevenLabs(음성)·영상 생성 API 등 **유료 호출**을 한다.
    그래서 기본 동작은 **변환만**(script.json 생성) 하고 멈춘다.
    실제 파이프라인 실행은 명시적으로 `--run` 을 줘야 한다.

사용 예:
    # 변환만 (비용 0) — script.json 만들고 실행 명령 안내
    python execution/run_reels_auto.py --draft ".tmp/media_drafts/20260531_기도/"

    # 변환 + 실제 영상 제작 (유료 API 호출)
    python execution/run_reels_auto.py --draft ".tmp/media_drafts/20260531_기도/" --run

    # 길이·비율·제목 지정
    python execution/run_reels_auto.py --draft <폴더> --duration 30 --aspect 9:16 --title "기도가 어려울 때"
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
REELS_STUDIO = PROJECT_ROOT / "reels_studio"

# vrew_script.txt 라인 분류용 패턴
TAG_LINE = re.compile(r"^\s*\[#.*\]\s*$")          # [#기도 #청년] 형태 (Vrew 이미지 매칭 태그)
HANDLE_LINE = re.compile(r"^\s*@[\w.]+\s*$")        # @hyds.official 형태 (CTA 핸들)
COMMENT_LINE = re.compile(r"^\s*(음성|BGM)\s*:", re.IGNORECASE)  # "음성: ...", "BGM: ..." 추천 댓글


def _extract_tags(tag_line: str) -> list[str]:
    """'[#기도 #청년 #답답함]' → ['기도', '청년', '답답함']."""
    return re.findall(r"#([^\s#\[\]]+)", tag_line)


def _build_visual_prompt(tags: list[str]) -> str:
    """Vrew 태그(한국어 키워드) → text-to-video용 영어 visual_prompt 스캐폴드.

    실제 영상 생성기(step3)가 쓰는 영어 프롬프트의 **뼈대**만 만든다.
    번역이 아니라 키워드를 그대로 끼운 자리표시자이며, media-producer가
    필요하면 다듬는다. (정확한 영어 프롬프트 자동화는 step3 교체 시 별도.)
    """
    keywords = ", ".join(tags) if tags else "calm reflective scene"
    return (
        f"Cinematic vertical 9:16 b-roll, mood keywords: {keywords}. "
        "Soft natural lighting, shallow depth of field, no on-screen text, "
        "warm contemplative atmosphere."
    )


def parse_vrew_script(text: str) -> tuple[list[dict], str]:
    """vrew_script.txt 본문 → (scenes, cta).

    - 빈 줄로 구분된 블록 = 한 컷(scene).
    - 블록 안의 일반 줄 = 내레이션, `[#...]` 줄 = 영상 태그, `@핸들` = CTA 표식.
    - "음성:"·"BGM:" 추천 댓글 줄은 무시.
    - @핸들이 들어간 마지막 블록은 CTA로 분리(원하면 별도 처리).
    """
    blocks = re.split(r"\n\s*\n", text.strip())
    scenes: list[dict] = []
    cta = ""

    for block in blocks:
        narration_lines: list[str] = []
        tags: list[str] = []
        has_handle = False

        for raw in block.splitlines():
            line = raw.strip()
            if not line or COMMENT_LINE.match(line):
                continue
            if TAG_LINE.match(line):
                tags.extend(_extract_tags(line))
            elif HANDLE_LINE.match(line):
                has_handle = True  # @hyds.official 등 — 내레이션에서 제외
            else:
                narration_lines.append(line)

        narration = " ".join(narration_lines).strip()
        if not narration:
            continue

        # @핸들이 있고 내레이션이 짧으면 CTA 블록으로 간주
        if has_handle and len(narration) <= 40:
            cta = narration
            continue

        scenes.append({
            "scene_id": len(scenes) + 1,
            "narration": narration,
            "visual_prompt": _build_visual_prompt(tags),
            "_tags": tags,  # 변환 추적용 (아래에서 제거)
        })

    return scenes, cta


def _title_from_script_md(script_md: Path) -> str | None:
    """script.md 첫 번째 '# 제목' 헤딩에서 제목 추출."""
    if not script_md.exists():
        return None
    for line in script_md.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^#\s+(.*)", line.strip())
        if m:
            return m.group(1).strip()
    return None


def build_script_json(draft_dir: Path, duration: int, title: str | None) -> dict:
    """HYDS 드래프트 폴더 → reels_studio script.json dict."""
    vrew = draft_dir / "vrew_script.txt"
    if not vrew.exists():
        raise FileNotFoundError(f"vrew_script.txt 없음: {vrew}")

    scenes, cta = parse_vrew_script(vrew.read_text(encoding="utf-8"))
    if not scenes:
        raise ValueError(f"vrew_script.txt에서 씬을 하나도 못 뽑았습니다: {vrew}")

    # 전체 길이를 씬 수로 균등 분배 (최소 3초)
    per = max(3, round(duration / len(scenes)))
    for s in scenes:
        s["duration"] = per
        s.pop("_tags", None)

    resolved_title = (
        title
        or _title_from_script_md(draft_dir / "script.md")
        or draft_dir.name
    )

    return {
        "title": resolved_title,
        "hook": scenes[0]["narration"] if scenes else "",
        "scenes": scenes,
        "cta": cta or "저장하고 하루 한 번 보세요.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="HYDS vrew_script.txt → reels_studio script.json 변환 + (선택) 영상 제작"
    )
    parser.add_argument("--draft", required=True,
                        help="HYDS 미디어 드래프트 폴더 (vrew_script.txt 포함)")
    parser.add_argument("--duration", type=int, default=30,
                        help="총 영상 길이(초). 씬 수로 균등 분배 (기본 30)")
    parser.add_argument("--aspect", default="9:16",
                        help="영상 비율 (기본 9:16 세로)")
    parser.add_argument("--title", default=None,
                        help="영상 제목 (생략 시 script.md 헤딩 → 폴더명 순으로 추론)")
    parser.add_argument("--run", action="store_true",
                        help="변환 후 reels_studio/run_manual.py 실제 실행 (⚠️ 유료 API 호출)")
    args = parser.parse_args()

    draft_dir = Path(args.draft).resolve()
    if not draft_dir.is_dir():
        print(f"❌ 드래프트 폴더를 찾을 수 없음: {draft_dir}")
        sys.exit(1)

    # 1) 변환
    script = build_script_json(draft_dir, args.duration, args.title)
    out_path = draft_dir / "script.json"
    out_path.write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✅ 변환 완료: {out_path}")
    print(f"   제목: {script['title']}")
    print(f"   씬: {len(script['scenes'])}개 × {script['scenes'][0]['duration']}초")
    print(f"   CTA: {script['cta']}")

    run_cmd = [sys.executable, "run_manual.py", str(out_path), args.aspect]

    # 2) 실행 (opt-in)
    if not args.run:
        print("\n💡 변환만 했습니다 (비용 0). 실제 영상 제작은 --run 을 붙이세요.")
        print(f"   또는 직접: cd {REELS_STUDIO} && {' '.join(run_cmd[:1])} {' '.join(run_cmd[1:])}")
        return

    if not REELS_STUDIO.is_dir():
        print(f"❌ reels_studio 폴더 없음: {REELS_STUDIO}")
        sys.exit(1)

    print(f"\n🎬 영상 파이프라인 실행 (cwd={REELS_STUDIO})...")
    result = subprocess.run(run_cmd, cwd=REELS_STUDIO)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
