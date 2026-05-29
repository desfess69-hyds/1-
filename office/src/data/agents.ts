export type AgentStatus = 'idle' | 'working' | 'debating' | 'thinking' | 'moving';

export interface Agent {
  id: string;
  name: string;
  role: string;
  color: string;       // sprite 색
  position: { x: number; y: number };
  status: AgentStatus;
  message?: string;
  trigger?: string;    // 자동화로 깨우는 트리거 키
}

export const initialAgents: Agent[] = [
  {
    id: 'retreat-planner',
    name: '기획자',
    role: 'retreat-planner',
    color: '#fbbf24', // amber
    position: { x: 120, y: 200 },
    status: 'idle',
    trigger: 'manual',
  },
  {
    id: 'retreat-monitor',
    name: '모니터',
    role: 'retreat-monitor',
    color: '#f87171', // red
    position: { x: 320, y: 200 },
    status: 'idle',
    trigger: 'daily-monitor',
  },
  {
    id: 'report-summarizer',
    name: '리포터',
    role: 'report-summarizer',
    color: '#34d399', // emerald
    position: { x: 520, y: 200 },
    status: 'idle',
    trigger: 'manual',
  },
  {
    id: 'content-creator',
    name: '크리에이터',
    role: 'content-creator',
    color: '#a78bfa', // violet
    position: { x: 220, y: 380 },
    status: 'idle',
    trigger: 'manual',
  },
  {
    id: 'church-communicator',
    name: '커뮤니케이터',
    role: 'church-communicator',
    color: '#60a5fa', // blue
    position: { x: 420, y: 380 },
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
