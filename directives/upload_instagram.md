# 인스타그램 업로드 SOP

## 목표
완성된 카드뉴스를 HYDS 인스타 비즈니스 계정에 게시한다.

## 전제 조건 (Phase 3에서 셋업)
- 인스타 **비즈니스 계정** (개인 계정 불가)
- 페이스북 페이지 연동
- Instagram Graph API 액세스 토큰 (`IG_ACCESS_TOKEN`)
- 사용자 ID (`IG_USER_ID`)

## 입력
- 카드뉴스 폴더 (`.tmp/card_drafts/{...}/`)
- 게시 일정 (즉시 / 예약)

## 사용할 도구
- `execution/upload_to_ig.py`
- Instagram Graph API (`graph.facebook.com/v18.0/`)

## 절차
1. 폴더 안 PNG 파일들을 공개 URL로 업로드 (Cloudinary, S3 등 — 임시는 imgbb 가능)
2. `media_type=CAROUSEL` 컨테이너 생성
3. 각 이미지 자식 컨테이너 만들어 attach
4. 캡션·해시태그 합쳐 publish

## 출력
- 업로드된 게시물의 인스타그램 URL
- `data/posts.json`에 로그 추가

## 엣지 케이스
- API 토큰 만료 → 즉시 사용자에게 알림 (수동 재발급 필요)
- 슬라이드 11장 이상 → API 한도 초과, 10장 이내로 줄이기
- 해시태그 30개 초과 → 자동 컷

## 임시 우회 (Phase 3 전까지)
인스타 비즈니스 계정 셋업 전에는 → 폴더의 PNG들을 사용자가 **수동 업로드**.
스크립트는 PNG와 캡션까지만 만들면 됨.

## 학습 기록
(첫 운영 후 채워질 예정)
