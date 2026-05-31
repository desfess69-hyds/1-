# HYDS

> 1인 AI 회사 — 기독교 수련회 기획·점검 + 인스타 카드뉴스 제작·업로드

## 구조

3-Layer 아키텍처 — 자세한 내용은 `CLAUDE.md` 참고.

```
HYDS/
├── CLAUDE.md / AGENTS.md / GEMINI.md   ← AI 에이전트 운영 지침
├── 00_마스터_기획서.md                  ← 전체 사업/시스템 기획
├── directives/                          ← 한국어 SOP (Claude가 읽음)
├── execution/                           ← Python 스크립트
├── data/                                ← 영구 데이터 (강사·장소·이력)
├── templates/                           ← 카드뉴스 배경, 양식
├── .tmp/                                ← 임시 파일 (gitignore)
├── .env                                 ← API 키 (gitignore!)
└── requirements.txt
```

## 처음 셋업

```bash
# 1. Python 가상환경
python3 -m venv venv
source venv/bin/activate   # Windows는 venv\Scripts\activate

# 2. 패키지 설치
pip install -r requirements.txt

# 3. API 키 설정
cp .env.example .env
# .env 파일 열어서 ANTHROPIC_API_KEY=sk-ant-... 채우기

# 4. 연결 테스트
python execution/claude_client.py
```

## 사용법

Claude Code(또는 Antigravity 내 Claude)에게 자연어로 지시:

> "○○교회 청년 30명, 2026-08-15부터 2박3일 수련회 기획해줘. 예산 250만원"

→ Claude가 `directives/plan_retreat.md`를 읽고 → `execution/generate_retreat_plan.py` 실행 → `.tmp/dossiers/`에 기획안 저장

## 자동화 (launchd 스케줄)

macOS `launchd`로 정기 작업을 돌립니다. plist는 `__HYDS_PATH__` 플레이스홀더를 쓰므로 등록 시 실제 경로로 치환합니다.

| plist | 작업 | 주기 |
|-------|------|------|
| `com.hyds.daily-monitor` | 진행 수련회 점검 | 매일 09:30 |
| `com.hyds.realtime` | 실시간 위험 체크 | 수시 |
| `com.hyds.weekly-review` | 주간 종합 리뷰 | 매주 일 22:00 |
| `com.hyds.weekly-todos` | 주간 To-Do | 매주 |
| `com.hyds.archive` | 종료 수련회 아카이브 | — |
| **`com.hyds.weekly-trends`** | **주간 트렌드 보고 (trend-scout)** | **매주 월 09:45** |

### 등록 / 해제

```bash
HYDS="$HOME/Desktop/코딩/1인 회사 만들기"
NAME=com.hyds.weekly-trends          # 등록할 plist 이름

# 1) 경로 치환 후 LaunchAgents에 복사
sed "s|__HYDS_PATH__|$HYDS|g" "$HYDS/$NAME.plist" > "$HOME/Library/LaunchAgents/$NAME.plist"

# 2) 로드(등록) / 확인 / 해제
launchctl load   "$HOME/Library/LaunchAgents/$NAME.plist"
launchctl list | grep hyds
launchctl unload "$HOME/Library/LaunchAgents/$NAME.plist"
```

### 주간 트렌드 — 먼저 mock으로 점검 (비용 0)

```bash
# 관심 키워드는 data/trend_keywords.json 의 keywords 배열에 직접 입력 (비우면 자율 선정)
venv/bin/python execution/scout_trends.py --weekly --mock          # 더미·발송X (형식/폴더 확인)
venv/bin/python execution/scout_trends.py --weekly                 # 실호출(유료 ~$0.1) + 텔레그램 발송
venv/bin/python execution/scout_trends.py --weekly --no-telegram   # 실호출, 발송만 생략
```

> 결과는 `.tmp/media_drafts/{날짜}_주간-트렌드_trends/trend_brief.md`에 저장되고, **실호출 시 요약 카드가 텔레그램으로 발송**됩니다(`.env`의 `TELEGRAM_BOT_TOKEN`·`TELEGRAM_ADMIN_CHAT_ID` 필요). 미설정/실패해도 잡은 죽지 않고 로컬 저장은 유지됩니다.

## 원칙

1. **Directive에 한국어로 SOP 쓴다** — 코딩 아니라 사용설명서
2. **AI는 판단, 스크립트는 실행** — 반복 작업은 Python으로
3. **에러는 학습 기회** — self-anneal 루프로 시스템 강화
4. **로컬은 임시, 결과는 클라우드** — 기획안은 노션/드라이브, 카드뉴스는 인스타
