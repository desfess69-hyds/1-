import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath, URL } from 'node:url';
import { readFile, readFileSync } from 'node:fs';
import { readFile as readFileAsync } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import path from 'node:path';
import type { Plugin } from 'vite';
import type { IncomingMessage, ServerResponse } from 'node:http';

const ROOT = fileURLToPath(new URL('../', import.meta.url)); // HYDS 프로젝트 루트
const DATA_DIR = path.join(ROOT, 'data');
const PYTHON = path.join(ROOT, 'venv', 'bin', 'python');

// /api/run 으로 실행 허용된 스크립트 (화이트리스트 — 임의 파일 실행 방지)
const ALLOWED_SCRIPTS = new Set(['daily_monitor', 'realtime_check', 'generate_retreat_todos']);
// 부장(hyds-director)이 직접 위임할 수 있는 워커 (수련회 4팀장 + 미디어 본부장)
const DIRECTOR_WORKERS = new Set([
  'retreat-planner', 'retreat-monitor', 'report-summarizer', 'church-communicator',
  'media-director',
]);
// 미디어 본부장(media-director)이 다시 위임하는 팀장 4명 (trend-scout 가장 먼저)
const MEDIA_WORKERS = new Set(['trend-scout', 'concept-planner', 'scriptwriter', 'media-producer']);
// 트렌드 정찰이 필요한 작업을 감지하는 키워드 (있으면 trend-scout 가장 먼저).
// 릴스·쇼츠 단독은 '메시지 콘텐츠'일 수 있어 제외 — 트렌드성 단어만.
const TREND_RE = /트렌드|밈|챌린지|유행|CapCut|캡컷|MZ|Y2K|바이럴|짤/i;
// /api/chat 에서 시스템 프롬프트로 쓸 수 있는 에이전트 (화이트리스트 — 경로 traversal 방지)
const ALLOWED_AGENTS = new Set([
  'hyds-director',
  ...DIRECTOR_WORKERS,
  ...MEDIA_WORKERS,
]);

// ── 부모 폴더 .env 로드 (dotenv 대체 — 의존성 없이 동일 동작) ──────────────────
function loadParentEnv() {
  try {
    const raw = readFileSync(path.join(ROOT, '.env'), 'utf-8');
    for (const line of raw.split('\n')) {
      const t = line.trim();
      if (!t || t.startsWith('#')) continue;
      const eq = t.indexOf('=');
      if (eq === -1) continue;
      const key = t.slice(0, eq).trim();
      let val = t.slice(eq + 1).trim();
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
        val = val.slice(1, -1);
      }
      if (!(key in process.env)) process.env[key] = val; // 기존 env 우선
    }
  } catch {
    // .env 없으면 무시
  }
}
loadParentEnv();

function sendJson(res: ServerResponse, status: number, body: unknown) {
  res.statusCode = status;
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Cache-Control', 'no-store');
  res.end(JSON.stringify(body));
}

function readJsonBody(req: IncomingMessage): Promise<any> {
  return new Promise(resolve => {
    let data = '';
    req.on('data', c => (data += c));
    req.on('end', () => {
      try { resolve(JSON.parse(data || '{}')); } catch { resolve({}); }
    });
    req.on('error', () => resolve({}));
  });
}

// execution/{script}.py 를 venv 파이썬으로 실행, stdout/stderr 수집
function runScript(script: string): Promise<{ code: number; stdout: string; stderr: string }> {
  return new Promise(resolve => {
    const child = spawn(PYTHON, [`execution/${script}.py`], { cwd: ROOT });
    let stdout = '';
    let stderr = '';
    const timer = setTimeout(() => {
      child.kill('SIGKILL');
      stderr += '\n[시간 초과 — 200초]';
    }, 200_000);
    child.stdout.on('data', d => (stdout += d.toString()));
    child.stderr.on('data', d => (stderr += d.toString()));
    child.on('error', e => { clearTimeout(timer); resolve({ code: -1, stdout, stderr: stderr + String(e) }); });
    child.on('close', code => { clearTimeout(timer); resolve({ code: code ?? -1, stdout, stderr }); });
  });
}

// .claude/agents/{agent}.md 의 frontmatter 제거한 본문을 시스템 프롬프트로
async function loadAgentSystem(agent: string): Promise<string> {
  if (!ALLOWED_AGENTS.has(agent)) return '';
  try {
    const raw = await readFileAsync(path.join(ROOT, '.claude', 'agents', `${agent}.md`), 'utf-8');
    const m = raw.match(/^---\n[\s\S]*?\n---\n?/);
    return (m ? raw.slice(m[0].length) : raw).trim();
  } catch {
    return '';
  }
}

async function callClaude(system: string, text: string, maxTokens = 1024): Promise<string> {
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) throw new Error('ANTHROPIC_API_KEY 가 .env에 없습니다');
  const model = process.env.ANTHROPIC_MODEL || 'claude-sonnet-4-5';
  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-api-key': key,
      'anthropic-version': '2023-06-01',
    },
    body: JSON.stringify({
      model,
      max_tokens: maxTokens,
      ...(system ? { system } : {}),
      messages: [{ role: 'user', content: text }],
    }),
  });
  if (!res.ok) {
    const t = await res.text();
    throw new Error(`Claude API ${res.status}: ${t.slice(0, 200)}`);
  }
  const data = (await res.json()) as { content?: Array<{ type: string; text?: string }> };
  return (data.content ?? []).filter(b => b.type === 'text').map(b => b.text ?? '').join('').trim();
}

// plan JSON 파싱 (코드펜스/잡텍스트 방어). allowed: 그 단계에서 위임 가능한 에이전트 집합
function parsePlan(raw: string, allowed: Set<string>): { plan: Array<{ agent: string; task: string }>; reasoning: string; answer: string } {
  let s = (raw || '').trim();
  const fence = s.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (fence) s = fence[1].trim();
  const first = s.indexOf('{');
  const last = s.lastIndexOf('}');
  if (first !== -1 && last !== -1) s = s.slice(first, last + 1);
  try {
    const obj = JSON.parse(s);
    const plan = Array.isArray(obj.plan)
      ? obj.plan
          .filter((p: any) => p && allowed.has(p.agent) && typeof p.task === 'string' && p.task.trim())
          .map((p: any) => ({ agent: p.agent as string, task: String(p.task).trim() }))
      : [];
    return { plan, reasoning: String(obj.reasoning || ''), answer: String(obj.answer || '') };
  } catch {
    return { plan: [], reasoning: '', answer: raw };
  }
}

// ── 미디어 본부 (media-director) 2단계 위임 ────────────────────────────────
// 부장이 'media-director'에게 위임한 작업을, 본부장이 다시 concept/script/producer에
// 분배·종합한다. 반환값(종합 결과)이 부장의 worker-done.result 가 된다.
async function runMediaHQ(task: string, send: (obj: unknown) => void): Promise<string> {
  const dirSystem = await loadAgentSystem('media-director');
  const subInstruction =
    '\n\n[출력 형식 — 아래 JSON만 출력, 다른 텍스트 금지]\n' +
    '{"plan":[{"agent":"trend-scout|concept-planner|scriptwriter|media-producer","task":"구체적 작업(맥락을 충분히 녹여 자기완결적으로)"}],' +
    '"reasoning":"분배 이유 한 줄","answer":"plan이 빈 배열일 때만 부장에게 직접 답"}\n' +
    '규칙: 트렌드·밈·챌린지·유행·CapCut 요소가 있으면 trend-scout를 plan 맨 앞에 둔다(가장 먼저 실행). ' +
    '의존순서 trend-scout(트렌드 정찰) → concept-planner(전략·톤) → scriptwriter(카피) → media-producer(제작)를 지킨다. ' +
    '트렌드성 없는 메시지 콘텐츠는 trend-scout를 건너뛴다(비용 절감). ' +
    '캠페인·신규 콘텐츠면 여러 개, 카피만/이미지만이면 1개, 단순 질의면 plan:[] 이고 answer에 직접 답한다.';
  const raw = await callClaude(dirSystem + subInstruction, task, 900);
  const sub = parsePlan(raw, MEDIA_WORKERS);

  // 본부장이 직접 답하는 경우 (위임 불필요)
  if (sub.plan.length === 0) return sub.answer || raw;

  // 결정적 보정: task에 트렌드 키워드가 있는데 plan에 trend-scout가 없으면 맨 앞에 주입
  if (TREND_RE.test(task) && !sub.plan.some(p => p.agent === 'trend-scout')) {
    sub.plan.unshift({ agent: 'trend-scout', task: `다음 작업에 쓸 트렌드 정찰(CapCut 검색어·적용 방안): ${task}` });
  }
  // trend-scout 는 항상 맨 앞 → 가장 먼저 실행, 결과를 나머지 팀장에게 컨텍스트로 전달
  const trendSteps = sub.plan.filter(p => p.agent === 'trend-scout');
  const restSteps = sub.plan.filter(p => p.agent !== 'trend-scout');
  const ordered = [...trendSteps, ...restSteps];

  // 본부장이 자기 회의실로 팀장 소집 (trend-scout 먼저 표시)
  send({ phase: 'sub-delegating', director: 'media-director', plan: ordered, reasoning: sub.reasoning });

  // 팀장 한 명 실행 (extraContext: trend-scout 브리프를 다운스트림에 주입. 표시용 task는 원본 유지)
  const runOne = async (item: { agent: string; task: string }, extraContext = '') => {
    try {
      const sys = await loadAgentSystem(item.agent);
      const userText = extraContext
        ? `${item.task}\n\n[trend-scout 트렌드 브리프 — 반영할 것]\n${extraContext}`
        : item.task;
      const reply = await callClaude(sys, userText, 1024);
      send({ phase: 'sub-worker-done', director: 'media-director', agent: item.agent, task: item.task, result: reply });
      return { ...item, result: reply, ok: true };
    } catch (e) {
      const msg = `(실패: ${String((e as Error).message || e)})`;
      send({ phase: 'sub-worker-done', director: 'media-director', agent: item.agent, task: item.task, result: msg, error: true });
      return { ...item, result: msg, ok: false };
    }
  };

  // 1) trend-scout 먼저 순차 실행 → 트렌드 브리프 확보 (성공분만)
  const trendResults = [];
  for (const step of trendSteps) trendResults.push(await runOne(step));
  const trendBrief = trendResults.filter(r => r.ok).map(r => r.result).join('\n\n');

  // 2) 나머지 팀장은 트렌드 브리프를 컨텍스트로 받아 병렬 실행
  const restResults = await Promise.all(restSteps.map(item => runOne(item, trendBrief)));

  const subResults = [...trendResults, ...restResults];

  // 본부장 종합 (톤·메시지 일관성 검수)
  const synthSystem = dirSystem +
    '\n\n[종합 지시] 아래는 미디어 본부 팀장들의 결과다. 톤·핵심 메시지·디자인 규칙의 일관성을 검수하고, ' +
    '부장에게 한 덩어리로 종합 보고하라. 결론 먼저, 그다음 팀장별 핵심, 마지막에 다음 액션 제안.';
  const synthUser = `미디어 본부 요청: ${task}\n\n` +
    subResults.map(w => `### ${w.agent} — ${w.task}\n${w.result}`).join('\n\n');
  return await callClaude(synthSystem, synthUser, 1400);
}

// ── 대화 세션 (인메모리, 서버 재시작 시 초기화) ────────────────────────────────
interface ChatMsg { role: 'user' | 'assistant'; content: string }
interface ChatSession { messages: ChatMsg[]; lastActive: number }
const SESSIONS = new Map<string, ChatSession>();
const SESSION_TTL_MS = 60 * 60 * 1000;   // 60분 idle 만료
const MAX_TURNS = 50;                     // 세션당 최대 50턴 (초과 시 오래된 것부터 제거)
const MAX_CONTEXT_CHARS = 24000;          // 누적이 이보다 길면 새 대화 권유

function getSession(id: string): ChatSession {
  let s = SESSIONS.get(id);
  if (!s) { s = { messages: [], lastActive: Date.now() }; SESSIONS.set(id, s); }
  s.lastActive = Date.now();
  return s;
}
function cleanupSessions() {
  const now = Date.now();
  for (const [id, s] of SESSIONS) {
    if (now - s.lastActive > SESSION_TTL_MS) SESSIONS.delete(id);
  }
}

// 히스토리를 포함한 Claude 호출 (부장 전용 — 워커는 stateless callClaude 사용)
async function callClaudeMessages(system: string, messages: ChatMsg[], maxTokens = 1024): Promise<string> {
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) throw new Error('ANTHROPIC_API_KEY 가 .env에 없습니다');
  const model = process.env.ANTHROPIC_MODEL || 'claude-sonnet-4-5';
  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'x-api-key': key, 'anthropic-version': '2023-06-01' },
    body: JSON.stringify({ model, max_tokens: maxTokens, ...(system ? { system } : {}), messages }),
  });
  if (!res.ok) { const t = await res.text(); throw new Error(`Claude API ${res.status}: ${t.slice(0, 200)}`); }
  const data = (await res.json()) as { content?: Array<{ type: string; text?: string }> };
  return (data.content ?? []).filter(b => b.type === 'text').map(b => b.text ?? '').join('').trim();
}

// HYDS Python 자동화 data/*.json 실시간 노출 + 스크립트 실행 + Claude 채팅 API
function hydsBackendPlugin(): Plugin {
  function readJsonFile(file: string): Promise<unknown> {
    return new Promise(resolve => {
      readFile(path.join(DATA_DIR, file), 'utf-8', (err, data) => {
        if (err) return resolve(null);
        try { resolve(JSON.parse(data)); } catch { resolve(null); }
      });
    });
  }

  return {
    name: 'hyds-backend',
    configureServer(server) {
      // 1) 실데이터 상태
      server.middlewares.use('/api/hyds-state', async (_req, res) => {
        const [monitorLog, realtime, weeklyLog] = await Promise.all([
          readJsonFile('monitor_log.json'),
          readJsonFile('realtime_state.json'),
          readJsonFile('weekly_todos_log.json'),
        ]);
        sendJson(res as ServerResponse, 200, {
          monitorLog: Array.isArray(monitorLog) ? monitorLog : [],
          realtime: realtime ?? null,
          weeklyLog: Array.isArray(weeklyLog) ? weeklyLog : [],
        });
      });

      // 2) Python 스크립트 실행
      server.middlewares.use('/api/run', async (req, res) => {
        if (req.method !== 'POST') return sendJson(res as ServerResponse, 405, { error: 'POST만 허용' });
        const script = (req.url || '').replace(/^\//, '').split('?')[0];
        if (!ALLOWED_SCRIPTS.has(script)) {
          return sendJson(res as ServerResponse, 400, { error: `허용되지 않은 스크립트: ${script}` });
        }
        const result = await runScript(script);
        sendJson(res as ServerResponse, 200, {
          ok: result.code === 0,
          code: result.code,
          stdout: result.stdout,
          stderr: result.stderr,
        });
      });

      // 3) 세션 초기화 (반드시 /api/chat 보다 먼저 등록)
      server.middlewares.use('/api/chat/reset', async (req, res) => {
        const r = res as ServerResponse;
        if (req.method !== 'POST') return sendJson(r, 405, { error: 'POST만 허용' });
        const body = await readJsonBody(req);
        const sid = typeof body.sessionId === 'string' ? body.sessionId : '';
        if (sid) SESSIONS.delete(sid);
        sendJson(r, 200, { ok: true });
      });

      // 4) Claude 채팅 — 부장 오케스트레이션 (SSE 스트리밍 + 세션 메모리)
      server.middlewares.use('/api/chat', async (req, res) => {
        const r = res as ServerResponse;
        if (req.method !== 'POST') return sendJson(r, 405, { error: 'POST만 허용' });
        const body = await readJsonBody(req);
        const text = typeof body.text === 'string' ? body.text.trim() : '';
        const sessionId = typeof body.sessionId === 'string' && body.sessionId ? body.sessionId : 'default';
        if (!text) return sendJson(r, 400, { error: '메시지가 비었습니다' });

        const session = getSession(sessionId);

        r.statusCode = 200;
        r.setHeader('Content-Type', 'text/event-stream; charset=utf-8');
        r.setHeader('Cache-Control', 'no-cache, no-transform');
        r.setHeader('Connection', 'keep-alive');
        const send = (obj: unknown) => r.write(`data: ${JSON.stringify(obj)}\n\n`);
        const turns = () => Math.floor(session.messages.length / 2);

        // 안전장치: 대화가 너무 길면 Claude 호출 없이 새 대화 권유
        const contextChars = session.messages.reduce((n, m) => n + m.content.length, 0) + text.length;
        if (contextChars > MAX_CONTEXT_CHARS) {
          send({ phase: 'planning' });
          send({
            phase: 'complete',
            reply: '대화가 많이 길어졌습니다 🙏 맥락이 흐려질 수 있으니 상단 "🆕 새 대화"로 다시 시작하시는 걸 권합니다.',
            turns: turns(),
          });
          return r.end();
        }

        try {
          send({ phase: 'planning' });

          // 1) 부장: 작업 분해 (히스토리 포함, JSON 강제)
          const directorSystem = await loadAgentSystem('hyds-director');
          const planInstruction =
            '\n\n[출력 형식 — 아래 JSON만 출력, 다른 텍스트 금지]\n' +
            '{"plan":[{"agent":"retreat-planner|retreat-monitor|report-summarizer|church-communicator|media-director","task":"구체적 작업(이전 대화 맥락을 task에 충분히 녹여 자기완결적으로)"}],' +
            '"reasoning":"분해 이유 한 줄","answer":"plan이 빈 배열일 때만 대표에게 직접 답"}\n' +
            '규칙: 수련회(기획·점검·리포트·교회답변)는 해당 팀장에게 직접 위임한다. ' +
            '미디어(카드뉴스·릴스·영상·홍보·캡션·캠페인·콘텐츠 전략·트렌드·밈·챌린지·유행·CapCut·MZ·Y2K)는 쪼개지 말고 "media-director"에게 통째로 한 건으로 위임한다(본부장이 산하 4팀장에 재분배, 트렌드면 trend-scout가 가장 먼저). ' +
            '여러 영역이 얽히면 plan에 여러 개, 단일 작업이면 1개, 단순 조회·인사·되묻기면 plan:[] 이고 answer에 직접 답한다. 정보가 부족하면 plan:[] 로 두고 answer에 필요한 정보를 되물어라.';
          const planMsgs: ChatMsg[] = [...session.messages, { role: 'user', content: text }];
          const planRaw = await callClaudeMessages(directorSystem + planInstruction, planMsgs, 900);
          const parsed = parsePlan(planRaw, DIRECTOR_WORKERS);
          send({ phase: 'plan-ready', plan: parsed.plan, reasoning: parsed.reasoning });

          let finalReply: string;

          if (parsed.plan.length === 0) {
            // 즉답/되묻기 (위임 없음)
            finalReply = parsed.answer || planRaw;
            send({ phase: 'complete', reply: finalReply, turns: turns() + 1 });
          } else {
            // 2) 위임 통보
            send({ phase: 'delegating', plan: parsed.plan });

            // 3) 워커 병렬 실행 (stateless) — 각 완료 시 worker-done
            //    media-director 는 leaf 가 아니라 본부 2단계 위임(runMediaHQ)으로 처리
            const results = await Promise.all(parsed.plan.map(async item => {
              try {
                const reply = item.agent === 'media-director'
                  ? await runMediaHQ(item.task, send)
                  : await callClaude(await loadAgentSystem(item.agent), item.task, 1024);
                send({ phase: 'worker-done', agent: item.agent, task: item.task, result: reply });
                return { ...item, result: reply };
              } catch (e) {
                const msg = `(실패: ${String((e as Error).message || e)})`;
                send({ phase: 'worker-done', agent: item.agent, task: item.task, result: msg, error: true });
                return { ...item, result: msg };
              }
            }));

            // 4) 부장 종합 (히스토리 포함)
            send({ phase: 'synthesizing' });
            const synthSystem = directorSystem +
              '\n\n[종합 지시] 아래는 각 팀장이 제출한 결과다. 대표에게 한 페이지로 종합 보고하라. ' +
              '결론 먼저, 그다음 팀장별 핵심, 마지막에 다음 액션 제안.';
            const synthUser = `원 요청: ${text}\n\n` +
              results.map(w => `### ${w.agent} — ${w.task}\n${w.result}`).join('\n\n');
            const synthMsgs: ChatMsg[] = [...session.messages, { role: 'user', content: synthUser }];
            finalReply = await callClaudeMessages(synthSystem, synthMsgs, 1500);
            send({ phase: 'complete', reply: finalReply, turns: turns() + 1 });
          }

          // 세션에 종합본만 기록 (워커 raw 제외), 50턴 초과 시 오래된 것부터 제거
          session.messages.push({ role: 'user', content: text }, { role: 'assistant', content: finalReply });
          const maxMsgs = MAX_TURNS * 2;
          if (session.messages.length > maxMsgs) {
            session.messages.splice(0, session.messages.length - maxMsgs);
          }
          session.lastActive = Date.now();
          r.end();
        } catch (e) {
          send({ phase: 'error', error: String((e as Error).message || e) });
          r.end();
        }
      });

      // 만료 세션 정리 (10분마다)
      const cleanupTimer = setInterval(cleanupSessions, 10 * 60 * 1000);
      if (typeof cleanupTimer.unref === 'function') cleanupTimer.unref();
    },
  };
}

export default defineConfig({
  plugins: [react(), hydsBackendPlugin()],
  server: {
    port: 5173,
    fs: {
      allow: ['..'],
    },
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '@hyds': fileURLToPath(new URL('../', import.meta.url)),
    },
  },
});
