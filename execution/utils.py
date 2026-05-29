"""공통 유틸 — 파일 입출력, 경로, 로깅 등."""
import json
from pathlib import Path
from datetime import datetime


PROJECT_ROOT = Path(__file__).parent.parent


def read_json(rel_path: str) -> dict | list:
    """data/ 같은 상대경로 → JSON 읽기."""
    path = PROJECT_ROOT / rel_path
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(rel_path: str, data) -> Path:
    """data를 JSON으로 저장 (UTF-8, 한글 유지)."""
    path = PROJECT_ROOT / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def timestamp() -> str:
    """파일명용 타임스탬프 (예: 20260529_153045)."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def log(msg: str):
    """간단한 로그 출력 (시간 포함)."""
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {msg}")
