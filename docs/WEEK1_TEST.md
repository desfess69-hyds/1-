# WEEK1_TEST.md — 미디어팀 Phase 1 실전 1주 운영 검증 (CHECKLIST 단계 7)

> **목적**: 실제로 "릴스 한 편"을 처음부터 끝까지 굴려보며 어색함·누락을 잡는다.
> **연관**: `docs/PLAN.md` §4(성공 기준), `docs/CHECKLIST.md` 단계 7
> **기록**: 발견한 것은 맨 아래 **운영 로그**에 적고, 끝나면 `directives/learnings.md`에 한 줄 남긴다.

---

## 사전 준비 (이미 완료 — 확인만)

- [x] Office dev 서버: `cd office && npm run dev` → http://localhost:5174/
- [x] 주간 트렌드 launchd 등록 (월 09:45) — `launchctl list | grep weekly-trends`
- [x] 미디어 execution 3종 + mock 검증 완료
- [ ] `.env`에 `ANTHROPIC_API_KEY` / `TELEGRAM_BOT_TOKEN` / `TELEGRAM_ADMIN_CHAT_ID` 채워짐

---

## 7-1. 채팅 흐름 확인 (Office)

1. http://localhost:5174/ 접속
2. 채팅에 입력: **"@미디어 평택교회 수련회 30초 릴스 짜줘"**
3. 확인 포인트:
   - [ ] 부장 → media-director 위임 표시
   - [ ] 미디어 회의실에 **trend-scout가 가장 먼저** 발언(트렌드 키워드 있을 때)
   - [ ] concept → script → producer 순서로 진행
   - [ ] 캐릭터 5명 겹침 없음

> CLI로 같은 재료를 만들고 싶으면(비용 발생):
> ```bash
> venv/bin/python execution/generate_media_package.py \
>     --topic "평택교회 수련회 홍보" --length 30 --with-trend --no-telegram
> ```
> 비용 0으로 형식만: 위 명령에 `--mock` 추가.

## 7-2. 결과물 9종 + Vrew 테스트

1. 폴더 확인: `.tmp/media_drafts/{날짜}_{슬러그}/`
   - [ ] 9종: trend_brief · concept · script · vrew_script · capcut_guide · caption · bgm · thumbnail_brief · assets/
2. `vrew_script.txt`를 Vrew에 붙여넣기
   - [ ] 한 줄 = 한 컷으로 **자동 분할**되는지
   - [ ] `[#키워드]`로 AI 이미지가 그럴듯하게 매칭되는지

## 7-3. CapCut 템플릿 테스트

1. `trend_brief.md`의 **CapCut 검색어**(정확한 문자열)를 CapCut 검색창에 입력
   - [ ] 실제로 그 템플릿이 나오는지 (안 나오면 검색어가 부정확 → learnings 기록)
   - [ ] 수명 라벨(🟢/🟡/🔴)이 현실과 맞는지

## 7-4. 주간 트렌드 텔레그램 (월 09:45)

- [ ] 다음 월요일 09:45 이후 텔레그램에 트렌드 카드 도착 확인
- 즉시 점검하려면(비용 0·발송X): `venv/bin/python execution/scout_trends.py --weekly --mock --no-telegram`
- 실제 1회(유료·발송O): `launchctl start com.hyds.weekly-trends` → 로그 `.tmp/weekly-trends.*.log`

## 7-5. self-anneal

- [ ] 위에서 발견한 어색함·누락을 아래 **운영 로그**에 적고, 대표 확인 후 `directives/learnings.md`에 한 줄 추가
- [ ] 필요하면 directive(SOP)·프롬프트·좌표를 고치고 재테스트

## 7-6. 마무리

- [ ] 운영 로그 정리 → `git commit "HYDS: 미디어팀 Phase 1 운영 학습 반영"`

---

## 운영 로그 (발견사항 — 자유 기록)

| 날짜 | 단계 | 발견 / 어색함 | 조치 |
|------|------|---------------|------|
|      | 7-1  |               |      |
|      | 7-2  |               |      |
|      | 7-3  |               |      |
|      | 7-4  |               |      |

---

## 알려진 주의점 (미리 공유)

- **비용**: "릴스 짜줘" 1회 = 부장1+본부장2+팀장4 ≈ Claude 최대 7콜 ≈ $0.5. 주간 트렌드 = ~$0.1/주.
- **캡션 오타 가능**: LLM이 가끔 오타(예: "어떘까요") → 발행 전 사람이 한 번 훑기.
- **트렌드 키워드 비어 있음**: `data/trend_keywords.json`의 `keywords`가 비어 자율 선정 중. 관심 키워드를 넣으면 정확도↑.
- **트렌드 신선도**: Claude 학습 컷오프 한계로 "최신" 트렌드는 검증 필요(scout SOP 3중 필터로 거름).
