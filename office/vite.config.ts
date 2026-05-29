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
// /api/chat 에서 시스템 프롬프트로 쓸 수 있는 에이전트 (화이트리스트 — 경로 traversal 방지)
const ALLOWED_AGENTS = new Set([
  'hyds-director',
  'retreat-planner', 'retreat-monitor', 'report-summarizer', 'content-creator', 'church-communicator',
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

// 부장이 위임할 수 있는 워커 (director 자신은 제외)
const WORKER_AGENTS = new Set([...ALLOWED_AGENTS].filter(a => a !== 'hyds-director'));

// 부장 plan JSON 파싱 (코드펜스/잡텍스트 방어)
function parsePlan(raw: string): { plan: Array<{ agent: string; task: string }>; reasoning: string; answer: string } {
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
          .filter((p: any) => p && WORKER_AGENTS.has(p.agent) && typeof p.task === 'string' && p.task.trim())
          .map((p: any) => ({ agent: p.agent as string, task: String(p.task).trim() }))
      : [];
    return { plan, reasoning: String(obj.reasoning || ''), answer: String(obj.answer || '') };
  } catch {
    return { plan: [], reasoning: '', answer: raw };
  }
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

      // 3) Claude 채팅 — 부장 오케스트레이션 (SSE 스트리밍)
      server.middlewares.use('/api/chat', async (req, res) => {
        const r = res as ServerResponse;
        if (req.method !== 'POST') return sendJson(r, 405, { error: 'POST만 허용' });
        const body = await readJsonBody(req);
        const text = typeof body.text === 'string' ? body.text.trim() : '';
        if (!text) return sendJson(r, 400, { error: '메시지가 비었습니다' });

        r.statusCode = 200;
        r.setHeader('Content-Type', 'text/event-stream; charset=utf-8');
        r.setHeader('Cache-Control', 'no-cache, no-transform');
        r.setHeader('Connection', 'keep-alive');
        const send = (obj: unknown) => r.write(`data: ${JSON.stringify(obj)}\n\n`);

        try {
          send({ phase: 'planning' });

          // 1) 부장: 작업 분해 (JSON 강제)
          const directorSystem = await loadAgentSystem('hyds-director');
          const planInstruction =
            '\n\n[출력 형식 — 아래 JSON만 출력, 다른 텍스트 금지]\n' +
            '{"plan":[{"agent":"retreat-planner|retreat-monitor|report-summarizer|content-creator|church-communicator","task":"구체적 작업"}],' +
            '"reasoning":"분해 이유 한 줄","answer":"plan이 빈 배열일 때만 대표에게 직접 답"}\n' +
            '규칙: 여러 영역이 얽히면 plan에 여러 개, 단일 작업이면 1개, 단순 조회·인사·잡담이면 plan:[] 이고 answer에 직접 답한다.';
          const planRaw = await callClaude(directorSystem + planInstruction, text, 900);
          const parsed = parsePlan(planRaw);
          send({ phase: 'plan-ready', plan: parsed.plan, reasoning: parsed.reasoning });

          // 단순 조회 → 즉답 (위임 없음)
          if (parsed.plan.length === 0) {
            send({ phase: 'complete', reply: parsed.answer || planRaw });
            return r.end();
          }

          // 2) 위임 통보
          send({ phase: 'delegating', plan: parsed.plan });

          // 3) 워커 병렬 실행 — 각 완료 시 worker-done
          const results = await Promise.all(parsed.plan.map(async item => {
            try {
              const sys = await loadAgentSystem(item.agent);
              const reply = await callClaude(sys, item.task, 1024);
              send({ phase: 'worker-done', agent: item.agent, task: item.task, result: reply });
              return { ...item, result: reply };
            } catch (e) {
              const msg = `(실패: ${String((e as Error).message || e)})`;
              send({ phase: 'worker-done', agent: item.agent, task: item.task, result: msg, error: true });
              return { ...item, result: msg };
            }
          }));

          // 4) 부장 종합
          send({ phase: 'synthesizing' });
          const synthSystem = directorSystem +
            '\n\n[종합 지시] 아래는 각 팀장이 제출한 결과다. 대표에게 한 페이지로 종합 보고하라. ' +
            '결론 먼저, 그다음 팀장별 핵심, 마지막에 다음 액션 제안.';
          const synthUser = `원 요청: ${text}\n\n` +
            results.map(w => `### ${w.agent} — ${w.task}\n${w.result}`).join('\n\n');
          const finalReply = await callClaude(synthSystem, synthUser, 1500);

          send({ phase: 'complete', reply: finalReply });
          r.end();
        } catch (e) {
          send({ phase: 'error', error: String((e as Error).message || e) });
          r.end();
        }
      });
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
