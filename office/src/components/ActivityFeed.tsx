import { useEffect, useRef } from 'react';

export type ActivityType =
  | 'info' | 'work' | 'alert'
  | 'planning' | 'delegating' | 'synthesizing' | 'complete';

export interface Activity {
  id: string;
  agentName: string;
  message: string;
  ts: number;
  type: ActivityType;
  tone?: string;   // 세션 그룹 색상 (hex) — 있으면 좌측 보더를 이 톤으로
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
    planning: 'border-yellow-400 bg-yellow-50/80',       // 노랑 — 분석/분해
    delegating: 'border-orange-400 bg-orange-50/80',     // 주황 — 위임
    synthesizing: 'border-violet-400 bg-violet-50/80',   // 보라 — 종합
    complete: 'border-emerald-500 bg-emerald-50/80',     // 초록 — 완료
  }[t]);

  const dotFor = (t: Activity['type']) => ({
    info: 'bg-sky-500',
    work: 'bg-amber-500',
    alert: 'bg-rose-500',
    planning: 'bg-yellow-500',
    delegating: 'bg-orange-500',
    synthesizing: 'bg-violet-500',
    complete: 'bg-emerald-500',
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
            <div
              key={item.id}
              className={`border-l-4 pl-3 py-2 rounded-r-lg ${item.tone ? '' : styleFor(item.type)}`}
              style={item.tone ? { borderLeftColor: item.tone, background: `${item.tone}14` } : undefined}
            >
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
