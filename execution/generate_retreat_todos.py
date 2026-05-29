"""
HYDS 활성 수련회 × 마스터 체크리스트 → 교회별 맞춤 To-Do 생성.

각 수련회마다:
1. 현재 진행 상황 (DB 체크리스트 + 보고서) 분석
2. 마스터 체크리스트(66개 항목)와 비교
3. D-day 기준 우선순위 정렬
4. Claude로 컨텍스트 맞춤 코멘트
→ 깔끔한 .docx 1개 파일 + 텔레그램 발송

사용 예:
    python execution/generate_retreat_todos.py
    python execution/generate_retreat_todos.py --no-send
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from execution.db_client import list_active_retreats, get_retreat_full
from execution.claude_client import ask_claude

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT = PROJECT_ROOT / ".tmp" / "dossiers" / f"HYDS_수련회별_TODO_{datetime.now().strftime('%Y%m%d')}.docx"
KOREAN_FONT = "Apple SD Gothic Neo"

# ──────────────────────────────────────────────────────────
# 마스터 체크리스트 (D-day별로 카테고리화)
# ──────────────────────────────────────────────────────────
MASTER_CHECKLIST = {
    "D-90 이전": [
        "교회 측과 zoom 첫 소통, Needs 파악",
        "HYDS 본부에 교회 Needs 전달·정리",
    ],
    "D-90 ~ D-60": [
        "팀원 모집 + 예배·프로그램·안전 팀장 세움",
        "장소 답사 (팀장 + 가능한 팀원)",
        "참가 신청 폼 오픈",
        "보험 견적 받기 (50명 이상 시 필수)",
        "사진·영상 담당자 별도 지정",
    ],
    "D-60 ~ D-30": [
        "기획서 교회 측 최종 승인 (서면)",
        "1차 카드뉴스/포스터 홍보",
        "강사 확정 + 사례비/숙소/교통비 서면",
        "장소 잔금 일정 확정",
        "음향 기기 점검 (예비 1세트 포함)",
    ],
    "D-30 ~ D-14": [
        "참가자 50% 이상 모집",
        "보험 가입 완료",
        "식사·교통 업체 계약 확정",
        "찬양곡 리스트 + 코드/악보 공유",
        "단톡방 개설 + 공지 매뉴얼",
    ],
    "D-14 ~ D-7": [
        "참가자 명단 최종 확정",
        "알레르기·복용약·지병 수합",
        "비상연락망 (강사·교회·병원·119)",
        "방·조 배정표 사전 공유",
        "이름표/조끼 인쇄",
        "음향 리허설 일정 확정",
    ],
    "D-7 ~ D-1": [
        "짐 패킹 리스트 점검",
        "현장 답사 또는 도착 후 즉시 점검",
        "스태프 R&R 최종 확정",
        "응급의료 키트 준비",
        "사고 대응 매뉴얼 팀장 숙지",
    ],
    "당일": [
        "강사 도착 확인",
        "음향·영상 리허설",
        "응급의약품·구급함 위치 공지",
        "단체 사진 시간 진행",
    ],
    "사후 (D+1 ~ D+14)": [
        "사례비·정산 마감",
        "참가자 설문 발송 (D+3 이내)",
        "결산 보고 교회에 (D+7 이내)",
        "강사·장소·진행 후기 HYDS 데이터에 반영",
        "다음 기획에 적용할 교훈 메모",
        "참가자·교회 감사 인사",
    ],
}

# 어떤 D-day 카테고리들이 "지금" 활성인지 매핑
def active_categories(days_until: int) -> tuple[list[str], list[str], list[str]]:
    """현재 진행해야 할 / 다음 단계 / 이후 단계 분류."""
    all_cats = list(MASTER_CHECKLIST.keys())
    if days_until is None:
        return all_cats, [], []

    if days_until > 90: idx = 0
    elif days_until > 60: idx = 1
    elif days_until > 30: idx = 2
    elif days_until > 14: idx = 3
    elif days_until > 7: idx = 4
    elif days_until > 1: idx = 5
    elif days_until >= 0: idx = 6
    else: idx = 7

    # 지금 해야 할 것: 현재 idx 이전(놓친 것) + 현재
    now = all_cats[: idx + 1]
    nxt = all_cats[idx + 1: idx + 2]
    later = all_cats[idx + 2:]
    return now, nxt, later


def analyze_retreat(retreat: dict) -> dict:
    """수련회 1건의 현황을 분석하고 To-Do를 생성."""
    days_until = None
    if retreat.get("startAt"):
        days_until = (datetime.fromtimestamp(retreat["startAt"]/1000) - datetime.now()).days

    chk = retreat.get("checklist") or []
    total = len(chk)
    done = sum(1 for c in chk if c["isChecked"])
    progress = round(done / total * 100) if total else 0

    # 앱 체크리스트에서 이미 한 항목 추출
    done_titles = set(c["title"].strip() for c in chk if c["isChecked"])
    pending_titles = set(c["title"].strip() for c in chk if not c["isChecked"])

    # 최근 보고서에서 이슈 추출
    issues = []
    for r in (retreat.get("recent_reports") or [])[:3]:
        if r.get("issues"):
            issues.append(r["issues"].strip())
        for k in ["currentStatus", "teamStatus", "venueStatus"]:
            v = r.get(k)
            if v and any(kw in v for kw in ["없음", "안 됨", "지연", "취소", "문제"]):
                issues.append(f"[{k}] {v.strip()[:120]}")

    now, nxt, later = active_categories(days_until)

    # 지금 단계의 마스터 항목 중 앱에서 안 한 것
    todo_now = []
    for cat in now:
        for item in MASTER_CHECKLIST[cat]:
            # 단순 키워드 매칭으로 "이미 했나?" 추정
            already = any(any(kw in dt for kw in item.split()[:2]) for dt in done_titles)
            if not already:
                todo_now.append((cat, item))

    todo_next = []
    for cat in nxt:
        for item in MASTER_CHECKLIST[cat]:
            todo_next.append((cat, item))

    return {
        "retreat": retreat,
        "days_until": days_until,
        "progress": progress,
        "total": total,
        "done": done,
        "todo_now": todo_now[:15],   # 너무 길면 컷
        "todo_next": todo_next[:10],
        "issues": issues[:5],
        "pending_in_app": list(pending_titles)[:10],
    }


def get_ai_advice(analysis: dict) -> str:
    """Claude로 수련회 1건의 맞춤 조언 1~2문장."""
    r = analysis["retreat"]
    prompt = f"""HYDS의 수련회 매니저로서, 다음 수련회에 대해 가장 중요한 조언 1~2문장만 작성하세요.
(요약·격려·일반론 금지. 구체적 행동 1개를 명시.)

교회: {r.get('churchName')}
주제: {r.get('theme') or '미정'}
팀장: {r.get('teamLeader') or '미배정'}
D-day: D{'-' if analysis['days_until'] >= 0 else '+'}{abs(analysis['days_until'])}
진척률: {analysis['progress']}%
미해결 이슈: {'; '.join(analysis['issues'])[:200] or '없음'}
"""
    try:
        return ask_claude(prompt, max_tokens=200).strip()
    except Exception as e:
        return f"(AI 조언 생성 실패: {e})"


# ──────────────────────────────────────────────────────────
# DOCX 렌더링
# ──────────────────────────────────────────────────────────
def render_docx(analyses: list[dict]):
    try:
        from docx import Document
        from docx.shared import Pt, Cm, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement
    except ImportError:
        print("❌ python-docx 미설치: pip install python-docx")
        sys.exit(1)

    def set_font(run, font=KOREAN_FONT):
        run.font.name = font
        rPr = run._element.get_or_add_rPr()
        rFonts = rPr.find(qn("w:rFonts"))
        if rFonts is None:
            rFonts = OxmlElement("w:rFonts")
            rPr.append(rFonts)
        rFonts.set(qn("w:eastAsia"), font)
        rFonts.set(qn("w:ascii"), font)
        rFonts.set(qn("w:hAnsi"), font)

    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(1.8)
        section.bottom_margin = Cm(1.8)
        section.left_margin = Cm(2.0)
        section.right_margin = Cm(2.0)

    # 표지
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("HYDS 수련회별 To-Do 리스트")
    run.font.size = Pt(22); run.bold = True; set_font(run)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = sub.add_run(f"생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 분석 수련회: {len(analyses)}건")
    run.italic = True; run.font.size = Pt(10); set_font(run)
    doc.add_paragraph()

    # 한 줄 요약 표
    summary = doc.add_paragraph()
    run = summary.add_run("📊 전체 요약")
    run.bold = True; run.font.size = Pt(14); set_font(run)

    table = doc.add_table(rows=1 + len(analyses), cols=5)
    table.style = "Light Grid Accent 1"
    header = ["교회", "D-day", "진척률", "지금 할 일", "이슈"]
    for i, h in enumerate(header):
        c = table.rows[0].cells[i]
        c.text = ""
        rn = c.paragraphs[0].add_run(h)
        rn.bold = True; rn.font.size = Pt(10); set_font(rn)

    for idx, a in enumerate(analyses):
        r = a["retreat"]
        cells = table.rows[idx + 1].cells
        d = "?" if a["days_until"] is None else (f"D-{a['days_until']}" if a["days_until"] >= 0 else f"D+{-a['days_until']}")
        vals = [
            r.get("churchName") or "?",
            d,
            f"{a['progress']}%",
            f"{len(a['todo_now'])}개",
            f"{len(a['issues'])}건" if a["issues"] else "없음",
        ]
        for i, v in enumerate(vals):
            cells[i].text = ""
            rn = cells[i].paragraphs[0].add_run(str(v))
            rn.font.size = Pt(10); set_font(rn)

    doc.add_page_break()

    # 수련회별 상세 페이지
    for a in analyses:
        r = a["retreat"]
        # 헤더: 교회명 + D-day
        h = doc.add_paragraph()
        run = h.add_run(r.get("churchName") or "?")
        run.bold = True; run.font.size = Pt(18); set_font(run)

        d = "?" if a["days_until"] is None else (f"D-{a['days_until']}" if a["days_until"] >= 0 else f"D+{-a['days_until']}")
        meta = doc.add_paragraph()
        run = meta.add_run(f"주제: {r.get('theme') or '미정'} | 팀장: {r.get('teamLeader') or '미배정'} | {d} | 진척률 {a['progress']}% ({a['done']}/{a['total']})")
        run.font.size = Pt(10); run.italic = True; set_font(run)

        # AI 조언
        advice = doc.add_paragraph()
        adv_text = get_ai_advice(a)
        run = advice.add_run(f"🤖 AI 조언: ")
        run.bold = True; run.font.size = Pt(11); set_font(run)
        run = advice.add_run(adv_text)
        run.font.size = Pt(11); set_font(run)

        # 이슈
        if a["issues"]:
            head = doc.add_paragraph()
            run = head.add_run("⚠️ 발견된 이슈")
            run.bold = True; run.font.size = Pt(12); set_font(run)
            for issue in a["issues"]:
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Cm(0.5)
                run = p.add_run(f"• {issue}")
                run.font.size = Pt(10); set_font(run)

        # 지금 할 일
        head = doc.add_paragraph()
        run = head.add_run("🔴 지금 해야 할 To-Do (우선순위)")
        run.bold = True; run.font.size = Pt(12); run.font.color.rgb = RGBColor(0xC0, 0x00, 0x00); set_font(run)
        if a["todo_now"]:
            for cat, item in a["todo_now"]:
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Cm(0.5)
                run = p.add_run(f"☐  [{cat}] {item}")
                run.font.size = Pt(11); set_font(run)
        else:
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.5)
            run = p.add_run("(이 단계 항목 모두 완료 또는 추적 안 됨)")
            run.italic = True; run.font.size = Pt(10); set_font(run)

        # 앱에 등록된 미완료 항목
        if a["pending_in_app"]:
            head = doc.add_paragraph()
            run = head.add_run("📌 앱 체크리스트의 미완료 항목")
            run.bold = True; run.font.size = Pt(12); set_font(run)
            for item in a["pending_in_app"]:
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Cm(0.5)
                run = p.add_run(f"☐  {item}")
                run.font.size = Pt(10); set_font(run)

        # 다음 단계 미리보기
        if a["todo_next"]:
            head = doc.add_paragraph()
            run = head.add_run("🟡 다음 단계 미리보기")
            run.bold = True; run.font.size = Pt(11); run.font.color.rgb = RGBColor(0x80, 0x80, 0x00); set_font(run)
            for cat, item in a["todo_next"][:6]:
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Cm(0.5)
                run = p.add_run(f"○  [{cat}] {item}")
                run.font.size = Pt(10); set_font(run)

        doc.add_page_break()

    # 마지막 페이지 푸터
    foot = doc.add_paragraph()
    foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = foot.add_run("HYDS — 자동 생성 (매주 발송 가능)")
    run.italic = True; run.font.size = Pt(9); run.font.color.rgb = RGBColor(0x80, 0x80, 0x80); set_font(run)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    print(f"✅ 저장: {OUTPUT}")


def send_via_telegram():
    """텔레그램으로 문서 첨부."""
    import os, requests
    try:
        from dotenv import load_dotenv
        load_dotenv(PROJECT_ROOT / ".env")
    except ImportError:
        pass
    from execution.telegram_notify import send_telegram

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "").strip()

    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    summary = f"""<b>📋 HYDS 수련회별 To-Do ({today})</b>

각 교회 현황 분석 + D-day 우선순위 To-Do 정리.

→ 첨부 Word 파일 열어서 교회별 페이지 확인.
→ 매주 자동 발송 설정 가능."""

    send_telegram(summary)

    url = f"https://api.telegram.org/bot{token}/sendDocument"
    with open(OUTPUT, "rb") as f:
        files = {"document": (OUTPUT.name, f,
                              "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        data = {"chat_id": chat_id, "caption": "수련회별 To-Do (HYDS 자동 생성)", "parse_mode": "HTML"}
        res = requests.post(url, data=data, files=files, timeout=30)
        print("   ✅ 텔레그램 발송" if res.ok else f"   ❌ {res.text[:200]}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-send", action="store_true", help="docx만 만들고 텔레그램 안 보냄")
    args = parser.parse_args()

    print("📡 활성 수련회 조회...")
    summary = list_active_retreats()
    if not summary:
        print("   (활성 수련회 없음)")
        return

    print(f"   {len(summary)}건 분석 중 (각 건마다 Claude 호출 — 1~2분 소요)...")
    analyses = []
    for s in summary:
        full = get_retreat_full(s["id"])
        if full:
            analyses.append(analyze_retreat(full))
            print(f"   - {full.get('churchName')} (D-{analyses[-1]['days_until']}, 진척률 {analyses[-1]['progress']}%) — To-Do {len(analyses[-1]['todo_now'])}개")

    print("\n📝 Word 문서 생성...")
    render_docx(analyses)

    if not args.no_send:
        print("📤 텔레그램 발송...")
        send_via_telegram()
    else:
        print(f"\n파일만 생성됨: {OUTPUT}")


if __name__ == "__main__":
    main()
