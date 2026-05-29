# 실시간 알림 SOP

## 목표
팀장이 보고서를 올리는 순간 (최대 5분 지연) → 긴급 건만 텔레그램.

## 동작
1. 5분마다 `realtime_check.py` 실행 (launchd)
2. 지난 실행 이후 신규 `retreat_reports` 조회
3. **결정론적 판정** (Python 코드):
   - `issues` 비어있지 않음 → 🔴
   - 상태 필드에 위험 키워드 (취소/지연/문제/사고 등) → 🔴
   - D-day ≤ 7 수련회의 신규 보고 → 🟡
4. 🔴/🟡 발견 시 Claude로 한 줄 요약 + 조치 권고
5. 텔레그램 발송

## 상태 보존
`data/realtime_state.json` — 마지막으로 본 report_id

## 첫 셋업
```bash
python execution/realtime_check.py --reset
```
→ 현재 시점까지를 "본 것"으로 처리. 다음 실행부터 진짜 신규만 알림.

## 자동 실행
`com.hyds.realtime.plist` (5분 주기 launchd)

## 학습 기록
- 위험 키워드는 운영하면서 추가 (예: "병원", "구급차" 등)
- 오탐 많으면 → 키워드 정밀화 또는 결정론 판정 + LLM 2차 확인
