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

  return (
    <div
      className="absolute cursor-pointer transition-transform hover:scale-110"
      style={{ left: agent.position.x, top: agent.position.y }}
      onClick={onClick}
    >
      {/* 말풍선 */}
      {agent.message && (
        <div className="absolute -top-12 left-1/2 -translate-x-1/2 bg-white text-black text-xs korean px-2 py-1 rounded shadow-lg max-w-[180px] z-10">
          {agent.message}
          <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-white rotate-45"></div>
        </div>
      )}

      {/* 픽셀 캐릭터 (단순 SVG) */}
      <div className={animClass}>
        <svg width="48" height="64" viewBox="0 0 48 64" xmlns="http://www.w3.org/2000/svg" style={{ shapeRendering: 'crispEdges' }}>
          {/* 머리 */}
          <rect x="14" y="2" width="20" height="20" fill={agent.color} />
          <rect x="14" y="2" width="20" height="4" fill="#1a1a2e" />
          {/* 눈 */}
          <rect x="18" y="10" width="3" height="3" fill="#1a1a2e" />
          <rect x="27" y="10" width="3" height="3" fill="#1a1a2e" />
          {/* 입 */}
          {agent.status === 'debating' ? (
            <rect x="20" y="16" width="8" height="3" fill="#1a1a2e" />
          ) : (
            <rect x="21" y="17" width="6" height="2" fill="#1a1a2e" />
          )}
          {/* 몸통 */}
          <rect x="12" y="22" width="24" height="22" fill={agent.color} />
          <rect x="12" y="22" width="24" height="4" fill="#1a1a2e" opacity="0.3" />
          {/* 다리 */}
          <rect x="14" y="44" width="8" height="14" fill="#1a1a2e" />
          <rect x="26" y="44" width="8" height="14" fill="#1a1a2e" />
          {/* 신발 */}
          <rect x="14" y="58" width="10" height="4" fill="#000" />
          <rect x="24" y="58" width="10" height="4" fill="#000" />
        </svg>
      </div>

      {/* 이름표 */}
      <div className="absolute -bottom-10 left-1/2 -translate-x-1/2 text-center whitespace-nowrap">
        <div className="text-[8px] text-white bg-black/60 px-2 py-0.5 rounded korean">{agent.name}</div>
        <div className="text-[7px] text-yellow-300 mt-0.5">{statusIcon} <span className="korean">{statusLabels[agent.status]}</span></div>
      </div>
    </div>
  );
}
