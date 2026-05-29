import { useCallback, useEffect } from 'react';
import { OfficeRoom } from './components/OfficeRoom';
import { ActivityFeed } from './components/ActivityFeed';
import { ControlPanel } from './components/ControlPanel';
import { useOfficeSimulation } from './hooks/useOfficeSimulation';
import { useHydsData, type HydsEvent } from './hooks/useHydsData';

function fmtTime(iso?: string) {
  if (!iso) return '—';
  const t = Date.parse(iso);
  if (Number.isNaN(t)) return '—';
  return new Date(t).toLocaleString('ko-KR', { hour: '2-digit', minute: '2-digit', month: '2-digit', day: '2-digit' });
}

function App() {
  const { agents, activities, trigger, log, addActivity, flash } = useOfficeSimulation();

  // 첫 진입 시 환영 메시지
  useEffect(() => {
    log('시스템', 'HYDS Office 가동 — 실제 자동화 로그에 연결 중...', 'info');
  }, [log]);

  // 실제 Python 자동화 이벤트 → 픽셀 캐릭터 + 활동 로그
  const handleEvents = useCallback((events: HydsEvent[], isInitial: boolean) => {
    for (const ev of events) {
      if (ev.kind === 'monitor' && ev.run) {
        const r = ev.run;
        addActivity({
          id: `mon-${r.ran_at}`,
          agentName: 'retreat-monitor',
          message: `일일 모니터링 — ${r.retreats_total}건 분석 · 🔴 위험 ${r.red_count}건${r.notified ? ' · 텔레그램 발송' : ''}`,
          ts: ev.ts,
          type: r.red_count > 0 ? 'alert' : 'work',
        });
        if (!isInitial) {
          flash('retreat-monitor', 'working', `${r.retreats_total}건 분석 → 🔴 ${r.red_count}`, 5000);
        }
      } else if (ev.kind === 'realtime') {
        addActivity({
          id: `rt-${ev.ts}`,
          agentName: 'retreat-monitor',
          message: '5분 폴링 — 신규 보고 조회',
          ts: ev.ts,
          type: 'info',
        });
        if (!isInitial) flash('retreat-monitor', 'moving', '신규 보고 확인...', 2500);
      } else if (ev.kind === 'weekly' && ev.weekly) {
        const w = ev.weekly;
        addActivity({
          id: `wk-${w.ran_at}`,
          agentName: 'retreat-planner',
          message: `주간 To-Do 생성 — ${w.retreats_total}개 교회 · 할 일 ${w.total_todos}개${w.notified ? ' · 텔레그램 발송' : ''}`,
          ts: ev.ts,
          type: 'work',
        });
        if (!isInitial) {
          flash('retreat-planner', 'thinking', '교회별 현황 분석...', 5000);
          flash('retreat-monitor', 'working', `To-Do ${w.total_todos}개 정리`, 5000);
        }
      } else if (ev.kind === 'alert') {
        addActivity({
          id: `al-${ev.ts}-${ev.alerts}`,
          agentName: '🚨 긴급',
          message: `실시간 긴급 알림 ${ev.alerts}건 발송`,
          ts: ev.ts,
          type: 'alert',
        });
        if (!isInitial) flash('retreat-monitor', 'thinking', `긴급 ${ev.alerts}건!`, 5000);
      }
    }
  }, [addActivity, flash]);

  const { state, connected } = useHydsData({ onEvents: handleEvents });

  const lastRun = state.monitorLog[state.monitorLog.length - 1];
  const lastCheckAt = state.realtime?.last_check_at;

  return (
    <div className="min-h-screen bg-office-bg text-white p-6">
      <header className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-yellow-200 text-xl korean">🏢 HYDS Office</h1>
          <p className="text-gray-400 text-[10px] mt-1 korean">5명의 AI 에이전트가 일하는 픽셀 사무실 · 실데이터 연동</p>
        </div>
        <div className="text-right space-y-1">
          <div className={`text-[10px] korean ${connected ? 'text-green-400' : 'text-red-400'}`}>
            {connected ? '● 실데이터 연결됨' : '○ 연결 끊김 (dev 서버 확인)'}
          </div>
          <div className="text-[8px] text-gray-400 korean">
            마지막 실시간 체크: {fmtTime(lastCheckAt)}
          </div>
          {lastRun && (
            <div className="text-[8px] text-gray-400 korean">
              최근 모니터링: {fmtTime(lastRun.ran_at)} · 🔴 {lastRun.red_count}건
            </div>
          )}
        </div>
      </header>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-6">
          <OfficeRoom
            agents={agents}
            onAgentClick={id => {
              const a = agents.find(x => x.id === id);
              if (a) log(a.name, `클릭됨 — 현재 ${a.status}`, 'info');
            }}
          />
          <ControlPanel onTrigger={trigger} />
        </div>

        <div>
          <ActivityFeed items={activities} />
        </div>
      </div>

      <footer className="mt-6 text-center text-[8px] text-gray-500 korean">
        HYDS — 실제 data/monitor_log.json · realtime_state.json 을 4초마다 읽어 픽셀로 가시화 · 컨트롤 패널은 수동 시뮬레이션
      </footer>
    </div>
  );
}

export default App;
