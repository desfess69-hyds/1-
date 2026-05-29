import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath, URL } from 'node:url';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import type { Plugin } from 'vite';

// HYDS Python 자동화가 갱신하는 data/*.json 을 실시간으로 노출하는 작은 API.
// 요청이 올 때마다 디스크에서 새로 읽으므로, cron/launchd가 파일을 갱신하면 즉시 반영됨.
function hydsDataPlugin(): Plugin {
  const dataDir = fileURLToPath(new URL('../data/', import.meta.url));

  async function readJson(file: string) {
    try {
      return JSON.parse(await readFile(path.join(dataDir, file), 'utf-8'));
    } catch {
      return null; // 파일이 아직 없거나 쓰는 중이면 null
    }
  }

  return {
    name: 'hyds-data-api',
    configureServer(server) {
      server.middlewares.use('/api/hyds-state', async (_req, res) => {
        const [monitorLog, realtime, weeklyLog] = await Promise.all([
          readJson('monitor_log.json'),
          readJson('realtime_state.json'),
          readJson('weekly_todos_log.json'),
        ]);
        res.setHeader('Content-Type', 'application/json');
        res.setHeader('Cache-Control', 'no-store');
        res.end(
          JSON.stringify({
            monitorLog: Array.isArray(monitorLog) ? monitorLog : [],
            realtime: realtime ?? null,
            weeklyLog: Array.isArray(weeklyLog) ? weeklyLog : [],
          }),
        );
      });
    },
  };
}

export default defineConfig({
  plugins: [react(), hydsDataPlugin()],
  server: {
    port: 5173,
    fs: {
      // HYDS 폴더 상위 접근 허용 (data/ 파일 fetch 위해)
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
