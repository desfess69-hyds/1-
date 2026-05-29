# HYDS Sub-Agents

Claude Code가 자동 로드하는 sub-agent 5개. 본인이 채팅하면 적절한 페르소나가 자동 호출됨.

## 에이전트 목록

| 이름 | 역할 | 자동 트리거 키워드 |
|------|------|---------------------|
| `retreat-planner` | 수련회 기획 | 기획, 프로그램, 주제 추천, 강사·장소, 예산안 |
| `retreat-monitor` | 진행 점검 | 점검, 체크리스트, 진척률, 위험, D-day, 현황 |
| `report-summarizer` | 사후 정리 | 후기, 결산, 회고, 강사 평가 |
| `content-creator` | 인스타 카드뉴스 | 카드뉴스, 릴스, 캡션, 해시태그, 홍보 |
| `church-communicator` | 교회 답변 | 교회 답변, 카톡 초안, 감사 인사, 공지 |

## 사용 예시

본인이 Claude Code 안에서 그냥 평소처럼 채팅하면 됨:

> "○○교회 청년 30명, 8월 수련회 기획해줘"
→ `retreat-planner` 자동 호출

> "이번 주 위험 수련회 점검해줘"
→ `retreat-monitor` 자동 호출

> "기도 카드뉴스 8장 만들어줘"
→ `content-creator` 자동 호출

## 두 가지 운영 모드 (헷갈리지 말 것)

1. **자동 자동화** (cron, 사람 없어도 동작): `execution/*.py` Python 스크립트 — directive(.md) 참조
2. **대화형 작업** (본인이 직접): Claude Code 채팅 → sub-agent 자동 호출 → execution 스크립트 실행

→ **둘 다 같은 directive를 참조**해서 결과가 일관됨.
