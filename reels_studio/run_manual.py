"""수동 작성한 script.json으로 릴스 제작 (step 2~4만 실행).

사용법:
    python run_manual.py path/to/script.json [aspect_ratio]

예시:
    python run_manual.py my_script.json 9:16
"""
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

from step2_voice_generator import generate_voice
from step3_video_generator import generate_videos
from step4_editor import edit_final

load_dotenv()


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_manual.py <script.json> [aspect_ratio]")
        sys.exit(1)

    script_path = Path(sys.argv[1]).resolve()
    if not script_path.exists():
        print(f"❌ 스크립트 파일을 찾을 수 없음: {script_path}")
        sys.exit(1)

    aspect_ratio = sys.argv[2] if len(sys.argv) >= 3 else "9:16"

    script = json.loads(script_path.read_text(encoding="utf-8"))

    title = script.get("title") or script_path.stem
    safe_title = title.replace(" ", "_").replace("/", "_")
    output_dir = Path(__file__).parent / "output" / safe_title
    output_dir.mkdir(parents=True, exist_ok=True)

    saved_script = output_dir / "script.json"
    with open(saved_script, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)

    print(f"=== 수동 스크립트로 릴스 제작: '{title}' ({aspect_ratio}) ===")
    print(f"출력 폴더: {output_dir}")
    print(f"씬: {len(script['scenes'])}개\n")

    print("[1/3] 음성 합성 중 (ElevenLabs)...")
    audio_path = generate_voice(script, output_dir)
    print(f"      → {audio_path.name}\n")

    print("[2/3] 영상 생성 중 (Atlas Cloud / Kling v2.6 Pro)...")
    video_paths = generate_videos(script, aspect_ratio, output_dir)
    print(f"      → {len(video_paths)}개 클립\n")

    print("[3/3] FFmpeg 편집 중...")
    final_path = edit_final(video_paths, audio_path, script, output_dir)
    print(f"      → {final_path}\n")

    print(f"✅ 완료: {final_path}")


if __name__ == "__main__":
    main()
