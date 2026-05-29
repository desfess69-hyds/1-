# 실시간 알림 셋업

## ✅ Step 1 — 첫 상태 초기화 (필수, 한 번만)

```bash
cd ~/Desktop/코딩/1인\ 회사\ 만들기
source venv/bin/activate
python execution/realtime_check.py --reset
```

→ "현재까지의 모든 보고서를 본 것으로 처리". 다음부터 진짜 신규만 추적.

## ✅ Step 2 — 수동 테스트 (선택)

신규 보고서가 있는 척 만들어볼 수 있지만, 그냥 자동 등록 후 며칠 운영하면서 검증 추천.

지금 한 번 그냥 돌려보면:
```bash
python execution/realtime_check.py
```
→ "(신규 보고 없음)" 정상.

## ✅ Step 3 — 5분 주기 launchd 등록

```bash
HYDS_PATH="$HOME/Desktop/코딩/1인 회사 만들기"
sed "s|__HYDS_PATH__|$HYDS_PATH|g" \
    "$HYDS_PATH/com.hyds.realtime.plist" \
    > ~/Library/LaunchAgents/com.hyds.realtime.plist
launchctl load ~/Library/LaunchAgents/com.hyds.realtime.plist
launchctl list | grep hyds
```

→ `com.hyds.realtime` 보이면 성공. 5분마다 자동 실행.

## ✅ Step 4 — 모니터링

```bash
# 정상 출력 로그
tail -50 .tmp/realtime.out.log

# 에러 로그 (비어있어야 정상)
tail -50 .tmp/realtime.err.log

# 상태 (마지막 본 report_id)
cat data/realtime_state.json
```

## 해제 / 일시 정지
```bash
launchctl unload ~/Library/LaunchAgents/com.hyds.realtime.plist
```

## 즉시 한 번 실행 (테스트)
```bash
launchctl start com.hyds.realtime
```

## 주기 변경
plist의 `StartInterval` 숫자(초) 변경 → unload → load.
- 5분 = 300
- 10분 = 600
- 1분 = 60 (DB 부담 ↑)

## 막힐 때
에러 로그 통째로 + 실행한 명령어 알려주세요.
