# CHECKLIST.md
# HYDS 미디어팀 릴스/쇼츠 시스템 — 세부 공정표

> **연관 PLAN**: `docs/PLAN.md`
> **연관 CONTEXT**: `docs/CONTEXT.md`
> **작업 단위 규칙**: 한 번에 1~2개 항목만 순차 수행 → 완료 즉시 `[x]` 갱신 + 완료 보고서 양식 제출.

---

## 단계 0 — 시스템 지침 정착 (선결 조건)

- [ ] 0-1. `CLAUDE_CODE_SYSTEM.md` 를 HYDS 폴더 루트에 복사
- [ ] 0-2. `docs/rules/backend_rules.md`, `docs/rules/frontend_rules.md` HYDS 폴더에 배치
- [ ] 0-3. `docs/PLAN.md`, `docs/CONTEXT.md`, `docs/CHECKLIST.md` HYDS 폴더에 정착
- [ ] 0-4. `CLAUDE.md` 부장 7원칙에 "PLAN/CONTEXT/CHECKLIST 3대 문서 의무 작성" 한 줄 추가
- [ ] 0-5. git 커밋: "HYDS: Claude Code System v2 지침 도입 + 미디어팀 PLAN"

---

## 단계 1 — directive(SOP) 4종 작성

- [ ] 1-1. `directives/media_brand_tone.md` — HYDS 톤·금기·자막·BGM 정책 (마스터 참조)
- [ ] 1-2. `directives/scout_trends.md` — 트렌드 수집·필터·CapCut 가이드 SOP
- [ ] 1-3. `directives/create_reels.md` — 30초/60초 릴스 제작 SOP
- [ ] 1-4. `directives/create_shorts.md` — 유튜브 쇼츠 변환 SOP
- [ ] 1-5. git 커밋: "HYDS: 미디어 directive 4종 추가"

---

## 단계 2 — 신규 sub-agent: trend-scout

- [ ] 2-1. `.claude/agents/trend-scout.md` 생성 (페르소나 + PROACTIVELY 키워드)
- [ ] 2-2. CLAUDE/AGENTS/GEMINI.md에 미디어 본부 산하 5번째 팀장으로 trend-scout 명시
- [ ] 2-3. media-director.md의 위임 기준에 트렌드 키워드 라우팅 추가
- [ ] 2-4. README의 sub-agent 목록 갱신
- [ ] 2-5. git 커밋: "HYDS: trend-scout sub-agent 신설"

---

## 단계 3 — execution 스크립트 3종

- [ ] 3-1. `execution/scout_trends.py` — 트렌드 키워드 → CapCut 가이드 JSON 생성
  - 입력: 키워드 5개 + 주제
  - 출력: `.tmp/media_drafts/{slug}/trend_brief.md`
  - 의존: `claude_client.py`
  - 예외 처리: API 키 누락·네트워크 실패·금기 키워드 필터
- [ ] 3-2. `execution/generate_reels_script.py` — 30초 릴스 대본 + 컷 시트
  - 입력: 주제 / 길이 / 톤 / 플랫폼
  - 출력: `script.md`, `vrew_script.txt`, `capcut_guide.md`, `caption.txt`, `bgm.md`, `thumbnail_brief.md`
- [ ] 3-3. `execution/generate_media_package.py` — 위 두 스크립트 묶음 + 폴더 정리 + 텔레그램 발송
- [ ] 3-4. 각 스크립트 단위 테스트 (mock 입력으로 결과물 검증)
- [ ] 3-5. git 커밋: "HYDS: 미디어 execution 3종 추가"

---

## 단계 4 — Office UI 확장 (10번째 캐릭터)

- [ ] 4-1. `office/src/data/agents.ts` — trend-scout 추가 (id, 색 #fb923c, position, meetingPosition)
- [ ] 4-2. 미디어 회의실 좌표 4명 → 5명으로 재배치 (테이블 둘러앉기 5명)
- [ ] 4-3. 백엔드 화이트리스트 `MEDIA_WORKERS`에 trend-scout 등록
- [ ] 4-4. 채팅 키워드 라우팅: "트렌드/밈/챌린지/유행/CapCut" → trend-scout
- [ ] 4-5. `runMediaHQ()` plan 생성 시 trend-scout 호출 조건 추가
- [ ] 4-6. F5 새로고침 + 화면 확인 (캐릭터 좌표 겹침 없는지)
- [ ] 4-7. git 커밋: "HYDS Office: trend-scout 캐릭터 + 회의실 5명 배치"

---

## 단계 5 — 자동화: 주간 트렌드 보고

- [ ] 5-1. `com.hyds.weekly-trends.plist` 생성 (매주 월 09:30, daily-monitor와 같은 시각이 아니어야 하므로 09:45로 조정)
- [ ] 5-2. `scout_trends.py --weekly` 모드 — 본인이 입력한 관심 키워드 5개 자동 처리
- [ ] 5-3. `data/trend_keywords.json` — 본인이 직접 관리하는 관심 키워드 풀
- [ ] 5-4. 텔레그램 발송: 트렌드 5개 + CapCut 검색어 + 추천 시간 카드 형식
- [ ] 5-5. launchd 등록 가이드 README 추가
- [ ] 5-6. git 커밋: "HYDS: 주간 트렌드 자동 보고 자동화"

---

## 단계 6 — 시스템 지침 4가지 자동 검증

- [ ] 6-1. **컨텍스트 매뉴얼**: trend-scout가 작업 시 directives/media_brand_tone.md 자동 참조 확인
- [ ] 6-2. **작업 기억**: 모든 sub-agent에 "PLAN/CONTEXT/CHECKLIST 참조" 지침 명시
- [ ] 6-3. **품질 검사**:
  - [ ] 모든 execution 스크립트에 try-except 적용
  - [ ] API 키 하드코딩 없음 확인 (grep)
  - [ ] 무한 루프 위험 없음 확인
- [ ] 6-4. **완료 보고서**: 본 작업 끝나면 정해진 양식으로 보고서 제출
- [ ] 6-5. git 커밋: "HYDS: Phase 1 검증 완료"

---

## 단계 7 — 실전 운영 1주 검증

- [ ] 7-1. 채팅 명령 "@미디어 평택교회 수련회 30초 릴스 짜줘" — 흐름 확인
- [ ] 7-2. 결과물 9개 파일 확인 → Vrew에 vrew_script.txt 붙여넣기 테스트
- [ ] 7-3. CapCut에서 trend_brief.md의 검색어로 템플릿 찾기 테스트
- [ ] 7-4. 매주 월 09:30 트렌드 보고 텔레그램 도착 확인
- [ ] 7-5. 발견된 어색함·누락 → `directives/learnings.md`에 한 줄 추가 (self-anneal)
- [ ] 7-6. git 커밋: "HYDS: 미디어팀 Phase 1 운영 학습 반영"

---

## 단계 8 — Phase 1 종결 보고

- [ ] 8-1. 미디어팀 운영 한 달 후 → 부장이 "주간 종합 보고"에 미디어팀 지표 포함
- [ ] 8-2. Remotion·YouTube API 등 Phase 2 검토 여부 결정
- [ ] 8-3. PLAN.md 상태를 "✅ Phase 1 완료, Phase 2 검토" 로 변경

---

## 보류·차기 (Out of Phase 1)

- ⏭️ Remotion 자동 영상 렌더
- ⏭️ ElevenLabs 음성 자동 생성
- ⏭️ YouTube Data API 트렌드 자동 수집
- ⏭️ Instagram Graph API 자동 업로드
- ⏭️ 수련회 본부 본부장(operations-director) 신설
- ⏭️ analytics-lead, community-manager sub-agent 신설

---

## 진척률 계산

총 항목 수: **52개**
완료: **0**
진척률: **0%**

---

## 한 줄 의사결정 메모

이 CHECKLIST는 대표 승인 후 단계 0부터 순차 진행. 각 단계 진행 전 부장이 "이번에 N-1과 N-2 진행할게요. OK?" 한 줄로 확인 받는 패턴 유지.
