import { useCallback, useEffect, useMemo, useState } from 'react';
import { OfficeRoom } from './components/OfficeRoom';
import { ActivityFeed } from './components/ActivityFeed';
import { ControlPanel } from './components/ControlPanel';
import { ChatBox } from './components/ChatBox';
import { useOfficeSimulation, type PhaseEvent } from './hooks/useOfficeSimulation';
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

const DEFAULT_PLACEHOLDER = "에이전트에게 명령하세요... 예: '평택교회 카드뉴스 8장 만들어줘'";
const SESSION_KEY = 'hyds_chat_session_id';
const TONE_PALETTE = ['#fb923c', '#60a5fa', '#34d399', '#a78bfa', '#f472b6', '#fbbf24'];

function newSessionId(): string {
  const c = (globalThis.crypto as Crypto | undefined);
  if (c && typeof c.randomUUID === 'function') return c.randomUUID();
  return `s-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function toneFor(sessionId: string): string {
  let h = 0;
  for (const ch of sessionId) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return TONE_PALETTE[h % TONE_PALETTE.length];
}

// 후속 질문(되묻기)으로 보이면 placeholder를 답변 모드로
function looksLikeQuestion(reply: string): boolean {
  return /[?？]/.test(reply) || /(필요|알려|어떤|무엇|몇 명|언제|얼마|주세요|있나요|할까요)/.test(reply);
}

// /api/chat SSE 스트림을 읽어 phase 이벤트마다 onEvent 호출
async function streamChat(text: string, sessionId: string, onEvent: (ev: PhaseEvent) => void) {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ text, sessionId }),
  });
  if (!res.ok || !res.body) throw new Error(`스트림 연결 실패 (${res.status})`);
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = '';
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    let idx: number;
    while ((idx = buf.indexOf('\n\n')) !== -1) {
      const chunk = buf.slice(0, idx);
      buf = buf.slice(idx + 2);
      const line = chunk.split('\n').find(l => l.startsWith('data:'));
      if (!line) continue;
      try { onEvent(JSON.parse(line.slice(5).trim()) as PhaseEvent); } catch { /* 부분 청크 무시 */ }
    }
  }
}

function App() {
  const { agents, activities, meetings, trigger, log, addActivity, clearActivities, flash, setStatus, handlePhase } = useOfficeSimulation();
  const [chatBusy, setChatBusy] = useState(false);
  const [sessionId, setSessionId] = useState<string>(() => {
    const existing = sessionStorage.getItem(SESSION_KEY);
    if (existing) return existing;
    const id = newSessionId();
    sessionStorage.setItem(SESSION_KEY, id);
    return id;
  });
  const [turns, setTurns] = useState(0);
  const [placeholder, setPlaceholder] = useState(DEFAULT_PLACEHOLDER);
  const tone = useMemo(() => toneFor(sessionId), [sessionId]);

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

  // ── 채팅 → 부장 오케스트레이션 (SSE 스트리밍 + 세션) ─────────────────────
  const handleSend = useCallback(async (text: string) => {
    if (!text.trim() || chatBusy) return;
    if (!window.confirm(
      '복합 요청이면 위임마다 추가 Claude 호출이 발생합니다.\n' +
      '(부장 분석 1 + 워커들 + 종합 1. 미디어 작업은 본부장이 다시 3팀장에게 재위임해\n' +
      ' 호출이 더 늘 수 있습니다 — 대략 10~30센트)\n진행할까요?'
    )) return;

    addActivity({ id: `user-${Date.now()}`, agentName: '나 (서동현)', message: text, ts: Date.now(), type: 'info', tone });
    setChatBusy(true);
    try {
      await streamChat(text, sessionId, ev => {
        handlePhase(ev, tone);
        if (ev.phase === 'complete') {
          setTurns(typeof ev.turns === 'number' ? ev.turns : t => t + 1);
          setPlaceholder(looksLikeQuestion(ev.reply || '') ? '답변 입력...' : DEFAULT_PLACEHOLDER);
        }
      });
    } catch (e) {
      handlePhase({ phase: 'error', error: String((e as Error).message || e) }, tone);
    } finally {
      setChatBusy(false);
    }
  }, [chatBusy, sessionId, tone, addActivity, handlePhase]);

  // ── 새 대화: 세션 비우고 새 ID + 로그 클리어 ─────────────────────────────
  const handleNewConversation = useCallback(async () => {
    if (chatBusy) return;
    try {
      await fetch('/api/chat/reset', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ sessionId }),
      });
    } catch { /* 서버 못 닿아도 클라이언트는 새로 시작 */ }
    const id = newSessionId();
    sessionStorage.setItem(SESSION_KEY, id);
    setSessionId(id);
    setTurns(0);
    setPlaceholder(DEFAULT_PLACEHOLDER);
    clearActivities();
    log('시스템', '🆕 새 대화를 시작했습니다', 'info');
  }, [chatBusy, sessionId, clearActivities, log]);

  const lastRun = state.monitorLog[state.monitorLog.length - 1];
  const lastCheckAt = state.realtime?.last_check_at;

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-rose-50 text-[#4a2c1a] p-6">
      <header className="mb-6 flex items-center justify-between max-w-7xl mx-auto">
        <div>
          <h1 className="text-2xl korean font-bold text-[#4a2c1a]">🏢 HYDS Office</h1>
          <p className="text-amber-700 text-xs mt-1 korean">9명의 AI 에이전트 · 부장 + 수련회 4팀장 + 미디어 본부(본부장·3팀장) · 실데이터 연동</p>
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
            meetings={meetings}
            onAgentClick={id => {
              const a = agents.find(x => x.id === id);
              if (a) log(a.name, `클릭됨 — 현재 ${a.status}`, 'info');
            }}
          />
          <ChatBox
            onSend={handleSend}
            onNewConversation={handleNewConversation}
            disabled={chatBusy}
            turns={turns}
            placeholder={placeholder}
          />
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
