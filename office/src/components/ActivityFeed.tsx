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

  const colorFor = (t: Activity['type']) => ({
    info: 'border-blue-400 text-blue-300',
    work: 'border-amber-400 text-amber-300',
    alert: 'border-red-400 text-red-300 animate-pulse',
  }[t]);

  return (
    <div className="bg-black/40 border-2 border-office-wall rounded-lg p-3 h-[600px] overflow-hidden">
      <div className="text-yellow-200 text-[10px] mb-3 korean">📡 실시간 활동 로그</div>
      <div ref={scrollRef} className="h-[540px] overflow-y-auto space-y-2">
        {items.length === 0 ? (
          <div className="text-gray-500 text-[10px] korean">아직 활동 없음...</div>
        ) : (
          items.map(item => (
            <div key={item.id} className={`border-l-2 pl-2 ${colorFor(item.type)}`}>
              <div className="text-[8px] text-gray-400 korean">
                {new Date(item.ts).toLocaleTimeString('ko-KR')}
              </div>
              <div className="text-[9px] text-white korean font-bold">{item.agentName}</div>
              <div className="text-[9px] text-gray-300 korean leading-tight mt-0.5">{item.message}</div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
