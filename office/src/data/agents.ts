export type AgentStatus = 'idle' | 'working' | 'debating' | 'thinking' | 'moving';

// 어느 본부 소속인가 (회의실 배정 기준)
//  - exec   : 부장 (수련회 회의실을 직접 주관)
//  - retreat: 수련회 본부 팀장 (부장이 직접 관리)
//  - media  : 미디어 본부 (본부장 media-director + 팀장 3명)
export type Hq = 'exec' | 'retreat' | 'media';
export type RoomId = 'retreat' | 'media';

export interface Agent {
  id: string;
  name: string;
  role: string;
  color: string;      // 몸통 색
  hair: string;       // 머리/모자 색
  hq: Hq;             // 소속 본부
  room: RoomId;       // 회의 시 들어가는 회의실
  isChair?: boolean;  // 그 회의실의 주관자(부장/본부장)
  position: { x: number; y: number };          // 평상시 자기 자리
  meetingPosition: { x: number; y: number };   // 회의실 테이블 자리
  status: AgentStatus;
  message?: string;
  trigger?: string;
  inMeeting?: boolean;                          // 회의실에 있는가
}

// ── 회의실 두 곳 (수련회 / 미디어) 영역 정의 — OfficeRoom 렌더 + 시뮬레이션 공유 ──
export interface MeetingRoom {
  id: RoomId;
  label: string;
  box: { left: number; top: number; width: number; height: number };
  board: { left: number; top: number; width: number; height: number };
  table: { left: number; top: number; width: number; height: number };
  glow: { left: number; top: number; width: number; height: number };
}

export const MEETING_ROOMS: MeetingRoom[] = [
  {
    id: 'retreat',
    label: '🏕 수련회 회의실',
    box: { left: 18, top: 440, width: 384, height: 232 },
    board: { left: 36, top: 456, width: 200, height: 38 },
    table: { left: 150, top: 548, width: 104, height: 74 },
    glow: { left: 120, top: 500, width: 170, height: 190 },
  },
  {
    id: 'media',
    label: '🎬 미디어 회의실',
    box: { left: 418, top: 440, width: 384, height: 232 },
    board: { left: 436, top: 456, width: 200, height: 38 },
    table: { left: 552, top: 548, width: 104, height: 74 },
    glow: { left: 525, top: 500, width: 170, height: 190 },
  },
];

export const initialAgents: Agent[] = [
  // ── 부장 (총괄) — 평상시 윗줄 우측, 회의 시 수련회 회의실 상석 ──
  {
    id: 'hyds-director',
    name: '부장',
    role: 'hyds-director',
    color: '#fcd34d',  // 금색 (총괄)
    hair: '#78350f',
    hq: 'exec',
    room: 'retreat',
    isChair: true,
    position: { x: 535, y: 205 },
    meetingPosition: { x: 176, y: 460 },   // 수련회 회의실 상석
    status: 'idle',
    trigger: 'manual',
  },

  // ── 수련회 본부 (부장 직접 관리) — 윗줄 ──
  {
    id: 'retreat-planner',
    name: '기획자',
    role: 'retreat-planner',
    color: '#fde68a',  // 부드러운 살구
    hair: '#b45309',
    hq: 'retreat',
    room: 'retreat',
    position: { x: 35, y: 205 },
    meetingPosition: { x: 90, y: 538 },
    status: 'idle',
    trigger: 'manual',
  },
  {
    id: 'retreat-monitor',
    name: '모니터',
    role: 'retreat-monitor',
    color: '#fecaca',  // 산호
    hair: '#b91c1c',
    hq: 'retreat',
    room: 'retreat',
    position: { x: 160, y: 205 },
    meetingPosition: { x: 268, y: 538 },
    status: 'idle',
    trigger: 'daily-monitor',
  },
  {
    id: 'report-summarizer',
    name: '리포터',
    role: 'report-summarizer',
    color: '#bbf7d0',  // 민트
    hair: '#15803d',
    hq: 'retreat',
    room: 'retreat',
    position: { x: 285, y: 205 },
    meetingPosition: { x: 90, y: 604 },
    status: 'idle',
    trigger: 'manual',
  },
  {
    id: 'church-communicator',
    name: '커뮤니케이터',
    role: 'church-communicator',
    color: '#bfdbfe',  // 하늘
    hair: '#1e40af',
    hq: 'retreat',
    room: 'retreat',
    position: { x: 410, y: 205 },
    meetingPosition: { x: 268, y: 604 },
    status: 'idle',
    trigger: 'manual',
  },

  // ── 미디어 본부 — 아랫줄 ──
  {
    id: 'media-director',
    name: '미디어본부장',
    role: 'media-director',
    color: '#c4b5fd',  // 보라 (본부장)
    hair: '#6d28d9',
    hq: 'media',
    room: 'media',
    isChair: true,
    position: { x: 35, y: 350 },
    meetingPosition: { x: 580, y: 460 },   // 미디어 회의실 상석
    status: 'idle',
    trigger: 'manual',
  },
  {
    id: 'concept-planner',
    name: '컨셉기획',
    role: 'concept-planner',
    color: '#99f6e4',  // 청록
    hair: '#0f766e',
    hq: 'media',
    room: 'media',
    position: { x: 160, y: 350 },
    meetingPosition: { x: 494, y: 540 },
    status: 'idle',
    trigger: 'manual',
  },
  {
    id: 'scriptwriter',
    name: '카피라이터',
    role: 'scriptwriter',
    color: '#fbcfe8',  // 분홍
    hair: '#be185d',
    hq: 'media',
    room: 'media',
    position: { x: 285, y: 350 },
    meetingPosition: { x: 666, y: 540 },
    status: 'idle',
    trigger: 'manual',
  },
  {
    id: 'media-producer',
    name: '제작자',
    role: 'media-producer',
    color: '#fdba74',  // 주황
    hair: '#c2410c',
    hq: 'media',
    room: 'media',
    position: { x: 410, y: 350 },
    meetingPosition: { x: 580, y: 606 },
    status: 'idle',
    trigger: 'manual',
  },
];

export const statusLabels: Record<AgentStatus, string> = {
  idle: '대기 중',
  working: '작업 중',
  debating: '토론 중',
  thinking: '생각 중',
  moving: '이동 중',
};
