import { useState } from 'react';

interface Props {
  onSend: (text: string) => void;
  disabled: boolean;
}

export function ChatBox({ onSend, disabled }: Props) {
  const [value, setValue] = useState('');

  const submit = () => {
    const t = value.trim();
    if (!t || disabled) return;
    onSend(t);
    setValue('');
  };

  return (
    <div className="bg-white/60 backdrop-blur-sm border-2 border-amber-200 rounded-2xl p-3 shadow-md">
      <div className="text-amber-900 text-sm mb-2 korean font-bold flex items-center gap-2">
        <span>💬</span> 에이전트에게 명령
        {disabled && <span className="text-[10px] text-amber-600 korean font-normal">· 처리 중...</span>}
      </div>
      <div className="flex gap-2">
        <input
          type="text"
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') submit(); }}
          disabled={disabled}
          placeholder="에이전트에게 명령하세요... 예: '평택교회 카드뉴스 8장 만들어줘'"
          className="flex-1 bg-white/80 border border-amber-200 rounded-xl px-3 py-2 text-sm korean text-amber-900 placeholder:text-amber-400/70 focus:outline-none focus:ring-2 focus:ring-amber-300 disabled:opacity-50"
        />
        <button
          onClick={submit}
          disabled={disabled}
          className="bg-gradient-to-br from-amber-200 to-orange-200 hover:scale-105 active:scale-95 transition-all px-4 py-2 rounded-xl border border-white/80 text-sm text-amber-900 korean font-semibold shadow-sm disabled:opacity-50 disabled:hover:scale-100"
        >
          전송
        </button>
      </div>
      <div className="text-[10px] text-amber-600/70 korean mt-1.5">
        부장이 요청을 분석해 팀장들에게 자동 위임합니다 · 복합 요청은 여러 팀장이 병렬로 일해요
      </div>
    </div>
  );
}
