import { useEffect } from 'react';
import { OfficeRoom } from './components/OfficeRoom';
import { ActivityFeed } from './components/ActivityFeed';
import { ControlPanel } from './components/ControlPanel';
import { useOfficeSimulation } from './hooks/useOfficeSimulation';

function App() {
  const { agents, activities, trigger, log } = useOfficeSimulation();

  // 첫 진입 시 환영 메시지
  useEffect(() => {
    log('시스템', 'HYDS Office 가동 — 5명의 에이전트가 대기 중입니다', 'info');
  }, [log]);

  // 자동 자동화 시뮬레이션 (실제로는 백엔드 cron이 하지만 여기선 가시화)
  useEffect(() => {
    const tick = window.setInterval(() => {
      // 5분마다 realtime check (시연 위해 30초)
      trigger('realtime');
    }, 30_000);
    return () => clearInterval(tick);
  }, [trigger]);

  return (
    <div className="min-h-screen bg-office-bg text-white p-6">
      <header className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-yellow-200 text-xl korean">🏢 HYDS Office</h1>
          <p className="text-gray-400 text-[10px] mt-1 korean">5명의 AI 에이전트가 일하는 픽셀 사무실</p>
        </div>
        <div className="text-right">
          <div className="text-[10px] text-green-400 korean">● 자동화 3종 가동 중</div>
          <div className="text-[8px] text-gray-500 mt-1">
            {new Date().toLocaleDateString('ko-KR')}
          </div>
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
        HYDS — 자율형 AI 에이전트 오피스 · 5분마다 자동 실시간 체크 시뮬레이션
      </footer>
    </div>
  );
}

export default App;
