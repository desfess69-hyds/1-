# 노션 자동 정리 셋업

매번 수련회 끝나면 노션 DB에 자동 아카이브.

---

## ✅ Step 1 — 노션 Integration 만들기 (5분)

1. https://www.notion.so/my-integrations 접속
2. `New integration` 클릭
3. 이름: `HYDS Archive`
4. Associated workspace: 본인 워크스페이스
5. Capabilities: ✅ Read content, ✅ Update content, ✅ Insert content
6. `Submit`
7. **Internal Integration Token** 복사 (`secret_...` 로 시작)

---

## ✅ Step 2 — 노션에 DB 만들기 (10분)

새 페이지 만들고 `/database` → `Table - Inline` 선택.

이름: `HYDS 수련회 아카이브`

**컬럼 10개** (이름과 타입을 정확히):

| 컬럼명 | 타입 |
|--------|------|
| 교회명 | Title (기본) |
| 주제 | Text |
| 기간 | Date |
| 장소 | Text |
| 참가 인원 | Number |
| 최종 진척률 | Number (Number format) |
| 팀장 | Text |
| 원본 ID | Number |
| 후기 요약 | Text |
| 파일/링크 | Text |

→ 컬럼명이 다르면 코드가 실패함. 정확히 한국어로.

---

## ✅ Step 3 — DB에 Integration 연결

DB 페이지에서 우측 상단 `...` → `Connections` (또는 `Add connections`) → `HYDS Archive` 선택.

---

## ✅ Step 4 — DB ID 복사

DB 페이지 URL 형태:
```
https://www.notion.so/{워크스페이스}/abc1234567890def...?v=...
                                  ↑─────── 이 32자가 DB ID ────↑
```

물음표(?) 앞까지의 32자(또는 하이픈 포함 36자). 둘 다 OK.

---

## ✅ Step 5 — .env에 추가

```
NOTION_TOKEN=secret_복사한_토큰
NOTION_DATABASE_ID=abc1234567890def...
```

---

## ✅ Step 6 — 패키지 설치 + 연결 테스트

```bash
cd ~/Desktop/코딩/1인\ 회사\ 만들기
source venv/bin/activate
pip install notion-client

# 연결 확인
python execution/notion_client.py
```

→ "✅ DB 연결 성공: 'HYDS 수련회 아카이브'" + 컬럼 10개 출력되면 OK.

---

## ✅ Step 7 — 미리보기 (안전한 첫 실행)

```bash
python execution/archive_to_notion.py --dry-run
```

→ 어떤 수련회를 올릴지, 어떤 요약이 나올지 미리 봄. 노션엔 안 씀.

---

## ✅ Step 8 — 진짜 실행

```bash
python execution/archive_to_notion.py
```

→ 종료된(`status=done`) 수련회 모두 노션 페이지로 생성됨.
한 번 올라간 건 `data/notion_archive_state.json`에 기록되어 중복 안 됨.

---

## ✅ Step 9 — 매일 10시 자동 실행 등록

```bash
HYDS_PATH="$HOME/Desktop/코딩/1인 회사 만들기"
sed "s|__HYDS_PATH__|$HYDS_PATH|g" \
    "$HYDS_PATH/com.hyds.archive.plist" \
    > ~/Library/LaunchAgents/com.hyds.archive.plist
launchctl load ~/Library/LaunchAgents/com.hyds.archive.plist
launchctl list | grep hyds
```

---

## 막힐 때 흔한 원인

- **컬럼 이름 불일치** → 노션 DB의 컬럼명을 코드와 정확히 맞추기
- **Integration 미연결** → DB 페이지에서 Connections 다시 확인
- **DB ID 잘못 복사** → 페이지 ID(상위 페이지)랑 DB ID(내부 표) 구분
