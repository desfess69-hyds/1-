# Directive: 주간 리뷰 (Weekly Review)

매주 일요일 22:00, 지난 한 주의 자동화 활동을 집계하고 학습을 기록한다.

## 목표
- 한 주간 일일 모니터링·주간 To-Do·실시간 체크·결정 로그를 모아 요약
- `directives/learnings.md`에 배운 점 한 줄 누적 (부장 7원칙 #7)
- (opt-in) Claude 심층 회고 / 텔레그램 발송

## 입력 (data/)
- `monitor_log.json` — 일일 모니터링 실행 이력
- `weekly_todos_log.json` — 주간 To-Do 생성 이력
- `realtime_state.json` — 마지막 실시간 체크 시각
- `decisions.json` — 기록된 주요 결정

## 실행 도구
- `execution/weekly_review.py`
  - 기본(무료): 집계 + `.tmp/dossiers/weekly_review_YYYYMMDD.md` 저장 + learnings.md 한 줄 추가
  - `--ai`: Claude 심층 회고 (유료, 뼈대 — TODO)
  - `--notify`: 텔레그램 발송 (뼈대 — TODO)

## 출력
- `.tmp/dossiers/weekly_review_YYYYMMDD.md` (요약)
- `directives/learnings.md` (누적 한 줄)

## launchd 등록 가이드 (매주 일요일 22:00)

```bash
HYDS_PATH="$HOME/Desktop/코딩/1인 회사 만들기"
# 이미 있으면 먼저 언로드 (중복 방지)
launchctl unload ~/Library/LaunchAgents/com.hyds.weekly-review.plist 2>/dev/null
# __HYDS_PATH__ 치환해서 설치
sed "s|__HYDS_PATH__|$HYDS_PATH|g" \
    "$HYDS_PATH/com.hyds.weekly-review.plist" \
    > ~/Library/LaunchAgents/com.hyds.weekly-review.plist
# 로드
launchctl load ~/Library/LaunchAgents/com.hyds.weekly-review.plist
# 확인
launchctl list | grep hyds
# 즉시 테스트
launchctl start com.hyds.weekly-review
```

> 참고: macOS launchd에서 Weekday=0 과 7 은 모두 일요일. Mac이 꺼져 있거나 잠자기면
> 그 시각 실행은 건너뛰고, 깨어난 직후 한 번 실행된다.

## 학습 (이 directive에 누적)
- (아직 없음)
