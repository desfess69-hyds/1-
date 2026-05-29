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

## 원칙

1. **Directive에 한국어로 SOP 쓴다** — 코딩 아니라 사용설명서
2. **AI는 판단, 스크립트는 실행** — 반복 작업은 Python으로
3. **에러는 학습 기회** — self-anneal 루프로 시스템 강화
4. **로컬은 임시, 결과는 클라우드** — 기획안은 노션/드라이브, 카드뉴스는 인스타
