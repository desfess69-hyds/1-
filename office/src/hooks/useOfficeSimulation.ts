import { useState, useCallback, useRef } from 'react';
import { initialAgents, type Agent, type AgentStatus, type RoomId } from '@/data/agents';
import type { Activity } from '@/components/ActivityFeed';
import type { RoomMeeting } from '@/components/OfficeRoom';

// /api/chat SSE 위임 이벤트 (2단계: 부장 → 본부장 → 팀장)
export interface PhaseEvent {
  phase:
    | 'planning' | 'plan-ready' | 'delegating' | 'worker-done'
    | 'sub-delegating' | 'sub-worker-done'        // 미디어 본부 내부 위임
    | 'synthesizing' | 'complete' | 'error';
  plan?: Array<{ agent: string; task: string }>;
  reasoning?: string;
  director?: string;        // sub-* 이벤트의 본부장 (예: media-director)
  agent?: string;
  task?: string;
  result?: string;
  reply?: string;
  error?: boolean | string;
  turns?: number;
}

export type Meetings = Record<RoomId, RoomMeeting>;
const EMPTY_MEETINGS: Meetings = {
  retreat: { active: false, agenda: '' },
  media: { active: false, agenda: '' },
};

// 에이전트 → 소속 회의실 매핑
const ROOM_OF = new Map(initialAgents.map(a => [a.id, a.room]));

let activityCounter = 0;
function genId() {
  return `${Date.now()}-${++activityCounter}`;
}

function buildAgenda(items: Array<{ task: string }>): string {
  return items
    .map(p => (p.task.length > 16 ? p.task.slice(0, 16) + '…' : p.task))
    .join('  +  ');
}

export function useOfficeSimulation() {
  const [agents, setAgents] = useState<Agent[]>(initialAgents);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [meetings, setMeetings] = useState<Meetings>(EMPTY_MEETINGS);
  const timeoutsRef = useRef<number[]>([]);

  const later = useCallback((fn: () => void, ms: number) => {
    timeoutsRef.current.push(window.setTimeout(fn, ms));
  }, []);

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

  const flash = useCallback((id: string, status: AgentStatus, message?: string, ms = 4000) => {
    setStatus(id, status, message);
    const t = window.setTimeout(() => setStatus(id, 'idle', undefined), ms);
    timeoutsRef.current.push(t);
  }, [setStatus]);

  // 회의실 이동: inMeeting 플래그 + 상태 + 말풍선 동시 갱신
  const moveAgent = useCallback((id: string, inMeeting: boolean, status: AgentStatus, message?: string) => {
    setAgents(prev => prev.map(a => a.id === id ? { ...a, inMeeting, status, message } : a));
  }, []);

  // 회의실 한 곳의 상태만 갱신
  const setRoom = useCallback((id: RoomId, patch: Partial<RoomMeeting>) => {
    setMeetings(prev => ({ ...prev, [id]: { ...prev[id], ...patch } }));
  }, []);

  const nameOf = useCallback(
    (id: string) => initialAgents.find(a => a.id === id)?.name || id,
    [],
  );

  const clearActivities = useCallback(() => setActivities([]), []);

  // 팀장 한 명을 회의실로 소집 (이동 → 1.5초 후 작업)
  const summon = useCallback((agentId: string, task: string, who: string, now: number, i: number, add: (a: Activity) => void) => {
    const bubble = task.slice(0, 30) + (task.length > 30 ? '…' : '');
    moveAgent(agentId, true, 'moving', '회의실로 이동...');
    add({ id: `deleg-${who}-${now}-${i}`, agentName: nameOf(agentId), message: `▶ ${task}`, ts: now + i + 1, type: 'delegating' });
    later(() => moveAgent(agentId, true, 'working', bubble), 1500);
  }, [moveAgent, nameOf, later]);

  // 작업 끝난 팀장을 자기 자리로 복귀
  const sendHome = useCallback((id: string, task: string | undefined, result: string | undefined, error: boolean | string | undefined, now: number, add: (a: Activity) => void) => {
    const short = (result || '').replace(/\s+/g, ' ').trim().slice(0, 90);
    add({
      id: `done-${id}-${now}`,
      agentName: nameOf(id),
      message: `${error ? '⚠️' : '✅'} ${task} → ${short}${short.length >= 90 ? '…' : ''}`,
      ts: now,
      type: error ? 'alert' : 'work',
    });
    moveAgent(id, false, 'moving', '자리로 복귀');
    later(() => moveAgent(id, false, 'idle', undefined), 1500);
  }, [moveAgent, nameOf, later]);

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
        const mediaDir = plan.find(p => p.agent === 'media-director');
        const directItems = plan.filter(p => p.agent !== 'media-director');

        // 부장 회의 (수련회 회의실) 점등 — 부장이 상석에 앉아 주관
        const dirAgenda = directItems.length
          ? buildAgenda(directItems)
          : (mediaDir ? '미디어 본부에 위임' : '진행');
        setRoom('retreat', { active: true, agenda: dirAgenda });
        add({ id: `ph-deleg-${now}`, agentName: '부장', message: `${plan.length}곳에 위임`, ts: now, type: 'delegating' });
        moveAgent('hyds-director', true, 'moving', '회의 소집');
        later(() => moveAgent('hyds-director', true, 'working', '회의 주관 중'), 1500);

        // 수련회 팀장 직접 소집
        directItems.forEach((item, i) => summon(item.agent, item.task, 'r', now, i, add));

        // 미디어 본부장에게 통째로 위임 → 본부장이 미디어 회의실로
        if (mediaDir) {
          setRoom('media', { active: true, agenda: '미디어팀 소집 중...' });
          add({ id: `ph-deleg-md-${now}`, agentName: '미디어본부장', message: `▶ ${mediaDir.task}`, ts: now + 1, type: 'delegating' });
          moveAgent('media-director', true, 'moving', '미디어팀 소집');
          later(() => moveAgent('media-director', true, 'working', '본부 회의 주관'), 1500);
        }
        break;
      }

      // 미디어 본부장이 자기 회의실로 팀장 3명 소집
      case 'sub-delegating': {
        const plan = ev.plan || [];
        setRoom('media', { active: true, agenda: buildAgenda(plan) });
        add({ id: `ph-sub-${now}`, agentName: '미디어본부장', message: `${plan.length}명 팀장에게 분배`, ts: now, type: 'delegating' });
        plan.forEach((item, i) => summon(item.agent, item.task, 'm', now, i, add));
        break;
      }

      case 'sub-worker-done':
        sendHome(ev.agent || '', ev.task, ev.result, ev.error, now, add);
        break;

      case 'worker-done': {
        const id = ev.agent || '';
        sendHome(id, ev.task, ev.result, ev.error, now, add);
        // 미디어 본부장 종합 완료 → 미디어 회의실 닫기
        if (id === 'media-director') {
          setRoom('media', { agenda: '✅ 본부 종합 완료' });
          later(() => setRoom('media', { active: false, agenda: '' }), 2500);
        }
        break;
      }

      case 'synthesizing':
        moveAgent('hyds-director', true, 'working', '종합 보고 작성 중...');
        add({ id: `ph-synth-${now}`, agentName: '부장', message: '각 본부 결과 종합 중...', ts: now, type: 'synthesizing' });
        break;

      case 'complete': {
        const reply = ev.reply || '(빈 응답)';
        const bubble = reply.length > 120 ? reply.slice(0, 120) + '…' : reply;
        setRoom('retreat', { active: true, agenda: '✅ 완료' });
        add({ id: `ph-complete-${now}`, agentName: '부장', message: reply, ts: now, type: 'complete' });
        moveAgent('hyds-director', false, 'moving', '보고 정리');
        later(() => moveAgent('hyds-director', false, 'debating', bubble), 1500);
        later(() => setMeetings(EMPTY_MEETINGS), 3500);
        later(() => setStatus('hyds-director', 'idle', undefined), 10000);
        break;
      }

      case 'error':
        setMeetings(EMPTY_MEETINGS);
        moveAgent('hyds-director', false, 'idle', '으... 문제가 생겼어요 😢');
        add({ id: `ph-err-${now}`, agentName: '부장', message: `❌ ${ev.error}`, ts: now, type: 'alert' });
        later(() => setStatus('hyds-director', 'idle', undefined), 5000);
        break;
    }
  }, [setStatus, addActivity, moveAgent, setRoom, summon, sendHome, later]);

  const resetAll = useCallback(() => {
    timeoutsRef.current.forEach(t => clearTimeout(t));
    timeoutsRef.current = [];
    setAgents(initialAgents);
    setMeetings(EMPTY_MEETINGS);
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
        // 미디어 본부 내부 톤 결정 회의
        setStatus('concept-planner', 'debating', '캠페인 톤: 진중 vs 친근?');
        setStatus('scriptwriter', 'debating', '후크 카피 방향 고민...');
        log('concept-planner', '⚡ 카드뉴스 톤앤매너 결정 회의 시작', 'info');
        const lines: [string, string][] = [
          ['concept-planner', '청년부 대상이니 친근한 톤으로 잡읍시다.'],
          ['scriptwriter', '동의. 다만 첫 슬라이드는 무게감 있게 시작할게요.'],
          ['concept-planner', '좋아요. "지친 청년들에게" → 점차 따뜻하게.'],
          ['scriptwriter', '확정. 8장 기준 후크/본문/CTA로 카피 들어갑니다.'],
        ];
        lines.forEach(([who, msg], i) => {
          const t = window.setTimeout(() => setStatus(who, 'debating', msg), 1500 * (i + 1));
          timeoutsRef.current.push(t);
        });
        const tEnd = window.setTimeout(() => {
          setStatus('concept-planner', 'idle');
          setStatus('scriptwriter', 'idle');
          log('시스템', '✅ 합의: 친근하되 시작은 무게감 → media-producer 제작 인계', 'work');
        }, 1500 * 5);
        timeoutsRef.current.push(tEnd);
        break;
      }

      case 'card-news': {
        setStatus('media-producer', 'working', '슬라이드 8장 이미지 생성 중...');
        log('media-producer', '주제: 기도가 어려울 때 — 카드뉴스 8장 + 캡션', 'work');
        const t = window.setTimeout(() => {
          setStatus('media-producer', 'idle', '저장 완료');
          log('media-producer', '✅ .tmp/card_drafts/ 폴더에 저장', 'work');
          window.setTimeout(() => setStatus('media-producer', 'idle', undefined), 2000);
        }, 3000);
        timeoutsRef.current.push(t);
        break;
      }

      case 'reset':
      default:
        resetAll();
    }
  }, [log, setStatus, resetAll]);

  return { agents, activities, meetings, trigger, log, setStatus, addActivity, clearActivities, flash, handlePhase };
}
