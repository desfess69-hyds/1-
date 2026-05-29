# CONTEXT.md
# HYDS 미디어팀 — 개발 맥락 및 히스토리 노트

> **연관 PLAN**: `docs/PLAN.md` (미디어팀 릴스/쇼츠 제작 시스템)

---

## 1. 기술 스택 및 라이브러리 선정 이유

### 1.1 Python + Claude API (재료 생성 단계)

| 선택 | 이유 |
|------|------|
| **Python** (Anthropic SDK) | 기존 HYDS 3-Layer 아키텍처의 execution 레이어와 일관. 새 언어 도입 시 학습 곡선 ↑ |
| **Claude (Anthropic)** | 본인이 API 키 보유. 한국어 톤 정확. 다른 LLM 도입 시 키 추가 부담 |
| **python-docx, Pillow** | 이미 설치되어 있음. 새 의존성 최소화 |

### 1.2 Vrew + CapCut (영상 편집 단계)

| 도구 | 선택 이유 | 비선택 이유 (다른 도구) |
|------|----------|-------------------------|
| **Vrew** | 한국어 AI 음성 최강. 텍스트 → 영상 자동. 한국 회사라 트렌드 즉반영 | API 없음 → 100% 자동 불가 |
| **CapCut** | 인스타·틱톡 트렌드 템플릿 즉시 반영. 본인이 이미 익숙할 가능성 ↑ | API 없음. 대시보드 자동화 불가 |
| Remotion (비선택) | 100% 코드 자동화 가능하지만 정적 텍스트 위주 → 트렌드 적용 약함 | Phase 2 검토 |
| HeyGen (비선택) | AI 아바타 어색. 기독교 톤과 충돌 가능 | 검토 종결 |
| DaVinci Resolve (비선택) | 강력하지만 학습 곡선 ↑↑. 코딩 초보엔 부담 | 검토 종결 |

### 1.3 본부장 패턴 (Hierarchical Task Decomposition)

- **PDF 「자율형 AI 에이전트」 2.1절** 명시: Manager Agent → Worker Agent 분해 권장
- 부장(hyds-director)이 4~7명 직접 관리하던 평면 구조 → 본부장(media-director) 1명만 관리
- 부장 부담 감소, 본부 단위 일관성 ↑, 추후 본부 추가 용이 (수련회 본부, 영업 본부 등)

### 1.4 Server-Sent Events (SSE)

- 이미 `/api/chat`이 SSE 스트리밍 채택
- 본부장 2단계 위임 시각화에 `sub-delegating`, `sub-worker-done` 이벤트 추가 (이미 구현됨)
- WebSocket보다 단순, 브라우저 호환성 우수

---

## 2. 비즈니스 요구사항 및 예외 조건

### 2.1 비즈니스 컨텍스트 (대표 = 서동현, HYDS)

- 1인 회사. 코딩 초보 → 시스템이 알아서 도와줘야 함.
- **메인 사업**: 기독교 단체 수련회 기획·점검
- **서브 사업**: 인스타 카드뉴스·릴스·쇼츠 제작·업로드 (자금 확보 + 브랜드 인지도)
- **수익 우선순위 낮음** — 시스템 안착 단계
- **운영 환경**: Mac + Antigravity + Claude Code + Claude API 키 보유

### 2.2 톤·금기 (HYDS 미디어 브랜드)

**HYDS 톤**: 따뜻하고 차분, 깊이 있음, 과장 X, 청년 눈높이.

**금기**:
- 정치 풍자·이단 비판·교파 비교 ❌
- "꼭 보세요!"·"절대 놓치지 마세요!" 같은 어그로 ❌
- 신앙 강요 톤 (특정 교리 강조) ❌
- 미성년자가 등장하는 트렌드 → 보호자 동의 절차 명시

### 2.3 반드시 방어해야 하는 예외

1. **Claude API 키 누락** → 친절한 에러 + 발급 가이드 출력
2. **트렌드 검색 실패** → 캐시된 작년 동기 트렌드 fallback
3. **결과물 폴더 권한 오류** → `.tmp/` 생성 자동 + 안내
4. **텔레그램 발송 실패** → 로컬 파일 + Office 활동 로그에는 남기기
5. **회의실 캐릭터 좌표 겹침** → 그리드 자동 재배치
6. **사용자 한 명령에 트렌드 + 기획 + 대본 + 자료 다 요청** → 부장이 비용 confirm 후 진행

### 2.4 비용 가드

- 한 번의 "릴스 짜줘" 명령 = 부장 1 + 본부장 2 + 팀장 4 = **최대 Claude 7회 호출 ≈ $0.50**
- 주간 트렌드 자동 보고 = 부장 1 + scout 1 = **약 $0.10/회**
- 월 예상 = (주 5회 명령 × $0.50) + (주 1회 자동 × $0.10) = **약 $11/월**
- 한도 초과 방지: confirm 다이얼로그 + 일일 콜 카운터 (Phase 2)

---

## 3. 참고 자료 및 레퍼런스

### 3.1 내부 문서

- `CLAUDE.md` / `AGENTS.md` / `GEMINI.md` — 부장 7원칙 + 본부장 패턴
- `directives/retreat_team_leader_checklist.md` — 수련회 도메인 지식
- `directives/learnings.md` — 운영 학습 누적
- `data/decisions.json` — 대표 결정 이력 (부장 학습용)

### 3.2 외부 자료

- **자율형 AI 에이전트 가이드 PDF** (2026-05-29 업로드) — Manager/Worker 패턴 근거
- **Agent Instructions.docx** — 3-Layer 아키텍처 원본
- **Claude Code System v2** (2026-05-29 업로드) — 본 시스템 지침 출처
- **Anthropic API 문서**: <https://docs.anthropic.com>
- **Vrew 공식**: <https://vrew.voyagerx.com>
- **CapCut Templates 검색**: <https://www.capcut.com/templates>

### 3.3 기존 코드 참고 위치

| 신규 코드 작성 시 참고 | 위치 |
|----------------------|------|
| Claude API 호출 패턴 | `execution/claude_client.py` |
| 텔레그램 발송 패턴 | `execution/telegram_notify.py` |
| Office SSE 클라이언트 | `office/src/hooks/useOfficeSimulation.ts` |
| 본부장 plan JSON 처리 | `office/vite.config.ts:runMediaHQ` |
| sub-agent .md 양식 | `.claude/agents/media-director.md` |

### 3.4 결정 로그 (이 PLAN 작성 시 의사결정)

| 결정 | 근거 |
|------|------|
| Phase 1은 Vrew/CapCut 친화 출력만 | 본인 코딩 부담 최소 + 검증 필요 |
| Remotion 즉시 도입 안 함 | 자동 영상은 매력적이나 정적 텍스트 위주 → 트렌드 약함 |
| trend-scout 별도 sub-agent 신설 | concept-planner에 통합하면 톤·전략 vs 트렌드 분리 흐려짐 |
| 본부장이 4명 모두 호출하지 않고 선택적 호출 | "메시지 콘텐츠"는 trend-scout 불필요 → 비용 절감 |
| 매주 1회 자동 트렌드만 진행, 매일 X | 트렌드 검증 일주일 단위 충분, 비용 ↓ |
