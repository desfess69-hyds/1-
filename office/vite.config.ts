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

async function callClaude(system: string, text: string): Promise<string> {
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
      max_tokens: 1024,
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

      // 3) Claude 채팅
      server.middlewares.use('/api/chat', async (req, res) => {
        if (req.method !== 'POST') return sendJson(res as ServerResponse, 405, { error: 'POST만 허용' });
        const body = await readJsonBody(req);
        const text = typeof body.text === 'string' ? body.text.trim() : '';
        const agent = typeof body.agent === 'string' ? body.agent : '';
        if (!text) return sendJson(res as ServerResponse, 400, { error: '메시지가 비었습니다' });
        try {
          const system = await loadAgentSystem(agent);
          const reply = await callClaude(system, text);
          sendJson(res as ServerResponse, 200, { reply, agent });
        } catch (e) {
          sendJson(res as ServerResponse, 500, { error: String((e as Error).message || e) });
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
