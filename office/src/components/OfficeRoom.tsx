import { AgentCharacter } from './AgentCharacter';
import type { Agent } from '@/data/agents';

interface Props {
  agents: Agent[];
  onAgentClick: (id: string) => void;
}

export function OfficeRoom({ agents, onAgentClick }: Props) {
  return (
    <div className="relative w-full h-[600px] bg-office-floor border-4 border-office-wall rounded-lg overflow-hidden shadow-2xl">
      {/* 벽 */}
      <div className="absolute top-0 left-0 right-0 h-24 bg-office-wall">
        <div className="absolute top-4 left-8 w-16 h-12 bg-yellow-200/20 border-2 border-yellow-200/40 rounded"></div>
        <div className="absolute top-4 right-8 text-yellow-200/60 text-[10px] korean p-2">
          HYDS OFFICE
        </div>
        <div className="absolute top-8 left-1/2 -translate-x-1/2 w-12 h-12 rounded-full bg-yellow-100/30 animate-pulse"></div>
      </div>

      {/* 책상들 (캐릭터 아래) */}
      {agents.map(a => (
        <div
          key={`desk-${a.id}`}
          className="absolute w-16 h-4 bg-amber-900 rounded"
          style={{ left: a.position.x - 8, top: a.position.y + 70 }}
        />
      ))}

      {/* 컴퓨터 (캐릭터 옆) */}
      {agents.map(a => (
        <div
          key={`pc-${a.id}`}
          className="absolute w-6 h-5 bg-gray-700 border border-gray-500 rounded-sm flex items-center justify-center"
          style={{ left: a.position.x + 50, top: a.position.y + 40 }}
        >
          <div className={`w-4 h-3 ${a.status === 'working' ? 'bg-green-400' : 'bg-blue-900'} rounded-sm`}></div>
        </div>
      ))}

      {/* 캐릭터들 */}
      {agents.map(a => (
        <AgentCharacter key={a.id} agent={a} onClick={() => onAgentClick(a.id)} />
      ))}
    </div>
  );
}
