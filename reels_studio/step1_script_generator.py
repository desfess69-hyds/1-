"""Step 1: 로컬 Ollama LLM으로 릴스 스크립트(JSON) 생성.

API 키 불필요. 사전 준비:
    brew install ollama
    ollama serve &
    ollama pull llama3.2
"""
import json
import os
import re
from pathlib import Path

import requests

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")


def _build_prompt(topic: str, style: str, duration: int, num_scenes: int) -> str:
    scene_sec = max(3, duration // num_scenes)
    return f"""You are a viral Instagram Reels scriptwriter.

Topic: "{topic}"
Style: "{style}"
Total duration: {duration} seconds
Number of scenes: {num_scenes} (each ~{scene_sec} seconds)

Return ONLY a valid JSON object. No prose, no markdown fences, no commentary.

Schema:
{{
  "title": "<Korean catchy title>",
  "hook": "<Korean 1-sentence opening hook>",
  "scenes": [
    {{
      "scene_id": 1,
      "narration": "<Korean narration, 1-2 short sentences, fits ~{scene_sec}s when spoken>",
      "visual_prompt": "<English cinematic prompt for text-to-video AI: subject, action, setting, lighting, camera>",
      "duration": {scene_sec}
    }}
  ],
  "cta": "<Korean call to action, 1 short sentence>"
}}

Rules:
- All `narration`, `hook`, `title`, `cta` must be in Korean.
- All `visual_prompt` must be in English, vivid and cinematic.
- Exactly {num_scenes} scenes.
- Output ONLY the JSON object.
"""


def _extract_json(text: str) -> dict:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start : end + 1]
    return json.loads(text)


def generate_script(topic: str, style: str, duration: int, output_dir: Path) -> dict:
    num_scenes = max(2, duration // 5)
    prompt = _build_prompt(topic, style, duration, num_scenes)

    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.8},
        },
        timeout=300,
    )
    response.raise_for_status()
    raw = response.json().get("response", "")
    script = _extract_json(raw)

    if "scenes" not in script or not script["scenes"]:
        raise ValueError(f"Invalid script JSON from Ollama: {raw[:500]}")

    script_path = output_dir / "script.json"
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)
    return script
