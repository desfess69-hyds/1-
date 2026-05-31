"""
미디어 본부 execution 공통 헬퍼.

여러 미디어 스크립트(scout_trends / generate_reels_script / generate_media_package)가
import해서 쓰는 헬퍼다. 슬러그 생성·결과물 폴더·mock 배너·JSON 추출 담당.

- 결과물은 모두 `.tmp/media_drafts/{YYYYMMDD}_{slug}/` 아래에 모인다 (PLAN.md §2.5).
- `--mock` 모드에서는 Claude 호출 없이 더미 텍스트만 채워 폴더/파일 형식을 검증한다.
"""
import json
import re
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
MEDIA_DRAFTS = PROJECT_ROOT / ".tmp" / "media_drafts"

# mock 출력 맨 위에 붙는 경고 — 실수로 진짜 결과물로 오인하지 않도록
MOCK_BANNER = (
    "<!-- ⚠️ MOCK 출력 — 실제 Claude 호출 없이 만든 더미입니다. "
    "폴더/파일 형식 검증용이며 내용은 의미 없습니다. -->\n\n"
)


def slugify(text: str) -> str:
    """주제 문자열 → 폴더/파일용 슬러그. 한글은 유지, 공백·특수문자는 하이픈."""
    s = (text or "draft").strip().lower()
    s = re.sub(r"[\s/\\]+", "-", s)          # 공백·슬래시 → 하이픈
    s = re.sub(r"[^0-9a-z가-힣\-]", "", s)    # 한글/영소문/숫자/하이픈만 남김
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s[:40] or "draft"


def draft_dir(topic: str, kind: str = "") -> Path:
    """`.tmp/media_drafts/{YYYYMMDD}_{slug}[_kind]/` 폴더(+assets) 생성 후 경로 반환."""
    today = datetime.now().strftime("%Y%m%d")
    name = f"{today}_{slugify(topic)}" + (f"_{kind}" if kind else "")
    d = MEDIA_DRAFTS / name
    (d / "assets").mkdir(parents=True, exist_ok=True)
    return d


def write_file(path: Path, content: str) -> Path:
    """텍스트 파일 저장 (UTF-8, 부모 폴더 자동 생성)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def write_files(base: Path, files: dict[str, str]) -> list[Path]:
    """{상대경로: 내용} 묶음을 base 폴더 아래에 모두 저장. 저장된 경로 리스트 반환."""
    written = []
    for rel, content in files.items():
        written.append(write_file(base / rel, content))
    return written


def split_sections(raw: str, valid_names: list[str]) -> dict[str, str]:
    """'===FILE:파일명===' 마커로 구분된 멀티파일 응답을 {파일명: 내용}으로 분해.

    JSON보다 잘림·이스케이프에 강하다. 응답이 중간에 truncate돼도 그 전까지
    완성된 섹션은 그대로 살아남는다. valid_names에 있는 파일명만 채택.
    """
    out: dict[str, str] = {}
    parts = re.split(r"(?m)^={2,}\s*FILE:\s*(.+?)\s*={2,}\s*$", raw or "")
    # parts = [머리말, name1, content1, name2, content2, ...]
    for i in range(1, len(parts) - 1, 2):
        name = parts[i].strip()
        content = parts[i + 1].strip()
        if name in valid_names and content:
            out[name] = content
    return out


def extract_json(raw: str) -> dict:
    """Claude 응답에서 JSON 블록만 뽑아 파싱. 실패하면 빈 dict."""
    s = (raw or "").strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", s)
    if fence:
        s = fence.group(1).strip()
    first, last = s.find("{"), s.rfind("}")
    if first != -1 and last != -1:
        s = s[first:last + 1]
    try:
        return json.loads(s)
    except (json.JSONDecodeError, ValueError):
        return {}
