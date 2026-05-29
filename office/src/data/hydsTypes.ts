// HYDS Python 자동화가 쓰는 실제 데이터 파일들의 타입.
// execution/daily_monitor.py 와 execution/realtime_check.py 가 갱신함.

export interface MonitorRun {
  date: string;
  ran_at: string; // ISO timestamp
  retreats_total: number;
  red_count: number;
  notified: boolean;
  report_path: string;
}

export interface RealtimeState {
  last_report_id: number;
  last_check_at: string; // ISO timestamp
  last_run_alerts?: number;
}

export interface WeeklyRun {
  date: string;
  ran_at: string; // ISO timestamp
  retreats_total: number;
  total_todos: number;
  notified: boolean;
  report_path: string;
}

export interface HydsState {
  monitorLog: MonitorRun[];
  realtime: RealtimeState | null;
  weeklyLog: WeeklyRun[];
}
