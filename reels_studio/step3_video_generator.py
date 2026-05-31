"""Step 3: Atlas Cloud API (Kling v2.6 Pro)로 씬별 영상 생성."""
import os
import time
from pathlib import Path

import requests

BASE_URL = "https://api.atlascloud.ai/api/v1"
MODEL_T2V = "kwaivgi/kling-v2.6-pro/text-to-video"
MODEL_I2V = "kwaivgi/kling-v2.6-pro/image-to-video"

POLL_INTERVAL_SEC = 10
POLL_TIMEOUT_SEC = 1200


def _upload_image(image_path: Path, api_key: str) -> str:
    with open(image_path, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/model/uploadMedia",
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": f},
            timeout=120,
        )
    response.raise_for_status()
    body = response.json()
    data = body.get("data") or body
    url = (
        data.get("download_url")
        or data.get("url")
        or data.get("file_url")
        or data.get("fileUrl")
    )
    if not url:
        raise ValueError(f"No url in upload response: {body}")
    return url


def _start_prediction(
    prompt: str,
    aspect_ratio: str,
    duration: int,
    api_key: str,
    image_url: str | None = None,
) -> str:
    payload = {
        "model": MODEL_I2V if image_url else MODEL_T2V,
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "duration": duration,
    }
    if image_url:
        payload["image"] = image_url

    response = requests.post(
        f"{BASE_URL}/model/generateVideo",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    body = response.json()
    data = body.get("data") or body
    prediction_id = data.get("id") or data.get("prediction_id") or data.get("predictionId")
    if not prediction_id:
        raise ValueError(f"No prediction id in response: {body}")
    return prediction_id


def _poll_prediction(prediction_id: str, api_key: str) -> str:
    deadline = time.time() + POLL_TIMEOUT_SEC
    time.sleep(POLL_INTERVAL_SEC)
    while time.time() < deadline:
        try:
            response = requests.get(
                f"{BASE_URL}/model/prediction/{prediction_id}",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=30,
            )
        except requests.RequestException as e:
            print(f"      [poll] network error, retrying: {e}")
            time.sleep(POLL_INTERVAL_SEC)
            continue

        if response.status_code >= 500:
            try:
                body = response.json()
                inner = body.get("data") or {}
                inner_status = (inner.get("status") or "").lower()
                if inner_status in ("failed", "error", "canceled"):
                    err = inner.get("error") or body.get("message") or body
                    raise RuntimeError(f"Prediction {prediction_id} failed: {err}")
            except ValueError:
                pass
            print(f"      [poll] {response.status_code}, retrying...")
            time.sleep(POLL_INTERVAL_SEC)
            continue
        response.raise_for_status()
        body = response.json()
        data = body.get("data") or body
        status = (data.get("status") or "").lower()

        if status in ("succeeded", "completed", "success"):
            output = (
                data.get("outputs")
                or data.get("output")
                or data.get("video_url")
                or data.get("videoUrl")
            )
            if isinstance(output, list):
                output = output[0]
            if isinstance(output, dict):
                output = output.get("url") or output.get("video_url")
            if not output:
                raise ValueError(f"Succeeded but no output URL: {body}")
            return output

        if status in ("failed", "error", "canceled"):
            raise RuntimeError(f"Prediction {prediction_id} failed: {body}")

        time.sleep(POLL_INTERVAL_SEC)

    raise TimeoutError(f"Prediction {prediction_id} timed out after {POLL_TIMEOUT_SEC}s")


def _download(url: str, path: Path) -> None:
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 16):
                if chunk:
                    f.write(chunk)


def generate_videos(script: dict, aspect_ratio: str, output_dir: Path) -> list[Path]:
    api_key = os.environ["ATLAS_API_KEY"]

    video_dir = output_dir / "videos"
    video_dir.mkdir(exist_ok=True)

    paths: list[Path] = []
    for scene in script["scenes"]:
        scene_id = scene["scene_id"]
        out_path = video_dir / f"scene_{scene_id:02d}.mp4"

        if out_path.exists():
            print(f"      [scene {scene_id}] 기존 파일 재사용: {out_path.name}")
            paths.append(out_path)
            continue

        prompt = scene["visual_prompt"]
        duration = int(scene.get("duration", 5))

        image_url: str | None = None
        source_image = scene.get("source_image")
        if source_image:
            img_path = Path(source_image)
            if not img_path.is_absolute():
                img_path = (Path(__file__).parent / img_path).resolve()
            if not img_path.exists():
                raise FileNotFoundError(f"source_image not found: {img_path}")
            print(f"      [scene {scene_id}] uploading source image: {img_path.name}")
            image_url = _upload_image(img_path, api_key)

        mode = "image-to-video" if image_url else "text-to-video"
        print(f"      [scene {scene_id}] {mode} | prompt: {prompt[:55]}...")
        prediction_id = _start_prediction(prompt, aspect_ratio, duration, api_key, image_url)
        print(f"      [scene {scene_id}] prediction_id={prediction_id}, 폴링 중...")
        video_url = _poll_prediction(prediction_id, api_key)

        _download(video_url, out_path)
        print(f"      [scene {scene_id}] 다운로드 완료: {out_path.name}")
        paths.append(out_path)

    return paths
