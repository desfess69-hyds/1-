export type AgentStatus = 'idle' | 'working' | 'debating' | 'thinking' | 'moving';

export interface Agent {
  id: string;
  name: string;
  role: string;
  color: string;      // 몸통 색
  hair: string;       // 머리/모자 색
  position: { x: number; y: number };          // 평상시 자기 자리
  meetingPosition: { x: number; y: number };   // 회의실 테이블 자리
  status: AgentStatus;
  message?: string;
  trigger?: string;
  inMeeting?: boolean;                          // 회의실에 있는가
}

export const initialAgents: Agent[] = [
  {
    id: 'retreat-planner',
    name: '기획자',
    role: 'retreat-planner',
    color: '#fde68a',  // 부드러운 살구
    hair: '#b45309',
    position: { x: 110, y: 190 },
    meetingPosition: { x: 560, y: 340 },   // 테이블 좌상
    status: 'idle',
    trigger: 'manual',
  },
  {
    id: 'retreat-monitor',
    name: '모니터',
    role: 'retreat-monitor',
    color: '#fecaca',  // 산호
    hair: '#b91c1c',
    position: { x: 300, y: 190 },
    meetingPosition: { x: 700, y: 340 },   // 테이블 우상
    status: 'idle',
    trigger: 'daily-monitor',
  },
  {
    id: 'report-summarizer',
    name: '리포터',
    role: 'report-summarizer',
    color: '#bbf7d0',  // 민트
    hair: '#15803d',
    position: { x: 490, y: 190 },
    meetingPosition: { x: 560, y: 432 },   // 테이블 좌하
    status: 'idle',
    trigger: 'manual',
  },
  {
    id: 'content-creator',
    name: '크리에이터',
    role: 'content-creator',
    color: '#ddd6fe',  // 라일락
    hair: '#6d28d9',
    position: { x: 110, y: 380 },
    meetingPosition: { x: 700, y: 432 },   // 테이블 우하
    status: 'idle',
    trigger: 'manual',
  },
  {
    id: 'hyds-director',
    name: '부장',
    role: 'hyds-director',
    color: '#fcd34d',  // 금색 (총괄)
    hair: '#78350f',
    position: { x: 300, y: 380 },
    meetingPosition: { x: 630, y: 285 },   // 테이블 상석 (회의 주관)
    status: 'idle',
    trigger: 'manual',
  },
  {
    id: 'church-communicator',
    name: '커뮤니케이터',
    role: 'church-communicator',
    color: '#bfdbfe',  // 하늘
    hair: '#1e40af',
    position: { x: 490, y: 380 },
    meetingPosition: { x: 630, y: 487 },   // 테이블 하석
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
