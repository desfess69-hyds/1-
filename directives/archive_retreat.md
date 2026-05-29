# 수련회 아카이브 SOP (노션 자동 정리)

## 목표
종료된 수련회를 노션 DB에 자동으로 정리해 영구 자산화.
검색·재섭외·다음 기획 시 참고할 수 있도록.

## 트리거
- 자동: 매일 1회 (daily archive plist)
- 수동: `python execution/archive_to_notion.py`

## 흐름
1. 앱 DB에서 `status='done'` 수련회 조회
2. `data/notion_archive_state.json`의 archived_ids 와 비교 → 새로 올릴 것만 추리기
3. 각 건마다:
   - 체크리스트·보고서·파일 종합
   - Claude로 후기 4섹션 요약 생성 (잘된 점/아쉬운 점/교훈/재섭외 가치)
   - 노션 DB에 페이지 생성
4. 상태 파일 갱신

## 노션 DB 컬럼 (필수)
| 컬럼명 | 타입 |
|--------|------|
| 교회명 | Title |
| 주제 | Text |
| 기간 | Date (range) |
| 장소 | Text |
| 참가 인원 | Number |
| 최종 진척률 | Number |
| 팀장 | Text |
| 원본 ID | Number |
| 후기 요약 | Text |
| 파일/링크 | Text |

상세는 `NOTION_SETUP.md` 참고.

## 학습 기록
(첫 운영 후 채워질 예정)
