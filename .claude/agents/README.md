# HYDS Sub-Agents

Claude Code가 자동 로드하는 sub-agent들. 본인이 채팅하면 적절한 페르소나가 자동 호출됨.

## 조직 (계층 위임)

```
서동현 대표
└─ hyds-director (부장)
   ├─ [수련회 — 부장 직접 관리]
   │   ├─ retreat-planner   (기획 팀장)
   │   ├─ retreat-monitor   (점검 팀장)
   │   ├─ report-summarizer (리포트 팀장)
   │   └─ church-communicator (커뮤니케이션 팀장)
   └─ [미디어 — media-director 본부 경유]
       └─ media-director (미디어 본부장)
           ├─ trend-scout     (트렌드 팀장: 밈·챌린지·CapCut 정찰 — 가장 먼저)
           ├─ concept-planner (기획 팀장: 전략·캘린더·톤)
           ├─ scriptwriter    (카피 팀장: 스크립트·캡션·해시태그)
           └─ media-producer  (제작 팀장: 이미지·영상·업로드)
```

## 에이전트 목록

> 총 **10개** sub-agent (부장 1 + 수련회 4 + 미디어 본부장 1 + 미디어 팀장 4). 최상위 Claude가 부장(hyds-director) 역할을 겸합니다.

| 이름 | 역할 | 자동 트리거 키워드 |
|------|------|---------------------|
| `hyds-director` | 총괄 부장 (오케스트레이터) | 모든 요청을 먼저 받아 분해·위임·종합 |
| `retreat-planner` | 수련회 기획 | 기획, 프로그램, 주제 추천, 강사·장소, 예산안 |
| `retreat-monitor` | 진행 점검 | 점검, 체크리스트, 진척률, 위험, D-day, 현황 |
| `report-summarizer` | 사후 정리 | 후기, 결산, 회고, 강사 평가 |
| `church-communicator` | 교회 답변 | 교회 답변, 카톡 초안, 감사 인사, 공지 |
| `media-director` | 미디어 본부장 | 카드뉴스·릴스·영상·캠페인·디자인·캡션·트렌드 (전체) |
| `trend-scout` | 미디어 트렌드 팀장 | 트렌드, 밈, 챌린지, 바이럴, CapCut 템플릿, 요즘 유행, MZ/Y2K, 짤 |
| `concept-planner` | 미디어 기획 팀장 | 콘텐츠 전략, 캘린더, 톤앤매너, 시리즈 구성 |
| `scriptwriter` | 미디어 카피 팀장 | 카피, 스크립트, 캡션, 해시태그, 후크 문구 |
| `media-producer` | 미디어 제작 팀장 | 카드뉴스 이미지, 릴스/영상 제작, 썸네일, 업로드 (구 content-creator·reels-creator 통합) |

> ⚠️ **`hyds-director` 위임 한계**: Claude Code에서 sub-agent는 다른 sub-agent를 Task로 호출할 수 없습니다(중첩 미지원).
> 따라서 director를 **sub-agent로** 띄우면 5명 팀장에게 실제 위임이 안 됩니다. 진짜 오케스트레이션은
> 메인 대화(최상위 Claude)가 해야 합니다. director 페르소나는 "작업 분해·보고 형식" 가이드로는 유용하지만,
> 자동 위임을 원하면 이 분해 로직을 메인 레벨(CLAUDE.md)에 두는 것이 정석입니다.

## 사용 예시

본인이 Claude Code 안에서 그냥 평소처럼 채팅하면 됨:

> "○○교회 청년 30명, 8월 수련회 기획해줘"
→ `retreat-planner` 자동 호출

> "이번 주 위험 수련회 점검해줘"
→ `retreat-monitor` 자동 호출

> "기도 카드뉴스 8장 만들어줘"
→ `media-director`(미디어 본부장)가 받아 concept-planner→scriptwriter→media-producer로 분배

## 두 가지 실행 경로 (헷갈리지 말 것)

1. **자동 자동화** (cron, 사람 없어도 동작): `execution/*.py` Python 스크립트 — directive(.md) 참조
2. **대화형 작업** (본인이 직접): Claude Code 채팅 → sub-agent 자동 호출 → execution 스크립트 실행

→ **둘 다 같은 directive를 참조**해서 결과가 일관됨.

---

## 운영 모드 4종 (Operating Mode · v2.1)

부장은 매 응답 직전 메시지를 분석해 아래 4모드 중 하나로 답합니다. 자세한 규칙은 루트의 `CLAUDE_CODE_SYSTEM.md` 시스템 5 참조.

| 모드 | 트리거 | 시스템 1~4 | 응답 톤 |
|------|--------|-----------|--------|
| **STRICT** (기본) | 새 기능·리팩토링·코드 작업 | 풀 적용 (PLAN+CONTEXT+CHECKLIST+승인 대기) | 정식 보고서 |
| **REVIEW** | 캡처·다른 AI 결과 공유 | 시스템 1만 (필요시) | 짧은 분석 + 다음 액션 한 줄 |
| **FAST** | "급해"·"짧게"·"결론만" | 모두 면제 (사실관계는 유지) | 한 단락 이내 |
| **CHAT** | 가벼운 확인·의견 요청 | 모두 면제 | 자연 대화체 |

> ⚠️ **안전 가드**: 파일 삭제·git reset·DB 변경·유료 API 다회 호출 등 위험 작업은 **어떤 모드든 STRICT로 강제 승급**해 한 번 확인.

### 단축 명령 (메시지 앞에 붙여 모드 강제)

| 명령 | 효과 |
|------|------|
| `/빠르게` · `/짧게` | FAST 모드 강제 |
| `/잡담` | CHAT 모드 |
| `/판단` | FAST + 의견·판단만 (사실 X) |
| `/요약` | REVIEW + 보낸 자료 요약만 |
| `/긴급` | FAST + 즉시 행동 권장 (계획 단계 스킵) |
| `/조언` | CHAT + 비공식 조언 |
| `/정식` | STRICT 모드 강제 (FAST/CHAT 우회) |
