# Git + GitHub 백업 가이드

본인 Mac 터미널에서 한 번만 실행하면 평생 안전.

---

## ✅ Step 1 — 기존 잔여 .git 폴더 제거 (30초)

```bash
cd ~/Desktop/코딩/1인\ 회사\ 만들기
rm -rf .git
```

(이전 시도에서 만들어진 .git 폴더가 있어서 깨끗이 정리)

---

## ✅ Step 2 — Git 초기화 + 첫 커밋 (2분)

```bash
# 1. 초기화 (브랜치 이름 main)
git init -b main

# 2. 본인 정보 등록 (이 저장소에만 적용)
git config user.name "서동현"
git config user.email "desfess69@gmail.com"

# 3. ⚠️ 보안 점검 — .env가 안 보여야 함!
git status

# 4. 다 추가하고 커밋
git add .
git commit -m "HYDS: initial setup — 3-Layer architecture, retreat planner + card news skeleton"
```

### 🔒 보안 체크 (꼭 확인)

`git status` 했을 때 다음이 보이면 OK:
```
On branch main
Untracked files:
  .env.example          ← 이건 OK (예시 파일)
  .gitignore
  AGENTS.md
  CLAUDE.md
  ...
```

다음이 보이면 **위험!** 중단:
```
  .env                  ← ❌ 절대 안 됨
  venv/                 ← ❌ 절대 안 됨
```

→ 위험 케이스가 보이면 `.gitignore` 확인 후 다시 시도.

---

## ✅ Step 3 — GitHub 저장소 만들기 (3분)

### 3-1. GitHub에서 새 저장소 생성

1. https://github.com 로그인
2. 우측 상단 `+` → `New repository`
3. 입력:
   - **Repository name**: `HYDS` (또는 원하는 이름)
   - **Description**: `1인 AI 회사 — 수련회 기획·점검 + 카드뉴스 제작`
   - **Visibility**: 🔒 **Private** 강력 추천 (Public 하면 내부 데이터 공개됨)
   - ❌ `Add a README file` 체크 해제 (이미 있음)
   - ❌ `Add .gitignore` 체크 해제 (이미 있음)
4. `Create repository`

→ 생성 후 페이지에 나오는 URL 복사. 둘 중 하나:
- HTTPS: `https://github.com/사용자명/HYDS.git`
- SSH: `git@github.com:사용자명/HYDS.git`

### 3-2. 로컬과 연결 + 푸시

```bash
# 위에서 복사한 URL 붙여넣기
git remote add origin https://github.com/본인사용자명/HYDS.git

# 푸시
git push -u origin main
```

처음 push할 때 GitHub 인증 창이 뜸:
- **macOS**: 키체인 자동 처리되거나 GitHub Personal Access Token 입력
- 비밀번호 인증은 2021년 폐지됨 → **Personal Access Token** 필요

### 3-3. Personal Access Token 발급 (필요시)

1. https://github.com/settings/tokens
2. `Generate new token (classic)`
3. Note: `HYDS-local`
4. Expiration: `90 days` (또는 No expiration)
5. Scopes: ✅ `repo` 만 체크
6. `Generate token` → **복사 (한 번만 보여줌!)**
7. `git push` 시 비밀번호 자리에 이 토큰 붙여넣기

---

## ✅ Step 4 — 검증

```bash
# 원격에 잘 올라갔는지
git log --oneline
git remote -v
```

GitHub 페이지 새로고침 → 파일들이 보이면 성공.

⚠️ GitHub에서 `.env` 파일이 *안 보여야* 정상!

---

## 일상 사용 (앞으로)

뭔가 바꿀 때마다:
```bash
git add .
git commit -m "한국어로 뭐 바꿨는지 한 줄"
git push
```

---

## 막힐 때

다음 메시지에:
- 어느 Step에서 막혔는지
- 에러 메시지 통째로
- `git status` 결과
