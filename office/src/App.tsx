import { useCallback, useEffect, useState } from 'react';
import { OfficeRoom } from './components/OfficeRoom';
import { ActivityFeed } from './components/ActivityFeed';
import { ControlPanel } from './components/ControlPanel';
import { ChatBox } from './components/ChatBox';
import { useOfficeSimulation } from './hooks/useOfficeSimulation';
import { useHydsData, type HydsEvent } from './hooks/useHydsData';

function fmtTime(iso?: string) {
  if (!iso) return '—';
  const t = Date.parse(iso);
  if (Number.isNaN(t)) return '—';
  return new Date(t).toLocaleString('ko-KR', { hour: '2-digit', minute: '2-digit', month: '2-digit', day: '2-digit' });
}

// 컨트롤 버튼 → 실제 Python 스크립트 (없는 건 시뮬레이션으로 fallthrough)
const CONTROL_MAP: Record<string, { script: string; agent: string; paid: boolean; status: 'working' | 'thinking' | 'moving'; msg: string }> = {
  'daily-monitor': { script: 'daily_monitor', agent: 'retreat-monitor', paid: true, status: 'working', msg: '전체 수련회 분석 중...' },
  'realtime': { script: 'realtime_check', agent: 'retreat-monitor', paid: false, status: 'moving', msg: '신규 보고 확인...' },
  'weekly-todos': { script: 'generate_retreat_todos', agent: 'retreat-planner', paid: true, status: 'thinking', msg: '교회별 To-Do 생성...' },
};

// 채팅 라우팅
const MENTION: Record<string, string> = {
  '기획자': 'retreat-planner',
  '모니터': 'retreat-monitor',
  '리포터': 'report-summarizer',
  '크리에이터': 'content-creator',
  '커뮤니케이터': 'church-communicator',
};
const KEYWORD_ROUTES: { agent: string; kws: string[] }[] = [
  { agent: 'retreat-monitor', kws: ['점검', '진척', '위험', '현황', '체크리스트', 'd-day', 'dday'] },
  { agent: 'report-summarizer', kws: ['후기', '결산', '회고', '사후', '평가'] },
  { agent: 'content-creator', kws: ['카드뉴스', '릴스', '홍보', '캡션', '쇼츠', '포스터', '콘텐츠'] },
  { agent: 'church-communicator', kws: ['답장', '공지', '감사', '카톡', '이메일', '연락', '답변'] },
  { agent: 'retreat-planner', kws: ['기획', '주제', '강사', '장소', '예산', '프로그램'] },
];

function routeAgent(text: string): string {
  const mention = text.match(/@(\S+)/);
  if (mention) {
    const name = mention[1];
    for (const [k, v] of Object.entries(MENTION)) {
      if (name.startsWith(k)) return v;
    }
  }
  const lower = text.toLowerCase();
  for (const { agent, kws } of KEYWORD_ROUTES) {
    if (kws.some(k => lower.includes(k))) return agent;
  }
  return 'retreat-planner'; // 기본
}

function App() {
  const { agents, activities, trigger, log, addActivity, flash, setStatus } = useOfficeSimulation();
  const [chatBusy, setChatBusy] = useState(false);

  useEffect(() => {
    log('시스템', 'HYDS Office 가동 — 실제 자동화 로그에 연결 중...', 'info');
  }, [log]);

  // ── 실제 Python 자동화 이벤트 → 픽셀 캐릭터 ──────────────────────────────
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
        if (!isInitial) flash('retreat-monitor', 'working', `${r.retreats_total}건 분석 → 🔴 ${r.red_count}`, 5000);
      } else if (ev.kind === 'realtime') {
        addActivity({ id: `rt-${ev.ts}`, agentName: 'retreat-monitor', message: '5분 폴링 — 신규 보고 조회', ts: ev.ts, type: 'info' });
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
        addActivity({ id: `al-${ev.ts}-${ev.alerts}`, agentName: '🚨 긴급', message: `실시간 긴급 알림 ${ev.alerts}건 발송`, ts: ev.ts, type: 'alert' });
        if (!isInitial) flash('retreat-monitor', 'thinking', `긴급 ${ev.alerts}건!`, 5000);
      }
    }
  }, [addActivity, flash]);

  const { state, connected } = useHydsData({ onEvents: handleEvents });

  // ── 컨트롤 버튼 → 실제 스크립트 실행 ─────────────────────────────────────
  const handleControl = useCallback(async (id: string) => {
    const m = CONTROL_MAP[id];
    if (!m) { trigger(id); return; } // debate / card-news / reset → 시뮬레이션

    if (m.paid && !window.confirm('Claude 호출 비용이 발생합니다. 진행할까요?')) return;

    setStatus(m.agent, m.status, m.msg);
    log(m.agent, `▶ ${id} 실행 시작 (Python)`, 'work');
    try {
      const res = await fetch(`/api/run/${m.script}`, { method: 'POST' });
      const data = await res.json();
      if (data.ok) {
        const lastLine = String(data.stdout || '').trim().split('\n').filter(Boolean).pop() || '완료';
        addActivity({ id: `run-${m.script}-${Date.now()}`, agentName: m.agent, message: `✅ ${id} 완료 — ${lastLine}`, ts: Date.now(), type: 'work' });
        flash(m.agent, 'idle', '완료! 🎉', 2500);
      } else {
        const tail = String(data.stderr || '').trim().slice(-180) || `종료코드 ${data.code}`;
        addActivity({ id: `run-err-${Date.now()}`, agentName: m.agent, message: `❌ ${id} 실패 — ${tail}`, ts: Date.now(), type: 'alert' });
        flash(m.agent, 'idle', '으윽... 실패했어요 😢', 4000);
      }
    } catch (e) {
      addActivity({ id: `run-err-${Date.now()}`, agentName: m.agent, message: `❌ ${id} 호출 실패 — ${String((e as Error).message || e)}`, ts: Date.now(), type: 'alert' });
      flash(m.agent, 'idle', '서버에 못 닿았어요 😢', 4000);
    }
  }, [trigger, setStatus, log, addActivity, flash]);

  // ── 채팅 → sub-agent 라우팅 + Claude 호출 ────────────────────────────────
  const handleSend = useCallback(async (text: string) => {
    if (!text.trim() || chatBusy) return;
    const agentId = routeAgent(text);
    const agentName = agents.find(a => a.id === agentId)?.name || agentId;

    log('나 (서동현)', text, 'info');
    setChatBusy(true);
    setStatus(agentId, 'thinking', '음... 생각 중');
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ text, agent: agentId }),
      });
      const data = await res.json();
      if (!res.ok || data.error) throw new Error(data.error || `status ${res.status}`);
      const reply: string = data.reply || '(빈 응답)';
      const short = reply.length > 120 ? reply.slice(0, 120) + '…' : reply;
      setStatus(agentId, 'debating', short);
      addActivity({ id: `chat-${Date.now()}`, agentName, message: reply, ts: Date.now(), type: 'work' });
      window.setTimeout(() => setStatus(agentId, 'idle', undefined), 9000);
    } catch (e) {
      setStatus(agentId, 'idle', '으... 문제가 생겼어요 😢');
      addActivity({ id: `chat-err-${Date.now()}`, agentName, message: `❌ 응답 실패: ${String((e as Error).message || e)}`, ts: Date.now(), type: 'alert' });
      window.setTimeout(() => setStatus(agentId, 'idle', undefined), 5000);
    } finally {
      setChatBusy(false);
    }
  }, [chatBusy, agents, log, setStatus, addActivity]);

  const lastRun = state.monitorLog[state.monitorLog.length - 1];
  const lastCheckAt = state.realtime?.last_check_at;

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-rose-50 text-[#4a2c1a] p-6">
      <header className="mb-6 flex items-center justify-between max-w-7xl mx-auto">
        <div>
          <h1 className="text-2xl korean font-bold text-[#4a2c1a]">🏢 HYDS Office</h1>
          <p className="text-amber-700 text-xs mt-1 korean">5명의 AI 에이전트가 일하는 작은 사무실 · 실데이터 + 실행 연동</p>
        </div>
        <div className="text-right space-y-1">
          <div className="inline-flex items-center gap-2 bg-white/70 px-3 py-1.5 rounded-full shadow-sm">
            <span className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500 animate-pulse' : 'bg-rose-500'}`}></span>
            <span className="text-xs korean text-amber-900">
              {connected ? '실데이터 연결됨' : '연결 끊김 (dev 서버 확인)'}
            </span>
          </div>
          <div className="text-[10px] text-amber-600 korean">마지막 실시간 체크: {fmtTime(lastCheckAt)}</div>
          {lastRun && (
            <div className="text-[10px] text-amber-600 korean">최근 모니터링: {fmtTime(lastRun.ran_at)} · 🔴 {lastRun.red_count}건</div>
          )}
        </div>
      </header>

      <div className="grid grid-cols-3 gap-6 max-w-7xl mx-auto">
        <div className="col-span-2 space-y-6">
          <OfficeRoom
            agents={agents}
            onAgentClick={id => {
              const a = agents.find(x => x.id === id);
              if (a) log(a.name, `클릭됨 — 현재 ${a.status}`, 'info');
            }}
          />
          <ChatBox onSend={handleSend} disabled={chatBusy} />
          <ControlPanel onTrigger={handleControl} />
        </div>

        <div>
          <ActivityFeed items={activities} />
        </div>
      </div>

      <footer className="mt-6 text-center text-[10px] text-amber-700/70 korean">
        HYDS — 실데이터 가시화 + 버튼으로 진짜 Python 실행 + 채팅으로 sub-agent 호출
      </footer>
    </div>
  );
}

export default App;
