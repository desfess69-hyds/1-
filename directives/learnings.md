# HYDS 학습 로그 (Learnings)

부장(hyds-director)이 작업을 마칠 때마다 배운 점을 **한 줄씩** 추가한다.
실행 전 이 파일에서 유사 사례를 찾아 같은 실수를 반복하지 않는다 (부장 7원칙 #4, #7).

형식: `- YYYY-MM-DD | [상황] 무슨 일이 있었나 → 교훈/적용`

---

<!-- 여기서부터 한 줄씩 누적 -->
- 2026-05-29 | [주간리뷰] 모니터링 2회·주간To-Do 1회·결정 0건 → 자동 집계 기록
- 2026-05-30 | media-director 본부장 패턴 도입 — 평면 7명 위임 → 2단계 위임으로 부장 부담 감소
- 2026-05-30 | System v2.1 도입 — 운영 모드 4종(STRICT/REVIEW/FAST/CHAT)으로 일상 대화는 가볍게, 코드 작업은 풀 시스템. 부장 원칙에 0번(운영 모드 인식) 추가. 위험 작업은 모드 무관 STRICT 강제 승급.
- 2026-05-30 | trend-scout 미디어 본부 4번째 팀장 정착 — 트렌드 작업 시 가장 먼저 실행. 미디어 팀장은 media_brand_tone.md를 톤·금기 마스터로 반드시 선참조. (CHECKLIST 단계 0~2 완료)
- 2026-05-31 | Office 단계 4 완료 — trend-scout 10번째 캐릭터 + 미디어 회의실 5명(수련회 좌표 x+402 미러로 겹침 방지). runMediaHQ에 TREND_RE 결정적 보정(LLM이 trend-scout 누락해도 키워드 있으면 맨 앞 주입) → 트렌드 브리프를 다운스트림 팀장 컨텍스트로 주입. 교훈: LLM 라우팅은 결정적 가드와 병행해야 안정적. F5 시각 확인은 대표 OK로 통과.
- 2026-05-31 | 단계 3 execution 3종(mock) — media_common.py 공통화(slug·draft_dir·extract_json) 후 scout/reels/package 작성. 모든 스크립트에 --mock 플래그로 Claude 호출 없이 형식·폴더(9종) 검증. 교훈: 유료 API 스크립트는 mock 골격부터 만들어 폴더/파일 형식을 0원으로 확정한 뒤 실제 호출로 넘어가면 안전. 실제 호출 경로는 아직 미검증(대표 승인 시 1건만 소액 테스트 예정).
- 2026-05-31 | 단계 6 품질검사 + 5-4 텔레그램 연동. 미디어 3종 main에 친절 try-except(실패 시 트레이스백 대신 안내+exit). scout_trends에 notify_trends()로 trend_brief 요약 카드 텔레그램 발송(HTML escape·3500자 컷·실패 graceful). 교훈①: 발송류 단위테스트는 반드시 --no-telegram/mock으로 — 토큰 설정돼 있으면 진짜 발송됨(테스트 더미 1건 실발송 사고). 교훈②: 6-2(에이전트 정의 편집)는 자동 분류기가 범위 외로 차단 → 명시 승인 후 진행. 시스템 가드가 무단 self-modification을 막아준 정상 동작.
- 2026-05-31 | 단계 5 주간 트렌드 자동화 — com.hyds.weekly-trends.plist(월 09:45, daily-monitor 09:30과 분리) + data/trend_keywords.json. JSON은 주석 불가라 _안내 필드로 대신하고 로더가 객체{keywords:[]}·배열 둘 다 수용하도록 가드. README에 launchd 등록 가이드. 미연동: 텔레그램 발송(5-4)은 후속 — 현재는 .tmp 로컬 저장만이라 알림 없음에 주의.
- 2026-05-31 | reels 실호출 1차 실패 → self-anneal. 6개 섹션을 JSON 문자열 하나로 받게 했더니 max_tokens=4000 초과로 중간 잘림→JSON 파싱 전체 실패(fallback). 교훈: ①긴 멀티파일 LLM 출력은 JSON보다 '===FILE:파일명===' 마커 분할이 훨씬 안전(잘려도 완성 섹션 보존). ②max_tokens는 실콘텐츠 분량 기준으로 넉넉히(여기선 10000). 수정 후 reels 6종 정상·HYDS 톤·해시태그 30개 확인. mock 검증→소액 실호출 순서가 비용 사고 막아줌.
