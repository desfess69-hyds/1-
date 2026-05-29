import { useState, useCallback, useRef } from 'react';
import { initialAgents, type Agent, type AgentStatus } from '@/data/agents';
import type { Activity } from '@/components/ActivityFeed';

// /api/chat SSE 위임 이벤트
export interface PhaseEvent {
  phase: 'planning' | 'plan-ready' | 'delegating' | 'worker-done' | 'synthesizing' | 'complete' | 'error';
  plan?: Array<{ agent: string; task: string }>;
  reasoning?: string;
  agent?: string;
  task?: string;
  result?: string;
  reply?: string;
  error?: boolean | string;
  turns?: number;
}

let activityCounter = 0;

function genId() {
  return `${Date.now()}-${++activityCounter}`;
}

export function useOfficeSimulation() {
  const [agents, setAgents] = useState<Agent[]>(initialAgents);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [meeting, setMeeting] = useState<{ active: boolean; agenda: string }>({ active: false, agenda: '' });
  const timeoutsRef = useRef<number[]>([]);

  const log = useCallback((agentName: string, message: string, type: Activity['type'] = 'info') => {
    setActivities(prev => [
      { id: genId(), agentName, message, ts: Date.now(), type },
      ...prev,
    ].slice(0, 50));
  }, []);

  // 실제 데이터에서 만든 활동(고유 id + 실제 timestamp)을 중복 없이 병합.
  const addActivity = useCallback((a: Activity) => {
    setActivities(prev => {
      if (prev.some(p => p.id === a.id)) return prev;
      return [a, ...prev].sort((x, y) => y.ts - x.ts).slice(0, 50);
    });
  }, []);

  const setStatus = useCallback((id: string, status: AgentStatus, message?: string) => {
    setAgents(prev => prev.map(a => a.id === id ? { ...a, status, message } : a));
  }, []);

  // 잠깐 상태를 바꿨다가 일정 시간 뒤 idle 로 복귀 (실제 자동화 이벤트 가시화용).
  const flash = useCallback((id: string, status: AgentStatus, message?: string, ms = 4000) => {
    setStatus(id, status, message);
    const t = window.setTimeout(() => setStatus(id, 'idle', undefined), ms);
    timeoutsRef.current.push(t);
  }, [setStatus]);

  // 회의실 이동: inMeeting 플래그 + 상태 + 말풍선 동시 갱신
  const moveAgent = useCallback((id: string, inMeeting: boolean, status: AgentStatus, message?: string) => {
    setAgents(prev => prev.map(a => a.id === id ? { ...a, inMeeting, status, message } : a));
  }, []);

  const nameOf = useCallback(
    (id: string) => initialAgents.find(a => a.id === id)?.name || id,
    [],
  );

  const clearActivities = useCallback(() => setActivities([]), []);

  // SSE 위임 이벤트 → 캐릭터/활동 로그 반영 (tone: 세션 그룹 색상)
  const handlePhase = useCallback((ev: PhaseEvent, tone?: string) => {
    const now = Date.now();
    const add = (a: Activity) => addActivity(tone ? { ...a, tone } : a);
    switch (ev.phase) {
      case 'planning':
        setStatus('hyds-director', 'thinking', '요청 분석 중...');
        add({ id: `ph-plan-${now}`, agentName: '부장', message: '요청 분석 — 작업 분해 중', ts: now, type: 'planning' });
        break;
      case 'plan-ready':
        if (ev.reasoning) {
          add({ id: `ph-reason-${now}`, agentName: '부장', message: `분해: ${ev.reasoning}`, ts: now, type: 'planning' });
        }
        break;
      case 'delegating': {
        const plan = ev.plan || [];
        const agenda = plan
          .map(p => (p.task.length > 18 ? p.task.slice(0, 18) + '…' : p.task))
          .join('  +  ');
        setMeeting({ active: true, agenda });
        add({ id: `ph-deleg-${now}`, agentName: '부장', message: `${plan.length}개 팀장에게 위임`, ts: now, type: 'delegating' });

        // 부장 회의실 합류 (synthesizing 까지 머묾)
        moveAgent('hyds-director', true, 'moving', '회의 소집');
        timeoutsRef.current.push(window.setTimeout(() => moveAgent('hyds-director', true, 'working', '회의 주관 중'), 1500));

        // 워커들 회의실로 이동 → 1.5초 후 작업
        plan.forEach((item, i) => {
          const bubble = item.task.slice(0, 30) + (item.task.length > 30 ? '…' : '');
          moveAgent(item.agent, true, 'moving', '회의실로 이동...');
          add({ id: `ph-deleg-${now}-${i}`, agentName: nameOf(item.agent), message: `▶ ${item.task}`, ts: now + i + 1, type: 'delegating' });
          timeoutsRef.current.push(window.setTimeout(() => moveAgent(item.agent, true, 'working', bubble), 1500));
        });
        break;
      }
      case 'worker-done': {
        const id = ev.agent || '';
        const short = (ev.result || '').replace(/\s+/g, ' ').trim().slice(0, 90);
        add({
          id: `ph-done-${id}-${now}`,
          agentName: nameOf(id),
          message: `${ev.error ? '⚠️' : '✅'} ${ev.task} → ${short}${short.length >= 90 ? '…' : ''}`,
          ts: now,
          type: ev.error ? 'alert' : 'work',
        });
        // 자기 자리로 복귀 → 1.5초 후 idle
        moveAgent(id, false, 'moving', '자리로 복귀');
        timeoutsRef.current.push(window.setTimeout(() => moveAgent(id, false, 'idle', undefined), 1500));
        break;
      }
      case 'synthesizing':
        // 부장은 회의실에서 종합
        moveAgent('hyds-director', true, 'working', '종합 보고 작성 중...');
        add({ id: `ph-synth-${now}`, agentName: '부장', message: '팀장 결과 종합 중...', ts: now, type: 'synthesizing' });
        break;
      case 'complete': {
        const reply = ev.reply || '(빈 응답)';
        const bubble = reply.length > 120 ? reply.slice(0, 120) + '…' : reply;
        setMeeting({ active: true, agenda: '✅ 완료' });
        add({ id: `ph-complete-${now}`, agentName: '부장', message: reply, ts: now, type: 'complete' });
        // 부장 자리로 복귀 후 최종 보고
        moveAgent('hyds-director', false, 'moving', '보고 정리');
        timeoutsRef.current.push(window.setTimeout(() => moveAgent('hyds-director', false, 'debating', bubble), 1500));
        // 화이트보드 잠시 후 사라짐 + 부장 idle 복귀
        timeoutsRef.current.push(window.setTimeout(() => setMeeting({ active: false, agenda: '' }), 3500));
        timeoutsRef.current.push(window.setTimeout(() => setStatus('hyds-director', 'idle', undefined), 10000));
        break;
      }
      case 'error':
        setMeeting({ active: false, agenda: '' });
        moveAgent('hyds-director', false, 'idle', '으... 문제가 생겼어요 😢');
        add({ id: `ph-err-${now}`, agentName: '부장', message: `❌ ${ev.error}`, ts: now, type: 'alert' });
        timeoutsRef.current.push(window.setTimeout(() => setStatus('hyds-director', 'idle', undefined), 5000));
        break;
    }
  }, [setStatus, addActivity, moveAgent, nameOf]);

  const resetAll = useCallback(() => {
    timeoutsRef.current.forEach(t => clearTimeout(t));
    timeoutsRef.current = [];
    setAgents(initialAgents);
    setMeeting({ active: false, agenda: '' });
    log('시스템', '모든 에이전트 idle 복귀', 'info');
  }, [log]);

  const trigger = useCallback((action: string) => {
    switch (action) {
      case 'daily-monitor': {
        setStatus('retreat-monitor', 'thinking', '오늘 위험도 분석 중...');
        log('retreat-monitor', '매일 09:00 자동 실행 — 전체 수련회 스캔', 'work');

        const t1 = window.setTimeout(() => {
          setStatus('retreat-monitor', 'working', '6건 분석 중...');
          log('retreat-monitor', 'Claude로 위험도 판정 (🔴 4건 발견 시뮬)', 'work');
        }, 1500);
        const t2 = window.setTimeout(() => {
          setStatus('retreat-monitor', 'idle', '텔레그램 발송 완료');
          log('retreat-monitor', '✅ 텔레그램 알림 발송 성공', 'work');
          window.setTimeout(() => setStatus('retreat-monitor', 'idle', undefined), 2000);
        }, 4000);
        timeoutsRef.current.push(t1, t2);
        break;
      }

      case 'realtime': {
        setStatus('retreat-monitor', 'moving', '신규 보고 확인...');
        log('retreat-monitor', '5분 폴링: 신규 retreat_reports 조회', 'info');
        const t = window.setTimeout(() => {
          setStatus('retreat-monitor', 'idle', '신규 없음');
          window.setTimeout(() => setStatus('retreat-monitor', 'idle', undefined), 1500);
        }, 2000);
        timeoutsRef.current.push(t);
        break;
      }

      case 'weekly-todos': {
        setStatus('retreat-monitor', 'working', 'To-Do 생성 중...');
        setStatus('retreat-planner', 'thinking', '교회별 현황 분석...');
        log('시스템', '매주 월 09:30 자동 실행 — 수련회별 To-Do', 'work');

        const t1 = window.setTimeout(() => {
          log('retreat-monitor', 'Word 문서 생성 (6 페이지)', 'work');
        }, 2000);
        const t2 = window.setTimeout(() => {
          setStatus('retreat-monitor', 'idle');
          setStatus('retreat-planner', 'idle');
          log('시스템', '✅ 텔레그램 발송 완료', 'work');
        }, 4500);
        timeoutsRef.current.push(t1, t2);
        break;
      }

      case 'debate': {
        setStatus('retreat-planner', 'debating', '강사 사례비 60만 vs 80만?');
        setStatus('content-creator', 'debating', '카드뉴스 톤은 진중 vs 친근?');
        log('retreat-planner', '⚡ 카드뉴스 톤 결정 회의 시작', 'info');

        const lines: [string, string][] = [
          ['retreat-planner', '청년부 대상이니 친근한 톤이 좋겠어요.'],
          ['content-creator', '동의. 다만 첫 슬라이드는 무게감 있게 시작합시다.'],
          ['retreat-planner', '좋아요. "지친 청년들에게" 시작 → 점차 따뜻하게.'],
          ['content-creator', '확정. 슬라이드 8장 기준 잡고 작업 들어갈게요.'],
        ];
        lines.forEach(([who, msg], i) => {
          const t = window.setTimeout(() => setStatus(who, 'debating', msg), 1500 * (i + 1));
          timeoutsRef.current.push(t);
        });
        const tEnd = window.setTimeout(() => {
          setStatus('retreat-planner', 'idle');
          setStatus('content-creator', 'idle');
          log('시스템', '✅ 합의 도출: 친근하되 시작은 무게감', 'work');
        }, 1500 * 5);
        timeoutsRef.current.push(tEnd);
        break;
      }

      case 'card-news': {
        setStatus('content-creator', 'working', '슬라이드 8장 작성 중...');
        log('content-creator', '주제: 기도가 어려울 때 — 카드뉴스 8장 + 캡션', 'work');
        const t = window.setTimeout(() => {
          setStatus('content-creator', 'idle', '저장 완료');
          log('content-creator', '✅ .tmp/card_drafts/ 폴더에 저장', 'work');
          window.setTimeout(() => setStatus('content-creator', 'idle', undefined), 2000);
        }, 3000);
        timeoutsRef.current.push(t);
        break;
      }

      case 'reset':
      default:
        resetAll();
    }
  }, [log, setStatus, resetAll]);

  return { agents, activities, meeting, trigger, log, setStatus, addActivity, clearActivities, flash, handlePhase };
}
