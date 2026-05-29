# 텔레그램 자동 알림 셋업

## ✅ Step 1 — .env에 텔레그램 토큰 추가

Railway → HYDS Ministry App → Variables 에서 두 값 복사:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ADMIN_CHAT_ID` (본인 chat_id)

`.env` 파일 마지막에 추가:
```
TELEGRAM_BOT_TOKEN=...
TELEGRAM_ADMIN_CHAT_ID=...
```

> ⚠️ `TELEGRAM_ADMIN_CHAT_ID`가 비어있으면 → 봇과 1:1 대화 시작 후 →
> `https://api.telegram.org/bot<TOKEN>/getUpdates` 열어서 본인 chat.id 찾기.

## ✅ Step 2 — 발송 테스트

```bash
source venv/bin/activate
python execution/telegram_notify.py
```

→ 텔레그램에 "🤖 HYDS 텔레그램 테스트" 메시지 도착하면 OK.

## ✅ Step 3 — 일일 모니터링 수동 실행

```bash
python execution/daily_monitor.py --force-notify
```

→ 보고서 생성 + 요약 텔레그램 발송 확인.

## ✅ Step 4 — 매일 9시 자동 실행 (macOS launchd)

```bash
# 1. plist의 __HYDS_PATH__ 를 실제 경로로 치환
HYDS_PATH="$HOME/Desktop/코딩/1인 회사 만들기"
sed "s|__HYDS_PATH__|$HYDS_PATH|g" \
    "$HYDS_PATH/com.hyds.daily-monitor.plist" \
    > ~/Library/LaunchAgents/com.hyds.daily-monitor.plist

# 2. 등록
launchctl load ~/Library/LaunchAgents/com.hyds.daily-monitor.plist

# 3. 확인
launchctl list | grep hyds
```

→ 매일 오전 9시 자동 실행. 결과는 `.tmp/launchd.out.log` 와 `.tmp/launchd.err.log`에.

### 해제 / 일시 정지
```bash
launchctl unload ~/Library/LaunchAgents/com.hyds.daily-monitor.plist
```

### 즉시 한 번 실행 (테스트)
```bash
launchctl start com.hyds.daily-monitor
```

## ✅ Step 5 (선택) — 시간 변경

`com.hyds.daily-monitor.plist`의 `Hour`/`Minute` 값 수정 후 다시 load.
여러 시간 보내고 싶으면 `StartCalendarInterval`을 `Array of dict`로 변경.

## 막힐 때

```bash
# 에러 로그 확인
tail -50 ~/Desktop/코딩/1인\ 회사\ 만들기/.tmp/launchd.err.log

# 수동 실행해서 즉시 에러 보기
python execution/daily_monitor.py
```
