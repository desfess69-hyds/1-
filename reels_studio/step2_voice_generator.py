"""Step 2: ElevenLabs API로 씬별 MP3 생성 후 하나로 합치기."""
import os
import subprocess
from pathlib import Path

import requests

ELEVENLABS_URL = "https://api.elevenlabs.io/v1/text-to-speech"
DEFAULT_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
DEFAULT_MODEL_ID = os.environ.get("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
DEFAULT_STABILITY = float(os.environ.get("ELEVENLABS_STABILITY", "0.5"))
DEFAULT_SIMILARITY = float(os.environ.get("ELEVENLABS_SIMILARITY", "0.75"))
DEFAULT_STYLE = float(os.environ.get("ELEVENLABS_STYLE", "0.0"))
AUDIO_SPEED = float(os.environ.get("AUDIO_SPEED", "1.0"))


def _tts(text: str, voice_id: str, api_key: str, out_path: Path) -> None:
    response = requests.post(
        f"{ELEVENLABS_URL}/{voice_id}",
        headers={
            "Accept": "audio/mpeg",
            "xi-api-key": api_key,
            "Content-Type": "application/json",
        },
        json={
            "text": text,
            "model_id": DEFAULT_MODEL_ID,
            "voice_settings": {
                "stability": DEFAULT_STABILITY,
                "similarity_boost": DEFAULT_SIMILARITY,
                "style": DEFAULT_STYLE,
                "use_speaker_boost": True,
            },
        },
        timeout=120,
    )
    response.raise_for_status()
    out_path.write_bytes(response.content)


def _apply_speed(path: Path, speed: float) -> None:
    if abs(speed - 1.0) < 0.01:
        return
    tmp = path.with_suffix(".speed.mp3")
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(path),
            "-filter:a", f"atempo={speed:.3f}",
            "-c:a", "libmp3lame", "-q:a", "2",
            str(tmp),
        ],
        check=True, capture_output=True,
    )
    tmp.replace(path)


def _concat_mp3s(parts: list[Path], output: Path) -> None:
    concat_file = output.parent / "_audio_concat.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for p in parts:
            f.write(f"file '{p.absolute()}'\n")
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_file),
            "-c:a", "libmp3lame", "-q:a", "2",
            str(output),
        ],
        check=True,
        capture_output=True,
    )
    concat_file.unlink(missing_ok=True)


def generate_voice(script: dict, output_dir: Path) -> Path:
    api_key = os.environ["ELEVENLABS_API_KEY"]
    voice_id = DEFAULT_VOICE_ID

    audio_dir = output_dir / "audio"
    audio_dir.mkdir(exist_ok=True)

    segments: list[tuple[str, str]] = []
    if script.get("hook"):
        segments.append(("00_hook", script["hook"]))
    for scene in script["scenes"]:
        segments.append((f"{scene['scene_id']:02d}_scene", scene["narration"]))
    if script.get("cta"):
        segments.append(("99_cta", script["cta"]))

    part_paths: list[Path] = []
    for name, text in segments:
        path = audio_dir / f"{name}.mp3"
        _tts(text, voice_id, api_key, path)
        _apply_speed(path, AUDIO_SPEED)
        part_paths.append(path)

    final_audio = output_dir / "narration.mp3"
    _concat_mp3s(part_paths, final_audio)
    return final_audio
