"""릴스 자동 제작 파이프라인 - 메인 실행기.

사용법:
    python run_all.py "갓생 루틴" "동기부여형" 30 9:16
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

from step1_script_generator import generate_script
from step2_voice_generator import generate_voice
from step3_video_generator import generate_videos
from step4_editor import edit_final

load_dotenv()


def main():
    if len(sys.argv) < 5:
        print('Usage: python run_all.py "<topic>" "<style>" <duration_seconds> <aspect_ratio>')
        print('Example: python run_all.py "갓생 루틴" "동기부여형" 30 9:16')
        sys.exit(1)

    topic = sys.argv[1]
    style = sys.argv[2]
    duration = int(sys.argv[3])
    aspect_ratio = sys.argv[4]

    safe_topic = topic.replace(" ", "_").replace("/", "_")
    output_dir = Path(__file__).parent / "output" / safe_topic
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== 릴스 제작 시작: '{topic}' ({style}, {duration}s, {aspect_ratio}) ===")
    print(f"출력 폴더: {output_dir}\n")

    print("[1/4] 스크립트 생성 중 (Ollama)...")
    script = generate_script(topic, style, duration, output_dir)
    print(f"      → {len(script['scenes'])}개 씬 생성 완료\n")

    print("[2/4] 음성 합성 중 (ElevenLabs)...")
    audio_path = generate_voice(script, output_dir)
    print(f"      → {audio_path.name}\n")

    print("[3/4] 영상 생성 중 (Atlas Cloud / Kling v2.6 Pro)...")
    video_paths = generate_videos(script, aspect_ratio, output_dir)
    print(f"      → {len(video_paths)}개 클립 다운로드 완료\n")

    print("[4/4] FFmpeg 편집 중...")
    final_path = edit_final(video_paths, audio_path, script, output_dir)
    print(f"      → {final_path}\n")

    print(f"✅ 완료: {final_path}")


if __name__ == "__main__":
    main()
