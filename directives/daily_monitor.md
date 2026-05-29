# 일일 자동 모니터링 SOP

## 목표
매일 아침 9시 자동 실행 → 위험 수련회 발견 시 텔레그램으로 즉시 알림.

## 흐름
1. `execution/db_client.py` — 활성 수련회 목록
2. `execution/check_app_retreats.py:analyze_all` — Claude 위험도 분석
3. 🔴 빨강 1건 이상 → `execution/telegram_notify.py`로 텔레그램 발송
4. 결과 로그 → `data/monitor_log.json` (최근 90일)

## 실행
```bash
# 수동
python execution/daily_monitor.py

# 위험 없어도 요약 보내기
python execution/daily_monitor.py --force-notify

# 알림 안 보내고 보고서만
python execution/daily_monitor.py --no-notify
```

## 자동 실행 — macOS (launchd)
1. `~/Library/LaunchAgents/com.hyds.daily-monitor.plist` 생성 (가이드: TELEGRAM_SETUP.md)
2. `launchctl load ~/Library/LaunchAgents/com.hyds.daily-monitor.plist`
3. 매일 09:00 자동 실행됨

## 환경변수 (.env)
- `TELEGRAM_BOT_TOKEN` — Railway의 HYDS Ministry App 토큰 그대로
- `TELEGRAM_ADMIN_CHAT_ID` — 본인 텔레그램 chat_id

## 학습 기록
(첫 운영 후 채워질 예정)
