# 수련회별 맞춤 To-Do 생성 SOP

## 목표
HYDS 마스터 체크리스트 + 앱 DB 현황 → 각 수련회별 "지금 해야 할 일" 도출.

## 사용 도구
- `execution/generate_retreat_todos.py`
- `MASTER_CHECKLIST` (코드 내장, D-day별 8단계 36항목)
- `execution/db_client.py` (앱 DB)
- `execution/claude_client.py` (AI 조언)

## 흐름
1. 활성 수련회 전체 조회
2. 각 수련회 D-day → 활성 카테고리 결정 (예: D-25 → "D-30 ~ D-14" + 이전 단계 미완료)
3. 앱 체크리스트의 완료 항목과 마스터 비교 → 미완료 추출
4. 최근 보고서에서 이슈 탐지
5. Claude로 수련회별 "구체적 조언 1~2문장"
6. .docx 1개 (표지 + 수련회별 페이지) → 텔레그램

## 권장 운영
- 매주 월요일 09:30 자동 실행 권장 (launchd plist 추가 가능)

## 학습 기록
- (운영 후) 키워드 매칭 정확도 → 미흡 시 마스터 → 앱 항목 매핑 테이블 도입
