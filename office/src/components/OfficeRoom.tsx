import { AgentCharacter } from './AgentCharacter';
import type { Agent } from '@/data/agents';

interface Props {
  agents: Agent[];
  onAgentClick: (id: string) => void;
  meetingActive?: boolean;
  agenda?: string;
}

export function OfficeRoom({ agents, onAgentClick, meetingActive = false, agenda = '' }: Props) {
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
      <div className="absolute top-[42%] left-[28%] w-1/3 h-1/2 bg-orange-200/30 rounded-3xl border-2 border-orange-300/40"></div>

      {/* ── 회의실 (워룸) ─────────────────────────────────────── */}
      {/* 회의 중 따뜻한 빛 글로우 (박스 뒤) */}
      {meetingActive && (
        <div
          className="absolute pointer-events-none rounded-full bg-yellow-200/50 blur-3xl animate-pulse"
          style={{ left: 580, top: 320, width: 180, height: 200 }}
        />
      )}

      {/* 회의실 박스 (점선 테두리) */}
      <div
        className="absolute rounded-2xl border-2 border-dashed transition-all duration-700"
        style={{
          left: 540, top: 226, width: 240, height: 356,
          borderColor: meetingActive ? '#f59e0b' : 'rgba(139,90,60,0.45)',
          background: meetingActive ? 'rgba(254,243,199,0.45)' : 'rgba(255,255,255,0.10)',
          boxShadow: meetingActive
            ? 'inset 0 0 36px 6px rgba(251,191,36,0.40), 0 0 22px 4px rgba(251,191,36,0.30)'
            : 'none',
        }}
      >
        <div className="absolute -top-3 left-3 bg-office-trim text-yellow-100 text-[10px] korean px-2 py-0.5 rounded-full shadow whitespace-nowrap">
          📊 회의실
        </div>
      </div>

      {/* 화이트보드 (회의실 상단) */}
      <div
        className="absolute bg-white border-2 border-office-trim rounded shadow-md overflow-hidden flex flex-col"
        style={{ left: 556, top: 242, width: 208, height: 40 }}
      >
        <div className="text-[7px] text-amber-700 korean px-1 leading-none pt-0.5 border-b border-amber-200/70">📋 안건</div>
        <div className={`text-[8px] korean px-1 leading-tight flex-1 flex items-center ${agenda.startsWith('✅') ? 'text-emerald-600 font-bold' : 'text-[#4a2c1a]'}`}>
          {meetingActive ? (agenda || '회의 준비 중...') : '—'}
        </div>
      </div>

      {/* 회의 테이블 (우드 직사각형) */}
      <div
        className="absolute bg-office-trim rounded-xl shadow-lg"
        style={{ left: 600, top: 358, width: 112, height: 94 }}
      >
        <div className="absolute inset-1.5 rounded-lg border border-amber-300/30"></div>
      </div>

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
