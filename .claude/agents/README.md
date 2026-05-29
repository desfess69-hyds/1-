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
           ├─ concept-planner (기획 팀장: 전략·캘린더·톤)
           ├─ scriptwriter    (카피 팀장: 스크립트·캡션·해시태그)
           └─ media-producer  (제작 팀장: 이미지·영상·업로드)
```

## 에이전트 목록

| 이름 | 역할 | 자동 트리거 키워드 |
|------|------|---------------------|
| `hyds-director` | 총괄 부장 (오케스트레이터) | 모든 요청을 먼저 받아 분해·위임·종합 |
| `retreat-planner` | 수련회 기획 | 기획, 프로그램, 주제 추천, 강사·장소, 예산안 |
| `retreat-monitor` | 진행 점검 | 점검, 체크리스트, 진척률, 위험, D-day, 현황 |
| `report-summarizer` | 사후 정리 | 후기, 결산, 회고, 강사 평가 |
| `church-communicator` | 교회 답변 | 교회 답변, 카톡 초안, 감사 인사, 공지 |
| `media-director` | 미디어 본부장 | 카드뉴스·릴스·영상·캠페인·디자인·캡션 (전체) |
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

## 두 가지 운영 모드 (헷갈리지 말 것)

1. **자동 자동화** (cron, 사람 없어도 동작): `execution/*.py` Python 스크립트 — directive(.md) 참조
2. **대화형 작업** (본인이 직접): Claude Code 채팅 → sub-agent 자동 호출 → execution 스크립트 실행

→ **둘 다 같은 directive를 참조**해서 결과가 일관됨.
