interface Props {
  onTrigger: (action: string) => void;
}

export function ControlPanel({ onTrigger }: Props) {
  const buttons = [
    { id: 'daily-monitor', label: '🌅 매일 모니터', desc: 'retreat-monitor 깨우기' },
    { id: 'realtime', label: '⚡ 실시간 체크', desc: 'realtime checker 5분 주기' },
    { id: 'weekly-todos', label: '📋 주간 To-Do', desc: '월요일 09:30' },
    { id: 'debate', label: '💬 토론 시뮬', desc: '두 명이 대화' },
    { id: 'card-news', label: '🎨 카드뉴스', desc: 'content-creator 작업' },
    { id: 'reset', label: '🔄 리셋', desc: '전원 idle 복귀' },
  ];

  return (
    <div className="bg-black/40 border-2 border-office-wall rounded-lg p-4">
      <div className="text-yellow-200 text-[10px] mb-3 korean">🎮 컨트롤 패널</div>
      <div className="grid grid-cols-3 gap-2">
        {buttons.map(b => (
          <button
            key={b.id}
            onClick={() => onTrigger(b.id)}
            className="bg-office-wall hover:bg-blue-900 transition-colors p-2 rounded border border-gray-600 text-left"
          >
            <div className="text-[10px] text-yellow-200 korean">{b.label}</div>
            <div className="text-[8px] text-gray-400 korean mt-1">{b.desc}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
