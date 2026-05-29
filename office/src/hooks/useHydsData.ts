import { useEffect, useRef, useState, useCallback } from 'react';
import type { HydsState, MonitorRun, WeeklyRun } from '@/data/hydsTypes';

// 실제 Python 자동화에서 감지된 "사건" 하나.
export interface HydsEvent {
  kind: 'monitor' | 'realtime' | 'alert' | 'weekly';
  ts: number; // epoch ms
  run?: MonitorRun;
  weekly?: WeeklyRun;
  alerts?: number;
}

interface Options {
  // 새로 감지된 이벤트들을 넘겨줌. isInitial=true면 첫 로드(과거 이력) → 애니메이션 없이 피드만 채움.
  onEvents: (events: HydsEvent[], isInitial: boolean) => void;
  intervalMs?: number;
}

const EMPTY: HydsState = { monitorLog: [], realtime: null, weeklyLog: [] };

/**
 * /api/hyds-state 를 주기적으로 폴링해서, 직전 상태와 비교해 "새 이벤트"만 감지한다.
 * - 새 monitor_log 항목 → 'monitor' (red_count>0 이면 alert 타입)
 * - realtime_state.last_check_at 변경 → 'realtime' (last_run_alerts>0 이면 'alert' 추가)
 */
export function useHydsData({ onEvents, intervalMs = 4000 }: Options) {
  const [state, setState] = useState<HydsState>(EMPTY);
  const [connected, setConnected] = useState(false);

  const seenMonitor = useRef<Set<string>>(new Set()); // ran_at 기준 중복 방지
  const seenWeekly = useRef<Set<string>>(new Set());
  const lastCheck = useRef<string | null>(null);
  const firstLoad = useRef(true);
  const onEventsRef = useRef(onEvents);
  onEventsRef.current = onEvents;

  const poll = useCallback(async () => {
    try {
      const res = await fetch('/api/hyds-state');
      if (!res.ok) throw new Error(`status ${res.status}`);
      const data = (await res.json()) as HydsState;
      setConnected(true);
      setState(data);

      const isInitial = firstLoad.current;
      const events: HydsEvent[] = [];

      // 1) 새 일일 모니터링 실행
      for (const run of data.monitorLog) {
        if (seenMonitor.current.has(run.ran_at)) continue;
        seenMonitor.current.add(run.ran_at);
        events.push({
          kind: 'monitor',
          ts: Date.parse(run.ran_at) || Date.now(),
          run,
        });
      }

      // 2) 새 주간 To-Do 생성
      for (const run of data.weeklyLog ?? []) {
        if (seenWeekly.current.has(run.ran_at)) continue;
        seenWeekly.current.add(run.ran_at);
        events.push({
          kind: 'weekly',
          ts: Date.parse(run.ran_at) || Date.now(),
          weekly: run,
        });
      }

      // 3) 실시간 체크 (last_check_at 변경 시). 첫 로드에서는 "방금 일어난 일"이 아니므로 스킵.
      const lc = data.realtime?.last_check_at ?? null;
      if (lc && lc !== lastCheck.current) {
        if (!isInitial) {
          const ts = Date.parse(lc) || Date.now();
          events.push({ kind: 'realtime', ts });
          const alerts = data.realtime?.last_run_alerts ?? 0;
          if (alerts > 0) events.push({ kind: 'alert', ts, alerts });
        }
        lastCheck.current = lc;
      }

      if (events.length) onEventsRef.current(events, isInitial);
      firstLoad.current = false;
    } catch {
      setConnected(false);
    }
  }, []);

  useEffect(() => {
    poll();
    const id = window.setInterval(poll, intervalMs);
    return () => window.clearInterval(id);
  }, [poll, intervalMs]);

  return { state, connected };
}
