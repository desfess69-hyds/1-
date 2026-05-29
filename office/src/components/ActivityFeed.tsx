import { useEffect, useRef } from 'react';

export interface Activity {
  id: string;
  agentName: string;
  message: string;
  ts: number;
  type: 'info' | 'work' | 'alert';
}

interface Props {
  items: Activity[];
}

export function ActivityFeed({ items }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: 0, behavior: 'smooth' });
  }, [items]);

  const styleFor = (t: Activity['type']) => ({
    info: 'border-sky-300 bg-sky-50/70',
    work: 'border-amber-300 bg-amber-50/70',
    alert: 'border-rose-400 bg-rose-50/70 animate-pulse',
  }[t]);

  const dotFor = (t: Activity['type']) => ({
    info: 'bg-sky-500',
    work: 'bg-amber-500',
    alert: 'bg-rose-500',
  }[t]);

  return (
    <div className="bg-white/60 backdrop-blur-sm border-2 border-amber-200 rounded-2xl p-4 h-[680px] overflow-hidden shadow-md">
      <div className="text-amber-900 text-sm mb-3 korean font-bold flex items-center gap-2">
        <span>📡</span> 실시간 활동 로그
      </div>
      <div ref={scrollRef} className="h-[600px] overflow-y-auto space-y-2 pr-2">
        {items.length === 0 ? (
          <div className="text-amber-700/60 text-xs korean text-center mt-8">아직 활동 없음...</div>
        ) : (
          items.map(item => (
            <div key={item.id} className={`border-l-4 ${styleFor(item.type)} pl-3 py-2 rounded-r-lg`}>
              <div className="flex items-center gap-1.5 text-[10px] text-amber-700/70 korean">
                <span className={`w-1.5 h-1.5 rounded-full ${dotFor(item.type)}`}></span>
                {new Date(item.ts).toLocaleTimeString('ko-KR')}
              </div>
              <div className="text-xs text-amber-900 korean font-bold mt-0.5">{item.agentName}</div>
              <div className="text-xs text-amber-800 korean leading-tight mt-1">{item.message}</div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
