# PLAN.md
# HYDS 미디어팀 — 릴스/쇼츠 제작 시스템 전체 계획서

> **작성일**: 2026-05-29
> **작성자**: HYDS Director (부장)
> **승인자**: 서동현 대표
> **상태**: ⏳ 승인 대기

---

## 1. 구현 목표

기독교 청년 대상 **인스타 릴스·유튜브 쇼츠 제작 시스템**을 HYDS 미디어 본부 안에 구축한다. 본인(대표)이 무엇을 만들지 한 줄만 입력하면 **재료(대본·자막·BGM·자료·트렌드 가이드)가 자동 생성**되고, Vrew/CapCut에서 5분 안에 영상으로 완성되는 구조.

### 1.1 운영 시나리오 (To-Be)

```
대표: "@미디어 이번 주 트렌드로 평택교회 수련회 홍보 릴스 만들어줘"
   ↓
부장 → media-director에게 위임
   ↓
media-director가 4명 팀장 분배:
   1. trend-scout    → CapCut 인기 템플릿 검색 + 우리 적용 방안
   2. concept-planner → 한 줄 컨셉 + 톤앤매너 결정
   3. scriptwriter   → 대본 + 자막 + 캡션 + 해시태그
   4. media-producer → 자료 패키지 (Vrew/CapCut 친화 .txt + 이미지 + BGM 추천)
   ↓
본인 결과물 받아서 Vrew 또는 CapCut에서 5분 편집
   ↓
인스타 업로드 (수동 또는 Graph API 자동)
```

### 1.2 명확한 비목표 (Out of Scope)

- ❌ 완전 자동 영상 렌더링 (Remotion·FFmpeg) — Phase 2 검토
- ❌ AI 음성·아바타 (ElevenLabs·HeyGen) — Phase 3 검토
- ❌ Instagram Graph API 자동 업로드 — Phase 3
- ❌ CapCut 자체 자동화 (API 없음, 매크로 안정성 ↓)

---

## 2. 전체 아키텍처 및 로직 구조

### 2.1 미디어 본부 조직도 (현재 + 신규)

```
🎬 미디어 본부 (media-director) ← 기존
   ├ trend-scout         ← 🆕 신규 (트렌드 정찰병)
   ├ concept-planner     ← 기존 (전체 구상)
   ├ scriptwriter        ← 기존 (대본·카피)
   └ media-producer      ← 기존 (제작·자료 패키지)
```

### 2.2 새 sub-agent: `trend-scout`

- **역할**: 인스타·틱톡·CapCut 트렌드를 발견해 우리 주제에 맞게 적용 가이드 제공
- **결과물**: CapCut 검색어, 우리 적용 방안, 필요 자료 목록, 예상 소요 시간
- **자동 실행**: 매주 월요일 09:30 — "이번 주 트렌드 5개" 텔레그램

### 2.3 영상 콘텐츠 유형별 도구 매핑

| 유형 | 도구 | 자동화 | 시간 |
|------|------|--------|------|
| **A. 트렌드 콘텐츠** (밈·챌린지) | CapCut + trend-scout 가이드 | 60% | 5분 |
| **B. 메시지 콘텐츠** (말씀·격려) | Vrew + 대본 자동 | 80% | 5분 |
| **C. 정보 콘텐츠** (수련회 홍보) | Vrew or 카드뉴스 자동 | 85% | 5분 |

비율 목표: A 40% / B 30% / C 30% (운영하면서 조정)

### 2.4 데이터 흐름

```
[사용자 명령] → /api/chat (SSE)
     ↓ 부장 plan JSON
     ↓ media-director 위임 (sub-delegating)
     ↓ ┌─ trend-scout (선택적)
       ├─ concept-planner
       ├─ scriptwriter
       └─ media-producer
     ↓ 본부장 종합 (sub-worker-done × 4)
     ↓ 부장에게 보고
     ↓ 최종 응답
```

### 2.5 결과물 저장 구조

```
.tmp/media_drafts/{YYYYMMDD}_{slug}/
├── trend_brief.md        # 트렌드 + CapCut 검색어
├── concept.md            # 컨셉·톤·시리즈 위치
├── script.md             # 한국어 대본 + 컷 시트
├── vrew_script.txt       # Vrew 붙여넣기용 (한 줄 = 한 컷)
├── capcut_guide.md       # CapCut 작업 단계별 가이드
├── caption.txt           # 인스타 캡션 + 해시태그 30개
├── bgm.md                # BGM 분위기·곡명 3개·무료 출처
├── thumbnail_brief.md    # 썸네일 디자인 브리프
└── assets/               # 필요 이미지·자료
```

---

## 3. 연동 및 데이터 흐름

### 3.1 신규 execution 스크립트

| 파일 | 역할 | 의존성 |
|------|------|--------|
| `execution/scout_trends.py` | 트렌드 키워드 → CapCut 가이드 생성 | claude_client |
| `execution/generate_reels_script.py` | 주제 → 30초 릴스 대본 + 컷 시트 + Vrew 친화 | claude_client |
| `execution/generate_media_package.py` | 4개 결과물 묶어 폴더 생성 + 텔레그램 발송 | 위 + telegram |

### 3.2 신규 directive (SOP)

| 파일 | 정의 |
|------|------|
| `directives/scout_trends.md` | 트렌드 수집·필터링·적용 방안 작성 SOP |
| `directives/create_reels.md` | 30초/60초 릴스 제작 SOP |
| `directives/create_shorts.md` | 유튜브 쇼츠 변환 SOP (릴스 → 쇼츠) |
| `directives/media_brand_tone.md` | HYDS 톤·금기·자막 폰트·BGM 정책 |

### 3.3 자동화 추가

| 작업 | 시점 | 스크립트 |
|------|------|---------|
| 주간 트렌드 보고 | 매주 월 09:30 | `scout_trends.py --weekly` |
| 매월 콘텐츠 캘린더 생성 | 매월 1일 | `concept_planner --monthly` (Phase 2) |

### 3.4 Office 대시보드 변경

- 캐릭터 10명 = 부장 + 수련회 4명 + 미디어 본부장 1 + 미디어 팀장 4
- 미디어 회의실에 trend-scout 추가 좌표
- 채팅 라우팅 키워드 갱신: `트렌드/밈/챌린지/유행` → trend-scout

### 3.5 환경 변수 (.env)

추가 필요:
```
# Phase 1: 없음 (Claude API만 사용)
# Phase 2 (선택): YOUTUBE_API_KEY (트렌드 자동 수집)
# Phase 3 (선택): INSTAGRAM_GRAPH_API_TOKEN, ELEVENLABS_API_KEY
```

### 3.6 위험·제약

| 위험 | 대응 |
|------|------|
| Claude API 비용 — 트렌드 명령마다 5~7회 호출 | confirm 다이얼로그 + 주간 1회 자동 (예상 $1.5/주) |
| CapCut 템플릿이 빨리 식는다 | trend-scout가 "수명" 라벨 (🟢 성숙 / 🟡 정점 / 🔴 식는 중) 표기 |
| 기독교 가치관 충돌 밈 | scout SOP에 금기 키워드 리스트 + LLM 필터 |
| 본인 시간 — 5분 편집조차 부담될 때 | Phase 2 Remotion 자동 렌더 옵션 |

### 3.7 Phase 분할

- **Phase 1 (이번 작업)**: trend-scout 신설 + 3개 execution 스크립트 + 4개 directive + Office UI + 주간 트렌드 자동화. **Vrew/CapCut 친화 출력만**.
- **Phase 2 (한 달 후 검토)**: Remotion 자동 렌더 / YouTube API 트렌드 수집
- **Phase 3 (3개월 후 검토)**: Instagram Graph API 자동 업로드 / ElevenLabs 음성

---

## 4. 성공 기준 (Definition of Done)

- [ ] trend-scout가 자연어 명령 받으면 CapCut 검색어 + 적용 방안 5개 생성
- [ ] 채팅창에 "릴스 짜줘" 입력 → media-director가 4명 팀장 모두 호출 → 결과 묶음 받음
- [ ] `.tmp/media_drafts/{slug}/` 폴더에 9개 파일 자동 생성
- [ ] Vrew 친화 .txt를 Vrew에 붙여넣었을 때 자동 컷 분할 정상 동작
- [ ] 매주 월요일 09:30 트렌드 보고 텔레그램 도착
- [ ] Office 대시보드에 trend-scout 캐릭터 + 회의실 모임 시각화
- [ ] 시스템 지침 4가지 (자동 매뉴얼·작업 기억·품질 검사·완료 보고) 모두 준수

---

## 5. 다음 액션

이 PLAN.md에 대한 **대표 승인 대기 중** (시스템 2의 2단계).

승인되면 → `CHECKLIST.md`의 원자 단위 항목을 1~2개씩 순차 수행. 각 항목 완료마다 `[x]` 갱신 + 완료 보고서 양식 준수.
