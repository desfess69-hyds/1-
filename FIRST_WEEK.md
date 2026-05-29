# HYDS 첫 주 셋업 (자동화 버전)

**3단계로 끝.** 막히면 에러 메시지 복사해서 Claude에게.

---

## ✅ Step 1 — 자동 셋업 한 줄 (5분)

Antigravity 터미널에서:

```bash
cd ~/Desktop/코딩/1인\ 회사\ 만들기
bash setup.sh
```

→ Python 가상환경, 패키지 설치, `.env` 파일 자동 생성까지 한 번에.

---

## ✅ Step 2 — API 키 넣기 (3분, 본인만 가능)

`.env` 파일을 Antigravity에서 열기 → 한 줄 수정:

```
ANTHROPIC_API_KEY=sk-ant-여기에_본인_키_넣기
```
↓ 본인 키로 교체
```
ANTHROPIC_API_KEY=sk-ant-api03-실제_본인_키
```

키 없으면:
1. https://console.anthropic.com 접속
2. API Keys 메뉴 → Create Key
3. 복사해서 위 파일에 붙여넣기

---

## ✅ Step 3 — 연결 테스트 (1분)

```bash
source venv/bin/activate
python execution/claude_client.py
```

✅ 성공:
```
🤖 HYDS Claude 연결 테스트
✅ 응답: 안녕! HYDS 시스템이 정상 작동합니다
🎉 연결 성공!
```

❌ 실패하면 → 에러 메시지 통째로 Claude에 붙여넣기. 같이 고치자.

---

## 🎯 그 다음 — 첫 기획안 테스트

```bash
python execution/generate_retreat_plan.py \
  --church "테스트교회" \
  --target "청년 25명" \
  --period "2026-08-15~17, 2박 3일" \
  --budget 2500000 \
  --message "회복"
```

→ `.tmp/dossiers/테스트교회_*_기획안.md` 열어보기.

처음엔 어색할 수 있음. 결과 보고 → `directives/plan_retreat.md` 수정 → 다시 실행.
**이게 self-anneal 루프.** 매번 시스템이 똑똑해짐.

---

## 📌 이번 주 안에 할 일

- [ ] Step 1~3 완료 (셋업)
- [ ] 첫 기획안 1건 생성 + 결과 검토
- [ ] `data/speakers.json`에 알고 있는 강사 1~2명 입력
- [ ] `data/venues.json`에 알고 있는 장소 1~2곳 입력
- [ ] (선택) 친한 교회에 무료 기획안 1건 제공 → 피드백
- [ ] Git 초기화 (`git init && git add . && git commit -m "init"`)

---

## 막힐 때

다음 메시지에:
1. 어느 Step에서 막혔는지
2. 실행한 명령어
3. 에러 메시지 전체

그대로 붙여넣어. 같이 풀자.
