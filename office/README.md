# HYDS Office

5명의 AI 에이전트가 픽셀 사무실에서 일하는 비주얼 대시보드.

## 실행

```bash
npm run dev
```

→ http://localhost:5173

## 구조

- React 18 + TypeScript + Vite + Tailwind CSS
- 의존성 라이브러리 거의 없음 (의도적으로 순수 React)
- SVG로 픽셀 캐릭터 직접 렌더링

## 다음 단계 아이디어

- HYDS Python 자동화 로그(`../data/monitor_log.json`) 실시간 fetch
- Claude API 진짜 호출해서 debate 모드 동적 생성
- 사무실에 가구 추가 (소파, 화이트보드, 커피머신)
- 에이전트가 책상 사이로 이동하는 walk 애니메이션
