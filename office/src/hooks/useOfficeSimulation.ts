import { useState, useCallback, useRef } from 'react';
import { initialAgents, type Agent, type AgentStatus } from '@/data/agents';
import type { Activity } from '@/components/ActivityFeed';

let activityCounter = 0;

function genId() {
  return `${Date.now()}-${++activityCounter}`;
}

export function useOfficeSimulation() {
  const [agents, setAgents] = useState<Agent[]>(initialAgents);
  const [activities, setActivities] = useState<Activity[]>([]);
  const timeoutsRef = useRef<number[]>([]);

  const log = useCallback((agentName: string, message: string, type: Activity['type'] = 'info') => {
    setActivities(prev => [
      { id: genId(), agentName, message, ts: Date.now(), type },
      ...prev,
    ].slice(0, 50));
  }, []);

  const setStatus = useCallback((id: string, status: AgentStatus, message?: string) => {
    setAgents(prev => prev.map(a => a.id === id ? { ...a, status, message } : a));
  }, []);

  const resetAll = useCallback(() => {
    timeoutsRef.current.forEach(t => clearTimeout(t));
    timeoutsRef.current = [];
    setAgents(initialAgents);
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

  return { agents, activities, trigger, log };
}
