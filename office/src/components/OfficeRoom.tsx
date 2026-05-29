import { AgentCharacter } from './AgentCharacter';
import type { Agent } from '@/data/agents';

interface Props {
  agents: Agent[];
  onAgentClick: (id: string) => void;
}

export function OfficeRoom({ agents, onAgentClick }: Props) {
  return (
    <div className="relative w-full h-[600px] bg-office-floor border-4 border-office-trim rounded-2xl overflow-hidden shadow-2xl">
      {/* 나무 바닥 무늬 */}
      <div
        className="absolute inset-0"
        style={{
          backgroundImage: 'repeating-linear-gradient(90deg, transparent, transparent 80px, rgba(139, 90, 60, 0.15) 80px, rgba(139, 90, 60, 0.15) 82px)',
        }}
      />

      {/* 벽 (위쪽 35%) */}
      <div className="absolute top-0 left-0 right-0 h-[35%] bg-office-wall">
        {/* 벽지 무늬 (작은 점) */}
        <div
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage: 'radial-gradient(circle, #b45309 1px, transparent 1px)',
            backgroundSize: '20px 20px',
          }}
        />

        {/* 창문 — 햇살 들어오는 */}
        <div className="absolute top-6 left-10 w-32 h-20 bg-gradient-to-b from-sky-200 to-sky-100 border-4 border-office-trim rounded-md shadow-inner">
          {/* 창문 격자 */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-full h-0.5 bg-office-trim"></div>
          </div>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-0.5 h-full bg-office-trim"></div>
          </div>
          {/* 구름 */}
          <div className="absolute top-3 left-3 w-6 h-2 bg-white rounded-full opacity-80"></div>
          <div className="absolute top-2 left-10 w-4 h-2 bg-white rounded-full opacity-70"></div>
          {/* 햇살 (창문 밖으로 흘러나오는 노란 빛) */}
          <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-32 h-32 bg-yellow-200 opacity-30 rounded-full blur-2xl"></div>
        </div>

        {/* 천장 조명 (펜던트) */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 flex flex-col items-center">
          <div className="w-0.5 h-6 bg-office-trim"></div>
          <div className="w-10 h-6 bg-yellow-300 rounded-b-full shadow-lg animate-pulse"></div>
          <div className="w-20 h-20 bg-yellow-100 opacity-30 rounded-full blur-xl -mt-4"></div>
        </div>

        {/* 사인보드 */}
        <div className="absolute top-4 right-6 bg-office-trim text-yellow-100 px-3 py-1 rounded korean text-[10px] shadow-md">
          🏢 HYDS OFFICE
        </div>

        {/* 액자 */}
        <div className="absolute top-12 right-1/3 w-12 h-10 bg-amber-100 border-2 border-office-trim rounded shadow-sm flex items-center justify-center text-[8px] text-amber-700 korean">
          ❤️
        </div>

        {/* 화분 */}
        <div className="absolute bottom-0 right-4 flex flex-col items-center">
          <div className="w-6 h-8 bg-green-600 rounded-full animate-sway origin-bottom">
            <div className="w-3 h-3 bg-green-400 rounded-full mt-1 ml-1"></div>
          </div>
          <div className="w-7 h-3 bg-orange-300 rounded-b-md border-2 border-orange-500"></div>
        </div>
      </div>

      {/* 카펫 (중앙) */}
      <div className="absolute top-[42%] left-1/2 -translate-x-1/2 w-2/3 h-1/2 bg-orange-200/30 rounded-3xl border-2 border-orange-300/40"></div>

      {/* 책상들 (캐릭터 아래) */}
      {agents.map(a => (
        <div key={`desk-${a.id}`}>
          <div
            className="absolute w-20 h-3 bg-office-trim rounded-sm shadow-md"
            style={{ left: a.position.x - 10, top: a.position.y + 70 }}
          />
          <div
            className="absolute w-3 h-8 bg-office-trim"
            style={{ left: a.position.x - 8, top: a.position.y + 72 }}
          />
          <div
            className="absolute w-3 h-8 bg-office-trim"
            style={{ left: a.position.x + 26, top: a.position.y + 72 }}
          />
        </div>
      ))}

      {/* 모니터 (캐릭터 옆 책상 위) */}
      {agents.map(a => (
        <div
          key={`pc-${a.id}`}
          className="absolute"
          style={{ left: a.position.x + 52, top: a.position.y + 35 }}
        >
          {/* 모니터 화면 */}
          <div className={`w-8 h-7 ${a.status === 'working' ? 'bg-green-300' : 'bg-sky-200'} border-2 border-office-trim rounded`}>
            {a.status === 'working' && (
              <div className="text-[6px] text-green-900 font-mono p-0.5">
                {'>'}{'_'}
              </div>
            )}
          </div>
          {/* 받침대 */}
          <div className="w-2 h-2 bg-office-trim mx-auto"></div>
          <div className="w-6 h-1 bg-office-trim mx-auto rounded-b"></div>
        </div>
      ))}

      {/* 머그컵 (책상 위) */}
      {agents.map(a => (
        <div
          key={`mug-${a.id}`}
          className="absolute w-3 h-4 bg-white border-2 border-amber-700 rounded-b-md"
          style={{ left: a.position.x - 6, top: a.position.y + 62 }}
        >
          {/* 손잡이 */}
          <div className="absolute -right-1 top-0.5 w-1.5 h-2 border-2 border-amber-700 rounded-full"></div>
          {/* 김 */}
          <div className="absolute -top-1 left-1 text-[6px] opacity-60">☕</div>
        </div>
      ))}

      {/* 캐릭터들 */}
      {agents.map(a => (
        <AgentCharacter key={a.id} agent={a} onClick={() => onAgentClick(a.id)} />
      ))}
    </div>
  );
}
