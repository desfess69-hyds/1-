import type { Agent } from '@/data/agents';
import { statusLabels } from '@/data/agents';

interface Props {
  agent: Agent;
  onClick?: () => void;
}

export function AgentCharacter({ agent, onClick }: Props) {
  const animClass = {
    idle: 'animate-bob',
    working: 'animate-shake',
    debating: 'animate-bob',
    thinking: 'animate-pulse-glow',
    moving: 'animate-bob',
  }[agent.status];

  const statusIcon = {
    idle: '💤',
    working: '⌨️',
    debating: '💬',
    thinking: '💡',
    moving: '👟',
  }[agent.status];

  // 입 모양 (상태별)
  const Mouth = () => {
    if (agent.status === 'debating') {
      return <rect x="22" y="20" width="8" height="3" rx="1" fill="#7c2d12" />;
    }
    if (agent.status === 'thinking') {
      return <rect x="24" y="21" width="4" height="2" rx="1" fill="#7c2d12" />;
    }
    // 미소 (idle / working / moving)
    return (
      <path d="M 21 20 Q 26 24 31 20" stroke="#7c2d12" strokeWidth="1.5" fill="none" strokeLinecap="round" />
    );
  };

  // 회의실에 있고(이동/작업 중) → 회의실 자리, 아니면 평상시 자리
  const useMeetingPos = agent.inMeeting && (agent.status === 'moving' || agent.status === 'working');
  const pos = useMeetingPos ? agent.meetingPosition : agent.position;
  const isChairing = agent.role === 'hyds-director' && agent.inMeeting;

  return (
    <div
      className="absolute cursor-pointer hover:scale-110"
      style={{ left: pos.x, top: pos.y, transition: 'left 1.2s ease, top 1.2s ease, transform 0.2s ease' }}
      onClick={onClick}
    >
      {/* 부장 회의 주관 배지 */}
      {isChairing && (
        <div className="absolute -top-2 -right-2 z-20 bg-amber-500 text-white text-[7px] korean px-1.5 py-0.5 rounded-full shadow whitespace-nowrap">🎙 주관</div>
      )}

      {/* 말풍선 */}
      {agent.message && (
        <div className="absolute -top-14 left-1/2 -translate-x-1/2 bg-white text-[#4a2c1a] text-[10px] korean px-3 py-2 rounded-xl shadow-lg max-w-[200px] z-10 border-2 border-amber-200">
          {agent.message}
          <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-3 h-3 bg-white rotate-45 border-r-2 border-b-2 border-amber-200"></div>
        </div>
      )}

      {/* chibi 캐릭터 */}
      <div className={animClass}>
        <svg width="56" height="64" viewBox="0 0 52 60" xmlns="http://www.w3.org/2000/svg" style={{ shapeRendering: 'crispEdges' }}>
          {/* 그림자 */}
          <ellipse cx="26" cy="58" rx="14" ry="2" fill="#000" opacity="0.15" />

          {/* 다리 */}
          <rect x="19" y="46" width="6" height="10" rx="2" fill={agent.hair} />
          <rect x="27" y="46" width="6" height="10" rx="2" fill={agent.hair} />
          {/* 신발 */}
          <ellipse cx="22" cy="56" rx="4" ry="2" fill="#4a2c1a" />
          <ellipse cx="30" cy="56" rx="4" ry="2" fill="#4a2c1a" />

          {/* 몸통 (작고 동그란) */}
          <rect x="16" y="32" width="20" height="18" rx="6" fill={agent.color} />
          {/* 옷 디테일 (브이넥 느낌) */}
          <path d="M 22 32 L 26 38 L 30 32" stroke={agent.hair} strokeWidth="1.5" fill="none" opacity="0.4" />

          {/* 팔 */}
          <ellipse cx="14" cy="40" rx="3" ry="5" fill={agent.color} />
          <ellipse cx="38" cy="40" rx="3" ry="5" fill={agent.color} />

          {/* 머리 (크게 — chibi 비율) */}
          <ellipse cx="26" cy="18" rx="14" ry="14" fill={agent.color} />

          {/* 머리카락 (앞머리) */}
          <path d="M 12 14 Q 18 6 26 6 Q 34 6 40 14 Q 38 10 26 10 Q 14 10 12 14 Z" fill={agent.hair} />
          <ellipse cx="26" cy="9" rx="13" ry="5" fill={agent.hair} />

          {/* 양 볼 분홍 (chubby) */}
          <ellipse cx="17" cy="22" rx="2.5" ry="1.8" fill="#fda4af" opacity="0.7" />
          <ellipse cx="35" cy="22" rx="2.5" ry="1.8" fill="#fda4af" opacity="0.7" />

          {/* 눈 (큰 동그란) */}
          <g className="animate-blink" style={{ transformOrigin: '20px 17px' }}>
            <ellipse cx="20" cy="17" rx="2.5" ry="3" fill="#3a1f0a" />
            <circle cx="20.5" cy="16" r="0.8" fill="white" />
          </g>
          <g className="animate-blink" style={{ transformOrigin: '32px 17px' }}>
            <ellipse cx="32" cy="17" rx="2.5" ry="3" fill="#3a1f0a" />
            <circle cx="32.5" cy="16" r="0.8" fill="white" />
          </g>

          {/* 입 */}
          <Mouth />

          {/* working 상태일 때 키보드 효과 */}
          {agent.status === 'working' && (
            <>
              <rect x="44" y="42" width="2" height="1" fill="#4a2c1a" opacity="0.6" />
              <rect x="46" y="40" width="2" height="1" fill="#4a2c1a" opacity="0.6" />
            </>
          )}
        </svg>
      </div>

      {/* 이름표 */}
      <div className="absolute -bottom-10 left-1/2 -translate-x-1/2 text-center whitespace-nowrap">
        <div className="text-[9px] text-[#4a2c1a] bg-amber-100/90 px-2 py-0.5 rounded-full korean font-bold shadow-sm border border-amber-200">
          {agent.name}
        </div>
        <div className="text-[8px] text-amber-800 mt-1 korean">
          {statusIcon} {statusLabels[agent.status]}
        </div>
      </div>
    </div>
  );
}
