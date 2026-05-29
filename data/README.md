# data/

영구 데이터 — 강사·장소·이력. JSON으로 저장.

## speakers.json 예시

```json
[
  {
    "id": "spk_001",
    "name": "홍길동 목사",
    "specialty": ["청년부", "기도", "치유"],
    "fee_per_session": 300000,
    "phone": "010-XXXX-XXXX",
    "notes": "2025년 ○○교회 수련회 호평. 청년 눈높이 메시지 강점."
  }
]
```

## venues.json 예시

```json
[
  {
    "id": "ven_001",
    "name": "한마음수양관",
    "location": "경기도 양평",
    "capacity": 80,
    "price_per_night": 35000,
    "facilities": ["대강당", "식당", "운동장"],
    "notes": "조용함. 와이파이 약함."
  }
]
```

## 채우는 법

1. 직접 알고 있는 강사·장소부터 한 명/한 곳씩 입력
2. 수련회 끝날 때마다 → `notes`에 후기 한 줄 추가
3. 점수 매기지 않음 — 솔직한 메모로 충분
