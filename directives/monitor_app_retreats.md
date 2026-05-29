# 앱 수련회 자동 모니터링 SOP

## 목표
HYDS Ministry App DB에 등록된 진행 중인 모든 수련회를 스캔해서,
각 수련회의 위험 요소(진척률 저조, 보고 지연, D-day 임박 미준비 등)를
자동 감지하고 보고서로 정리한다.

## 사용할 도구
1. `execution/db_client.py` — DB 연결 및 조회 (공통 모듈)
2. `execution/check_app_retreats.py` — 전체 스캔 + AI 분석
3. `execution/claude_client.py` — Claude API

## 절차
1. `db_client.list_active_retreats()` 호출 → 활성 수련회 목록
2. 각 수련회마다 `get_retreat_full()` → 체크리스트·보고서 상세
3. Claude에게 다음 컨텍스트로 위험도 분석 요청:
   - 수련회 정보 (교회·주제·D-day)
   - 체크리스트 진척률 (단계별)
   - 최근 보고서 (currentStatus, issues 등)
4. 결과: 수련회별 위험도 (낮음/중간/높음) + 즉시 조치 권고

## 출력
`.tmp/dossiers/app_monitor_{YYYY-MM-DD}.md` 보고서.

## 위험 판정 기준 (참고)
- **높음**: D-7 이내인데 진척률 < 70%, 또는 최근 보고서에 'issues' 비어있지 않음
- **중간**: D-30 이내인데 진척률 < 50%, 또는 7일간 보고 없음
- **낮음**: 정상 페이스

## 다음 단계 (Phase 추가)
- 텔레그램 알림 자동 발송 (앱에 이미 TELEGRAM_BOT_TOKEN 있음)
- cron으로 매일 아침 9시 자동 실행

## 학습 기록
(첫 운영 후 채워질 예정)
