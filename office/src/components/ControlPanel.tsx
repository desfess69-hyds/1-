interface Props {
  onTrigger: (action: string) => void;
}

export function ControlPanel({ onTrigger }: Props) {
  const buttons = [
    { id: 'daily-monitor', label: '🌅 매일 모니터', desc: 'retreat-monitor 깨우기', color: 'from-amber-100 to-amber-200' },
    { id: 'realtime', label: '⚡ 실시간 체크', desc: '5분 주기 체크', color: 'from-rose-100 to-rose-200' },
    { id: 'weekly-todos', label: '📋 주간 To-Do', desc: '월요일 09:30', color: 'from-emerald-100 to-emerald-200' },
    { id: 'debate', label: '💬 토론 시뮬', desc: '미디어팀 톤 회의', color: 'from-violet-100 to-violet-200' },
    { id: 'card-news', label: '🎨 카드뉴스', desc: 'media-producer 작업', color: 'from-pink-100 to-pink-200' },
    { id: 'reset', label: '🔄 리셋', desc: '전원 idle 복귀', color: 'from-gray-100 to-gray-200' },
  ];

  return (
    <div className="bg-white/60 backdrop-blur-sm border-2 border-amber-200 rounded-2xl p-4 shadow-md">
      <div className="text-amber-900 text-sm mb-3 korean font-bold flex items-center gap-2">
        <span>🎮</span> 컨트롤 패널
      </div>
      <div className="grid grid-cols-3 gap-3">
        {buttons.map(b => (
          <button
            key={b.id}
            onClick={() => onTrigger(b.id)}
            className={`bg-gradient-to-br ${b.color} hover:scale-105 active:scale-95 transition-all p-3 rounded-xl border border-white/80 text-left shadow-sm hover:shadow-md`}
          >
            <div className="text-sm text-amber-900 korean font-semibold">{b.label}</div>
            <div className="text-[10px] text-amber-700 korean mt-1">{b.desc}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
