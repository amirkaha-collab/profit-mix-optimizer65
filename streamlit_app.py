from __future__ import annotations
# -*- coding: utf-8 -*-
# Profit Mix Optimizer – v3.0
# שיפורים v3.0:
# - פיצ׳ר 1: ייבוא דו"ח מסלקה (פורטפוליו קיים)
# - פיצ׳ר 2: כפתורי מסלול מהיר (מניות/אג"ח/חו"ל/ישראל/מט"ח)
# - פיצ׳ר 3: נעילת קרן עם סכום/משקל קבוע
# - פיצ׳ר 4: השוואת מצב מוצע מול מצב קיים בתוצאות

import itertools, math, os, re, html, io, traceback
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Profit Mix Optimizer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

import streamlit as _st_check
_st_version = tuple(int(x) for x in _st_check.__version__.split(".")[:2])

def _safe_plotly(fig, key=None):
    try:
        st.plotly_chart(fig, use_container_width=True, key=key)
    except TypeError:
        try:
            st.plotly_chart(fig, key=key)
        except TypeError:
            st.plotly_chart(fig)

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── Global RTL ── */
html, body, [class*="css"] { direction: rtl; text-align: right; font-family: 'Segoe UI', -apple-system, sans-serif; }
div[data-baseweb="slider"], div[data-baseweb="slider"] * { direction: ltr !important; }
section[data-testid="stSidebar"] { display: none !important; }
.block-container { padding: 0.6rem 1.2rem 2rem !important; max-width: 1200px; }
div[data-testid="stVerticalBlock"] { gap: 0.3rem; }

/* ── Premium Header ── */
.app-header {
  background: linear-gradient(135deg, #0f1e3d 0%, #1a3560 55%, #1e4080 100%);
  border-radius: 16px; padding: 20px 28px 16px;
  margin-bottom: 0; position: relative; overflow: hidden;
}
.app-header::before {
  content: ''; position: absolute; top: -30px; left: -30px;
  width: 180px; height: 180px;
  background: radial-gradient(circle, rgba(99,153,255,0.14) 0%, transparent 70%);
  pointer-events: none;
}
.app-logo { display: flex; align-items: center; gap: 12px; margin-bottom: 4px; }
.app-logo-icon {
  width: 40px; height: 40px;
  background: linear-gradient(135deg, #3b82f6, #60a5fa);
  border-radius: 10px; display: flex; align-items: center;
  justify-content: center; font-size: 20px; flex-shrink: 0;
  box-shadow: 0 3px 10px rgba(59,130,246,0.4);
}
.app-title { font-size: 22px; font-weight: 800; color: #f0f6ff; margin: 0; letter-spacing: -0.2px; }
.app-sub   { font-size: 12px; color: #93b4e0; margin: 2px 0 0; }
.app-header-stats { display: flex; gap: 14px; margin-top: 12px; flex-wrap: wrap; }
.header-stat {
  background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.13);
  border-radius: 8px; padding: 6px 14px; display: flex; flex-direction: column; align-items: center;
}
.header-stat .hval { font-size: 17px; font-weight: 800; color: #60a5fa; }
.header-stat .hlbl { font-size: 10px; color: #93b4e0; letter-spacing: 0.4px; }

/* ── Navigation pills (st.radio styled) ── */
.nav-bar { 
  background: #fff; border-radius: 0 0 14px 14px;
  padding: 8px 14px 6px; border: 1px solid #e2e8f0; border-top: none;
  margin-bottom: 12px;
}
div[role="radiogroup"] {
  display: flex !important; gap: 6px !important;
  flex-wrap: nowrap !important; overflow-x: auto;
  padding-bottom: 2px;
}
div[role="radiogroup"] label {
  display: inline-flex !important; align-items: center !important;
  padding: 6px 14px !important; border-radius: 999px !important;
  border: 1.5px solid #e2e8f0 !important; background: #f8fafc !important;
  font-size: 13px !important; font-weight: 600 !important;
  cursor: pointer !important; white-space: nowrap !important;
  color: #334155 !important; transition: all 0.15s !important;
  margin: 0 !important;
}
div[role="radiogroup"] label:hover { background: #eff6ff !important; border-color: #bfdbfe !important; color: #1e40af !important; }
div[role="radiogroup"] label:has(input:checked) {
  background: #1e3a8a !important; color: #ffffff !important;
  border-color: #1e3a8a !important; box-shadow: 0 2px 8px rgba(30,58,138,0.25) !important;
}
div[role="radiogroup"] input[type="radio"] { display: none !important; }
div[role="radiogroup"] p { margin: 0 !important; }

/* ── Profile section ── */
.profile-section {
  background: #f8faff; border: 1px solid #dbeafe;
  border-radius: 12px; padding: 10px 14px 8px; margin: 0 0 10px;
}
.profile-title { font-size: 13px; font-weight: 800; color: #1e3a8a; margin-bottom: 3px; }
.profile-hint  { font-size: 11px; color: #64748b; margin-bottom: 8px; }

/* ── Portfolio card ── */
.portfolio-card {
  border: 1px solid #e2e8f0; border-radius: 12px;
  padding: 12px 14px; background: #f0fdf4; margin-bottom: 12px;
}
.portfolio-card .ptitle { font-size: 13px; font-weight: 800; color: #166534; margin-bottom: 6px; }
.portfolio-card .prow   { display: flex; justify-content: space-between; padding: 2px 0; border-bottom: 1px dashed #d1fae5; font-size: 12px; }
.portfolio-card .prow:last-child { border-bottom: none; }
.portfolio-card .plabel { color: #374151; }
.portfolio-card .pval   { font-weight: 800; color: #166534; }

/* ── Compact settings ── */
.score-tip {
  background: #fffbeb; border: 1px solid #fde68a;
  border-radius: 8px; padding: 8px 12px;
  font-size: 12px; color: #78350f; margin: 6px 0;
}
.settings-section { margin-bottom: 8px; }

/* ── Results table ── */
.res-tbl { width: 100%; border-collapse: collapse; font-size: 12.5px; direction: rtl; }
.res-tbl th {
  background: #0f1e3d; color: #e2e8f0; padding: 8px 10px;
  text-align: center; white-space: nowrap; font-weight: 700; font-size: 11.5px;
}
.res-tbl th:first-child { text-align: right; min-width: 100px; }
.res-tbl th:nth-child(2) { text-align: right; min-width: 180px; }
.res-tbl td { padding: 8px 10px; border-bottom: 1px solid #f1f5f9; text-align: center; vertical-align: middle; }
.res-tbl td:first-child { text-align: right; }
.res-tbl td:nth-child(2) { text-align: right; }
.res-tbl tr:hover td { filter: brightness(0.97); }

/* ── Voting / alternative select buttons ── */
.vote-section {
  background: linear-gradient(135deg, #f8faff, #eff6ff);
  border: 1px solid #dbeafe; border-radius: 12px;
  padding: 14px 16px 12px; margin-top: 12px;
}
.vote-title { font-size: 13px; font-weight: 800; color: #1e3a8a; margin-bottom: 4px; }
.vote-sub   { font-size: 11px; color: #64748b; margin-bottom: 10px; }
.voted-badge {
  display: inline-block; background: #dcfce7; color: #065f46;
  border-radius: 999px; padding: 6px 16px; font-size: 13px; font-weight: 700;
}

/* ── Stats dialog ── */
.stat-bar-wrap { display: flex; align-items: center; gap: 10px; margin: 5px 0; direction: rtl; }
.stat-bar { height: 16px; border-radius: 4px; min-width: 4px; transition: width 0.3s; }

/* ── Change badges ── */
.change-badge { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.change-low  { background: #dcfce7; color: #166534; }
.change-med  { background: #fef3c7; color: #92400e; }
.change-high { background: #fee2e2; color: #991b1b; }

/* ── Comparison table (fund comparison tab) ── */
.cmp-table {
  width: 100%; border-collapse: separate; border-spacing: 0;
  border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;
  font-size: 13px; direction: rtl; margin-top: 4px;
}
.cmp-table th {
  background: #0f172a; color: #f8fafc; padding: 9px 11px;
  font-weight: 700; white-space: nowrap; text-align: right;
}
.cmp-table td {
  padding: 8px 11px; border-bottom: 1px solid #f1f5f9;
  text-align: right; vertical-align: middle;
}
.cmp-table tr:last-child td { border-bottom: none; }
.cmp-table tr:hover td { filter: brightness(0.97); }

/* ── History badge ── */
.hist-badge { display: inline-block; font-size: 11px; padding: 2px 8px; border-radius: 999px; background: #dbeafe; color: #1e40af; margin-left: 6px; }

/* ── Password screen ── */
.pw-wrap  { max-width: 320px; margin: 50px auto; text-align: center; }
.pw-title { font-size: 24px; font-weight: 800; margin-bottom: 4px; }
.pw-sub   { font-size: 13px; opacity: 0.7; margin-bottom: 16px; }
.pw-warn  { font-size: 11px; color: #b45309; background: #fef3c7; border-radius: 6px; padding: 5px 10px; margin-top: 8px; }

/* ── Sharpe warning ── */
.sharpe-warn { font-size: 10px; color: #92400e; background: #fef3c7; border-radius: 4px; padding: 1px 6px; display: inline-block; margin-top: 1px; }

@media (prefers-color-scheme: dark) {
  .app-header { background: linear-gradient(135deg, #0a1628, #0f2040, #112350); }
  .nav-bar { background: #0f172a; border-color: #1e3a5f; }
  div[role="radiogroup"] label { background: #1e293b !important; border-color: #334155 !important; color: #cbd5e1 !important; }
  div[role="radiogroup"] label:has(input:checked) { background: #1e40af !important; border-color: #1e40af !important; color: #fff !important; }
  .profile-section { background: #0f172a; border-color: #1e3a8a; }
  .portfolio-card { background: #052e16; border-color: #166534; }
  .vote-section { background: linear-gradient(135deg, #0f172a, #0d1d3a); border-color: #1e3a5f; }
  .res-tbl th { background: #1e3a8a; }
  .res-tbl td { border-color: #1e293b; color: #cbd5e1; }
  .score-tip { background: #451a03; border-color: #92400e; color: #fde68a; }
}
div[data-testid="stDataFrame"] * { direction: rtl; text-align: right; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def _esc(x) -> str:
    try:
        return html.escape("" if x is None else str(x), quote=True)
    except Exception:
        return ""

def _to_float(x) -> float:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return np.nan
    if isinstance(x, (int, float, np.number)):
        return float(x)
    s = re.sub(r"[^\d.\-]", "", str(x).replace(",", "").replace("−", "-"))
    if s in ("", "-", "."):
        return np.nan
    try:
        return float(s)
    except Exception:
        return np.nan

def _fmt_pct(x, decimals=2) -> str:
    try:
        return f"{float(x):.{decimals}f}%"
    except Exception:
        return "—"

def _fmt_num(x, fmt="{:.2f}") -> str:
    try:
        return fmt.format(float(x))
    except Exception:
        return "—"


# ─────────────────────────────────────────────
# Password Gate
# ─────────────────────────────────────────────
def _check_password() -> bool:
    if st.session_state.get("auth_ok", False):
        return True
    is_default = True
    if hasattr(st, "secrets") and "APP_PASSWORD" in st.secrets:
        correct = str(st.secrets["APP_PASSWORD"])
        is_default = False
    else:
        correct = os.getenv("APP_PASSWORD", "1234")

    st.markdown("""
    <div class="pw-wrap">
      <div class="pw-title">🔒 כניסה</div>
      <div class="pw-sub">האפליקציה מוגנת בסיסמה</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        pwd = st.text_input("סיסמה", type="password", placeholder="••••••••", label_visibility="collapsed")
        if st.button("כניסה", use_container_width=True, type="primary"):
            if pwd == correct:
                st.session_state["auth_ok"] = True
                st.rerun()
            else:
                st.error("סיסמה שגויה")
        if is_default:
            st.markdown(
                '<div class="pw-warn">⚠️ סיסמה ברירת מחדל (1234). הגדר APP_PASSWORD ב-Streamlit Secrets בייצור!</div>',
                unsafe_allow_html=True
            )
    st.stop()

_check_password()


# ─────────────────────────────────────────────
# Google Sheets – מקורות נתונים
# ─────────────────────────────────────────────
FUNDS_GSHEET_ID   = "1ty_tqcyGqmVI4pQZetHHKd-cC0O2HCpD2dbpNpYlPtY"
SERVICE_GSHEET_ID = "1FSgvIG6VsJxB5QPY6fmwAwGc1TYLB0KXg-7ckkD_RJQ"

# ─────────────────────────────────────────────
# Voting – Google Sheets via Service Account
# ─────────────────────────────────────────────
VOTES_SHEET_NAME = "votes"

def _get_votes_worksheet():
    """Return the gspread worksheet for votes, or None if not configured."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
        ]
        # Credentials stored in Streamlit Secrets as [gcp_service_account]
        if not (hasattr(st, "secrets") and "gcp_service_account" in st.secrets):
            return None
        sa_info = dict(st.secrets["gcp_service_account"])
        creds   = Credentials.from_service_account_info(sa_info, scopes=scopes)
        client  = gspread.authorize(creds)
        sheet   = client.open_by_key(FUNDS_GSHEET_ID)
        try:
            ws = sheet.worksheet(VOTES_SHEET_NAME)
        except gspread.WorksheetNotFound:
            ws = sheet.add_worksheet(title=VOTES_SHEET_NAME, rows=2000, cols=8)
            ws.append_row(["timestamp","alternative","managers","tracks",
                           "n_funds","mix_policy","session_hash"], value_input_option="RAW")
        return ws
    except Exception as _e:
        return None


def _write_vote(alternative: str, managers: str, tracks: str) -> bool:
    """Write a single vote row. Returns True on success."""
    try:
        ws = _get_votes_worksheet()
        if ws is None:
            return False
        import hashlib, uuid
        session_id = st.session_state.get("_session_id")
        if not session_id:
            session_id = hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()[:10]
            st.session_state["_session_id"] = session_id
        ws.append_row([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            alternative,
            managers,
            tracks,
            str(st.session_state.get("n_funds", 2)),
            str(st.session_state.get("mix_policy", "")),
            session_id,
        ], value_input_option="RAW")
        return True
    except Exception:
        return False


@st.cache_data(ttl=300, show_spinner=False)
def _load_votes_cached() -> pd.DataFrame:
    """Load all votes from the sheet (cached 5 min)."""
    try:
        ws = _get_votes_worksheet()
        if ws is None:
            return pd.DataFrame()
        records = ws.get_all_records()
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame(records)
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame()


def _render_votes_stats():
    """Render voting statistics in an expander."""
    df = _load_votes_cached()

    if df.empty:
        st.info("עדיין אין נתוני הצבעות. היה הראשון לבחור חלופה!")
        return

    from datetime import timedelta
    cutoff_30 = datetime.now() - timedelta(days=30)
    cutoff_7  = datetime.now() - timedelta(days=7)
    df30 = df[df["timestamp"] >= cutoff_30].copy()
    df7  = df[df["timestamp"] >= cutoff_7].copy()

    total_30 = len(df30)
    total_7  = len(df7)
    total_all = len(df)

    # ── Summary numbers ──
    c1, c2, c3 = st.columns(3)
    c1.metric("הצבעות ב-30 יום", f"{total_30:,}")
    c2.metric("הצבעות ב-7 ימים", f"{total_7:,}")
    c3.metric("סה״כ כל הזמנים", f"{total_all:,}")

    if df30.empty:
        st.caption("אין הצבעות ב-30 הימים האחרונים עדיין.")
        return

    st.markdown("---")

    # ── Alternative popularity ──
    st.markdown("**🏆 פופולריות חלופות — 30 יום אחרונים**")
    alt_counts = df30["alternative"].value_counts().reset_index()
    alt_counts.columns = ["חלופה", "הצבעות"]
    alt_counts["אחוז"] = (alt_counts["הצבעות"] / total_30 * 100).round(1).astype(str) + "%"

    # Color bar HTML
    max_v = int(alt_counts["הצבעות"].max()) if total_30 else 1
    bar_colors = {"חלופה משוקללת": "#2563eb", "הכי מדויקת": "#16a34a",
                  "שארפ מקסימלי": "#ea580c", "שירות מוביל": "#7c3aed"}
    rows_html = ""
    for _, r in alt_counts.iterrows():
        alt   = str(r["חלופה"])
        cnt   = int(r["הצבעות"])
        pct   = r["אחוז"]
        color = bar_colors.get(alt, "#64748b")
        bar_w = max(4, int(cnt / max_v * 200))
        rows_html += (
            f"<div style='display:flex;align-items:center;gap:10px;margin:5px 0;direction:rtl'>"
            f"<span style='min-width:130px;font-weight:700;font-size:13px'>{_esc(alt)}</span>"
            f"<div style='height:18px;width:{bar_w}px;background:{color};border-radius:4px'></div>"
            f"<span style='font-size:12px;color:#475569'>{cnt} ({pct})</span>"
            f"</div>"
        )
    st.markdown(rows_html, unsafe_allow_html=True)

    st.markdown("---")

    # ── Top tracks voted for ──
    if "tracks" in df30.columns:
        st.markdown("**📋 המסלולים הנבחרים ביותר — 30 יום**")
        all_tracks_voted = []
        for cell in df30["tracks"].dropna():
            for t in str(cell).split("|"):
                t = t.strip()
                if t:
                    all_tracks_voted.append(t)
        if all_tracks_voted:
            tc = pd.Series(all_tracks_voted).value_counts().head(8)
            track_rows = ""
            for trk, cnt in tc.items():
                track_rows += (
                    f"<div style='display:flex;justify-content:space-between;"
                    f"padding:4px 0;border-bottom:1px solid #f1f5f9;font-size:12px;direction:rtl'>"
                    f"<span style='color:#334155'>{_esc(str(trk))}</span>"
                    f"<span style='font-weight:800;color:#1e3a8a'>{cnt}</span>"
                    f"</div>"
                )
            st.markdown(f"<div style='border:1px solid #e2e8f0;border-radius:10px;padding:10px 14px'>{track_rows}</div>",
                        unsafe_allow_html=True)

    st.caption(f"נתונים מתעדכנים כל 5 דקות. עדכון אחרון: {datetime.now().strftime('%H:%M:%S')}")


PARAM_ALIASES = {
    "stocks":   ["סך חשיפה למניות", "מניות"],
    "foreign":  ['סך חשיפה לנכסים המושקעים בחו"ל', "סך חשיפה לנכסים המושקעים בחו׳ל", 'חו"ל', "חו׳ל"],
    "fx":       ['חשיפה למט"ח', 'מט"ח', "מט׳׳ח"],
    "illiquid": ["נכסים לא סחירים", "לא סחירים", "לא-סחיר", "לא סחיר"],
    "sharpe":   ["מדד שארפ", "שארפ"],
}

# ── פיצ׳ר 2: quick profiles ───────────────────
QUICK_PROFILES = {
    "📈 מניות":  {"stocks_min": 90},
    '🏦 אג"ח':   {"stocks_max": 10, "illiquid_max": 10},
    "🌍 חו״ל":   {"foreign_min": 90},
    "🇮🇱 ישראל": {"foreign_max": 10},
    '💱 מט"ח':   {"fx_min": 90},
}


# ─────────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────────
def _match_param(row_name: str, key: str) -> bool:
    rn = str(row_name).strip()
    return any(a in rn for a in PARAM_ALIASES[key])

def _extract_manager(fund_name: str) -> str:
    name = str(fund_name).strip()
    for splitter in [" קרן", " השתלמות", " -", "-", "  "]:
        if splitter in name:
            head = name.split(splitter)[0].strip()
            if head:
                return head
    return name.split()[0] if name.split() else name

def _gsheet_to_bytes(sheet_id: str) -> Tuple[bytes, str]:
    import requests as _req
    urls = [
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx",
        f"https://docs.google.com/feeds/download/spreadsheets/Export?key={sheet_id}&exportFormat=xlsx",
    ]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    last_err = ""
    for url in urls:
        try:
            resp = _req.get(url, headers=headers, allow_redirects=True, timeout=30)
            if resp.status_code == 200 and len(resp.content) > 500:
                if resp.content[:2] == b"PK":
                    return resp.content, ""
                else:
                    preview = resp.content[:120].decode("utf-8", errors="ignore").replace("\n"," ") if resp.content else ""
                    last_err = (
                        f"קוד 200 אבל התקבל HTML במקום XLSX (גיליון {sheet_id[:20]}). "
                        "בדוק ש-Share מוגדר 'Anyone with the link' כ-Viewer. "
                        f"Preview: {preview[:80]}"
                    )
            else:
                last_err = f"HTTP {resp.status_code} מ-{url[:60]}"
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
    return b"", last_err

def _load_service_scores(xlsx_bytes: bytes) -> Tuple[Dict[str, float], str]:
    try:
        df = pd.read_excel(io.BytesIO(xlsx_bytes), header=None)
    except Exception as e:
        return {}, f"שגיאה בטעינת ציוני שירות: {e}"
    if df.empty:
        return {}, "גיליון ציוני שירות ריק"

    try:
        df_hdr = pd.read_excel(io.BytesIO(xlsx_bytes))
        if not df_hdr.empty:
            cols = [str(c).lower().strip() for c in df_hdr.columns]
            df_hdr.columns = cols
            if "provider" in df_hdr.columns and "score" in df_hdr.columns:
                out = {}
                for _, r in df_hdr.iterrows():
                    p = _extract_manager(str(r["provider"]).strip())
                    sc = _to_float(r["score"])
                    if p and not math.isnan(sc):
                        out[p] = float(sc)
                if out:
                    return out, ""
    except Exception:
        pass

    df2 = df.copy().dropna(how="all").dropna(how="all", axis=1)
    if df2.shape[0] >= 2 and df2.shape[1] >= 2:
        first_col = df2.iloc[:, 0].astype(str).str.strip().str.lower()
        prov_rows = df2.index[first_col.eq("provider")].tolist()
        combo_cell = df2.iloc[:, 0].astype(str).str.strip().str.lower()
        combo_rows = df2.index[combo_cell.str.contains("provider") & combo_cell.str.contains("score")].tolist()
        for r0 in combo_rows:
            if r0 not in prov_rows:
                prov_rows.append(r0)
        for r0 in prov_rows[:3]:
            if r0 + 1 in df2.index:
                header = df2.loc[r0].tolist()
                values = df2.loc[r0 + 1].tolist()
                tag = str(values[0]).strip().lower()
                if tag in {"score", "ציון", "שירות", "ציון שירות"} or tag in {"nan", "", "none"}:
                    out = {}
                    for name, val in zip(header[1:], values[1:]):
                        p = _extract_manager(str(name).strip())
                        sc = _to_float(val)
                        if p and not math.isnan(sc):
                            out[p] = float(sc)
                    if out:
                        return out, ""

    return {}, "מבנה גיליון שירות לא מזוהה"


# ─────────────────────────────────────────────
# פיצ׳ר 1: Parse clearing house report
# ─────────────────────────────────────────────
def parse_clearing_report(xlsx_bytes: bytes) -> Tuple[Optional[Dict], str]:
    """
    מנתח דו"ח מסלקה (Excel) ומחזיר dict עם:
      {
        "holdings": [{"fund": str, "manager": str, "track": str, "amount": float, "weight_pct": float}],
        "total_amount": float,
        "baseline": {"foreign": float, "stocks": float, "fx": float, "illiquid": float}
      }
    או None + הודעת שגיאה.
    """
    AMOUNT_ALIASES  = ["יתרה", "ערך", "סכום", "balance", "amount", "שווי"]
    FUND_ALIASES    = ["שם הקרן", "קרן", "שם מוצר", "fund", "product", "שם הקופה", "שם הגוף"]
    MANAGER_ALIASES = ["מנהל", "גוף מנהל", "בית השקעות", "manager", "provider", "מנהל ההשקעות"]
    TRACK_ALIASES   = ["מסלול", "track", "שם מסלול"]

    try:
        xls = pd.ExcelFile(io.BytesIO(xlsx_bytes))
    except Exception as e:
        return None, f"לא ניתן לפתוח את הקובץ: {e}"

    all_records = []

    for sheet in xls.sheet_names:
        try:
            df = pd.read_excel(xls, sheet_name=sheet, header=None)
        except Exception:
            continue
        if df.empty or df.shape[0] < 2:
            continue

        # Find header row (contains at least one known alias)
        header_idx = None
        for i in range(min(10, len(df))):
            row_vals = [str(v).strip().lower() for v in df.iloc[i].tolist()]
            matches = sum(
                1 for v in row_vals
                if any(a.lower() in v for a in AMOUNT_ALIASES + FUND_ALIASES + MANAGER_ALIASES)
            )
            if matches >= 2:
                header_idx = i
                break

        if header_idx is None:
            continue

        df_clean = df.iloc[header_idx:].copy().reset_index(drop=True)
        df_clean.columns = [str(c).strip() for c in df_clean.iloc[0].tolist()]
        df_clean = df_clean.iloc[1:].reset_index(drop=True)

        def _find_col(aliases):
            for col in df_clean.columns:
                col_l = col.lower()
                for a in aliases:
                    if a.lower() in col_l:
                        return col
            return None

        fund_col    = _find_col(FUND_ALIASES)
        manager_col = _find_col(MANAGER_ALIASES)
        amount_col  = _find_col(AMOUNT_ALIASES)
        track_col   = _find_col(TRACK_ALIASES)

        if not fund_col and not manager_col:
            continue
        if not amount_col:
            continue

        for _, row in df_clean.iterrows():
            fund_name    = str(row.get(fund_col, "") or "").strip() if fund_col else ""
            manager_name = str(row.get(manager_col, "") or "").strip() if manager_col else ""
            track_name   = str(row.get(track_col, "") or "").strip() if track_col else ""
            amount_val   = _to_float(row.get(amount_col, np.nan))

            if not fund_name and not manager_name:
                continue
            if math.isnan(amount_val) or amount_val <= 0:
                continue

            if not manager_name and fund_name:
                manager_name = _extract_manager(fund_name)

            all_records.append({
                "fund":    fund_name or manager_name,
                "manager": manager_name or _extract_manager(fund_name),
                "track":   track_name,
                "amount":  amount_val,
            })

    if not all_records:
        return None, (
            "לא נמצאו נתונים בקובץ. וודא שהקובץ הוא דו\"ח מסלקה תקני "
            "עם עמודות שם קרן/מנהל וסכום/יתרה."
        )

    total = sum(r["amount"] for r in all_records)
    for r in all_records:
        r["weight_pct"] = round(r["amount"] / total * 100, 2) if total > 0 else 0.0

    return {
        "holdings":     all_records,
        "total_amount": total,
        "baseline":     None,  # יחושב בהמשך מהנתונים של האפליקציה
    }, ""


def _compute_baseline_from_holdings(holdings: List[Dict], df_long: pd.DataFrame) -> Optional[Dict]:
    """מחשב פרמטרי חשיפה משוקללים לפורטפוליו הנוכחי."""
    if not holdings:
        return None
    total = sum(r["amount"] for r in holdings)
    if total <= 0:
        return None

    result = {"foreign": 0.0, "stocks": 0.0, "fx": 0.0, "illiquid": 0.0, "sharpe": 0.0, "service": 0.0}
    matched = 0

    for h in holdings:
        w = h["amount"] / total
        # חפש התאמה בנתוני האפליקציה (לפי שם מנהל או שם קרן)
        fund_match = df_long[df_long["fund"].str.lower().str.strip() == h["fund"].lower().strip()]
        if fund_match.empty:
            mgr_match = df_long[df_long["manager"].str.lower().str.strip() == h["manager"].lower().strip()]
            if not mgr_match.empty:
                fund_match = mgr_match.head(1)
        if fund_match.empty:
            # fuzzy: check if any word matches
            words = h["manager"].lower().split()
            for word in words:
                if len(word) > 2:
                    m = df_long[df_long["manager"].str.lower().str.contains(word, na=False)]
                    if not m.empty:
                        fund_match = m.head(1)
                        break

        if not fund_match.empty:
            r = fund_match.iloc[0]
            for key in ["foreign", "stocks", "fx", "illiquid", "sharpe", "service"]:
                val = _to_float(r.get(key, np.nan))
                if not math.isnan(val):
                    result[key] += val * w
            matched += 1

    return result if matched > 0 else None


@st.cache_data(show_spinner=False, ttl=900)
def load_funds_long(funds_id: str, service_id: str) -> Tuple[pd.DataFrame, Dict[str, float], List[str]]:
    warnings: List[str] = []

    svc_bytes, svc_err = _gsheet_to_bytes(service_id)
    if svc_err:
        warnings.append(svc_err)
        svc = {}
    else:
        svc, parse_err = _load_service_scores(svc_bytes)
        if parse_err:
            warnings.append(parse_err)

    funds_bytes, funds_err = _gsheet_to_bytes(funds_id)
    if funds_err:
        return pd.DataFrame(), svc, warnings + [funds_err]

    try:
        xls = pd.ExcelFile(io.BytesIO(funds_bytes))
    except Exception as e:
        return pd.DataFrame(), svc, warnings + [f"שגיאה בפתיחת גיליון קרנות: {e}"]

    records: List[Dict] = []
    for sh in xls.sheet_names:
        sh_str = str(sh)
        if re.search(r"ניהול\s*אישי", sh_str) or re.search(r"(^|[^a-z])ira([^a-z]|$)", sh_str.lower()):
            continue
        try:
            df = pd.read_excel(xls, sheet_name=sh, header=None)
        except Exception as e:
            warnings.append(f"גיליון '{sh}': שגיאת קריאה – {e}")
            continue
        if df.empty:
            continue

        header_row = df.iloc[0].tolist()
        if not str(header_row[0]).strip().startswith("פרמטר"):
            idxs = df.index[df.iloc[:, 0].astype(str).str.contains("פרמטר", na=False)].tolist()
            if not idxs:
                continue
            df = df.iloc[idxs[0]:].reset_index(drop=True)
            header_row = df.iloc[0].tolist()

        fund_names = [c for c in header_row[1:] if str(c).strip() and str(c).strip() != "nan"]
        if not fund_names:
            continue

        param_col = df.iloc[1:, 0].astype(str).tolist()

        def row_for(key: str) -> Optional[int]:
            for i, rn in enumerate(param_col, start=1):
                if _match_param(rn, key):
                    return i
            return None

        ridx = {k: row_for(k) for k in ["stocks", "foreign", "fx", "illiquid", "sharpe"]}
        if ridx["foreign"] is None and ridx["stocks"] is None:
            continue

        for j, fname in enumerate(fund_names, start=1):
            manager = _extract_manager(fname)
            rec = {
                "track":    sh_str,
                "fund":     str(fname).strip(),
                "manager":  manager,
                "stocks":   _to_float(df.iloc[ridx["stocks"],   j]) if ridx["stocks"]   is not None else np.nan,
                "foreign":  _to_float(df.iloc[ridx["foreign"],  j]) if ridx["foreign"]  is not None else np.nan,
                "fx":       _to_float(df.iloc[ridx["fx"],       j]) if ridx["fx"]       is not None else np.nan,
                "illiquid": _to_float(df.iloc[ridx["illiquid"], j]) if ridx["illiquid"] is not None else np.nan,
                "sharpe":   _to_float(df.iloc[ridx["sharpe"],   j]) if ridx["sharpe"]   is not None else np.nan,
            }
            if all(math.isnan(rec[k]) for k in ["foreign", "stocks", "fx", "illiquid", "sharpe"]):
                continue
            rec["service"] = float(svc.get(manager, 50.0))
            records.append(rec)

    df_long = pd.DataFrame.from_records(records)
    if not df_long.empty:
        for c in ["stocks", "foreign", "fx", "illiquid", "sharpe", "service"]:
            if c in df_long.columns:
                df_long[c] = pd.to_numeric(df_long[c], errors="coerce")
    return df_long, svc, warnings


# ─────────────────────────────────────────────
# Optimizer
# ─────────────────────────────────────────────
def _weights_for_n(n: int, step: int) -> np.ndarray:
    step = max(1, int(step))
    if n == 1:
        return np.array([[100]], dtype=float)
    if n == 2:
        ws = np.arange(0, 101, step)
        pairs = np.column_stack([ws, 100 - ws])
        return pairs.astype(float)
    out = []
    for w1 in range(0, 101, step):
        for w2 in range(0, 101 - w1, step):
            w3 = 100 - w1 - w2
            if w3 >= 0 and w3 % step == 0:
                out.append([w1, w2, w3])
    return np.array(out, dtype=float) if out else np.empty((0, 3), dtype=float)

def _prefilter_candidates(df, include, targets, cap, locked_fund):
    keys = [k for k, v in include.items() if v and k in ["foreign", "stocks", "fx", "illiquid"]]
    if not keys:
        keys = ["foreign", "stocks"]
    tmp = df.copy()
    score = np.zeros(len(tmp), dtype=float)
    for k in keys:
        score += np.abs(tmp[k].fillna(50.0).to_numpy() - float(targets.get(k, 0.0))) / 100.0
    tmp["_s"] = score
    if locked_fund:
        locked_mask = tmp["fund"].str.strip() == locked_fund.strip()
        locked_df = tmp[locked_mask]
        rest_df   = tmp[~locked_mask].sort_values("_s").head(max(cap - len(locked_df), 1))
        tmp = pd.concat([locked_df, rest_df])
    else:
        tmp = tmp.sort_values("_s").head(cap)
    return tmp.drop(columns=["_s"]).reset_index(drop=True)

def _hard_ok_vec(values, target, mode):
    if mode == "בדיוק":
        return np.abs(values - target) < 0.5
    if mode == "לפחות":
        return values >= target - 0.5
    if mode == "לכל היותר":
        return values <= target + 0.5
    return np.ones(len(values), dtype=bool)

def find_best_solutions(
    df, n_funds, step, mix_policy, include, constraint, targets, primary_rank,
    locked_fund="", locked_weight_pct: Optional[float] = None,
    max_solutions_scan=20000,
) -> Tuple[pd.DataFrame, str]:
    import gc
    targets = {k: float(v) for k, v in targets.items()}

    cap = 50 if n_funds == 2 else 35 if n_funds == 3 else 80
    df_scan = _prefilter_candidates(df, include, targets, cap=cap, locked_fund=locked_fund)

    weights_arr  = _weights_for_n(n_funds, step)
    if len(weights_arr) == 0:
        return pd.DataFrame(), "לא נמצאו שילובי משקלים. נסה צעד קטן יותר."
    weights_norm = weights_arr / 100.0

    metric_keys = ["foreign", "stocks", "fx", "illiquid"]
    active_soft = [k for k in metric_keys if include.get(k, False)] or ["foreign", "stocks"]
    soft_idx    = {k: i for i, k in enumerate(metric_keys)}
    hard_keys   = [(k, constraint[k][1]) for k in metric_keys
                   if constraint.get(k, ("רך", ""))[0] == "קשיח"]

    A       = df_scan[["foreign","stocks","fx","illiquid","sharpe","service"]].to_numpy(dtype=float)
    records = df_scan.reset_index(drop=True)

    locked_idx: Optional[int] = None
    if locked_fund:
        matches = records.index[records["fund"].str.strip() == locked_fund.strip()].tolist()
        if matches:
            locked_idx = matches[0]

    # ── פיצ׳ר 3: סינון משקלים לפי locked_weight_pct ──
    if locked_idx is not None and locked_weight_pct is not None:
        tol = max(step * 0.5, 0.5)
        # עמודה של הקרן הנעולה היא העמודה שמתאימה ל-locked_idx בקומבינציה
        # נסנן אחרי בחירת קומבינציה — שמור רק weights שבהם המשקל ב-locked_idx == locked_weight_pct
        # בשלב הלולאה נסנן ידנית
        pass  # handled in loop below

    if mix_policy == "אותו מנהל בלבד":
        groups = list(records.groupby("manager").groups.values())
        combo_source = itertools.chain.from_iterable(
            itertools.combinations(list(g), n_funds) for g in groups if len(g) >= n_funds
        )
    else:
        combo_source = itertools.combinations(range(len(records)), n_funds)

    solutions = []
    scanned   = 0
    MAX_STORED = 60000

    for combo in combo_source:
        if locked_idx is not None and locked_idx not in combo:
            continue
        scanned += 1
        if scanned > max_solutions_scan:
            break

        arr     = A[list(combo), :]
        w_arr   = weights_arr.copy()

        # ── פיצ׳ר 3: אם יש locked_weight_pct, סנן משקלים ──
        if locked_idx is not None and locked_weight_pct is not None:
            pos_in_combo = list(combo).index(locked_idx)
            tol = max(step * 0.5, 0.5)
            mask_w = np.abs(w_arr[:, pos_in_combo] - locked_weight_pct) <= tol
            w_arr = w_arr[mask_w]
            if len(w_arr) == 0:
                continue

        w_norm = w_arr / 100.0
        mix_all = np.einsum("wn,nm->wm", w_norm, np.nan_to_num(arr, nan=0.0))

        mask = np.ones(len(w_norm), dtype=bool)
        for k, mode in hard_keys:
            mask &= _hard_ok_vec(mix_all[:, soft_idx[k]], targets.get(k, 0.0), mode)
        if not mask.any():
            continue

        mix_ok    = mix_all[mask]
        w_ok      = w_arr[mask]
        score_arr = np.zeros(len(mix_ok))
        for k in active_soft:
            score_arr += np.abs(mix_ok[:, soft_idx[k]] - targets.get(k, 0.0)) / 100.0

        fund_labels  = [records.loc[i, "fund"]    for i in combo]
        track_labels = [records.loc[i, "track"]   for i in combo]
        managers     = [records.loc[i, "manager"] for i in combo]
        manager_set  = " | ".join(sorted(set(managers)))

        # ── Feature 5: Sharpe validity check ──
        sharpe_vals = arr[:, 4]  # sharpe column
        sharpe_incomplete = bool(np.any(np.isnan(sharpe_vals) | (sharpe_vals == 0)))

        for wi in range(len(mix_ok)):
            solutions.append({
                "combo":             combo,
                "weights":           tuple(int(round(x)) for x in w_ok[wi]),
                "מנהלים":            manager_set,
                "מסלולים":           " | ".join(track_labels),
                "קופות":             " | ".join(fund_labels),
                'חו"ל (%)'  :        float(mix_ok[wi, 0]),
                "ישראל (%)"  :        float(100.0 - mix_ok[wi, 0]),
                "מניות (%)"  :        float(mix_ok[wi, 1]),
                'מט"ח (%)'  :        float(mix_ok[wi, 2]),
                "לא־סחיר (%)" :       float(mix_ok[wi, 3]),
                "שארפ משוקלל":        np.nan if sharpe_incomplete else float(mix_ok[wi, 4]),
                "sharpe_incomplete":  sharpe_incomplete,
                "שירות משוקלל":       float(mix_ok[wi, 5]),
                "score"       :       float(score_arr[wi]),
            })

        if len(solutions) >= MAX_STORED:
            solutions.sort(key=lambda r: (r["score"], -r["שארפ משוקלל"], -r["שירות משוקלל"]))
            solutions = solutions[:10000]
            gc.collect()

    if not solutions:
        return pd.DataFrame(), "לא נמצאו פתרונות. נסה לרכך מגבלות, להגדיל צעד, או לשנות יעדים."

    df_sol = pd.DataFrame(solutions)
    del solutions
    gc.collect()

    note = f"נסרקו {min(scanned, max_solutions_scan):,} קומבינציות מתוך {len(df_scan)} קופות מסוננות."

    if primary_rank == "דיוק":
        df_sol = df_sol.sort_values(["score", "שארפ משוקלל", "שירות משוקלל"], ascending=[True, False, False])
    elif primary_rank == "שארפ":
        df_sol = df_sol.sort_values(["שארפ משוקלל", "score"], ascending=[False, True])
    elif primary_rank == "שירות":
        df_sol = df_sol.sort_values(["שירות משוקלל", "score"], ascending=[False, True])

    return df_sol, note

def _pick_three_distinct(df_sol, primary_rank):
    if df_sol.empty:
        return df_sol

    def mgr(row): return str(row["מנהלים"]).strip()

    sorted_primary = df_sol.copy()
    sorted_sharpe  = df_sol.sort_values(["שארפ משוקלל",  "score"], ascending=[False, True])
    sorted_service = df_sol.sort_values(["שירות משוקלל", "score"], ascending=[False, True])

    def best_from(df_sorted, exclude_managers):
        for _, r in df_sorted.iterrows():
            if mgr(r) not in exclude_managers:
                return r
        return df_sorted.iloc[0]

    pick1 = best_from(sorted_primary, set())
    pick2 = best_from(sorted_sharpe,  set())
    pick3 = best_from(sorted_service, set())

    used_after_1 = {mgr(pick1)}
    if mgr(pick2) in used_after_1:
        pick2 = best_from(sorted_sharpe, used_after_1)

    used_after_2 = used_after_1 | {mgr(pick2)}
    if mgr(pick3) in used_after_2:
        pick3 = best_from(sorted_service, used_after_2)

    labels     = ["חלופה 1 – דירוג ראשי", "חלופה 2 – שארפ", "חלופה 3 – שירות"]
    criterions = ["דיוק", "שארפ", "שירות"]
    base = pick1.to_dict()
    rows = []
    for i, r in enumerate([pick1, pick2, pick3]):
        row = r.to_dict()
        row["חלופה"]        = labels[i]
        row["weights_items"] = _weights_items(row.get("weights"), row.get("קופות",""), row.get("מסלולים",""))
        row["משקלים"]       = _weights_short(row.get("weights"))
        row["יתרון"]        = _make_advantage(criterions[i], row, base if i > 0 else None)
        rows.append(row)
    return pd.DataFrame(rows)


def _weights_items(weights, funds_str, tracks_str):
    try:    ws = list(weights)
    except: ws = []
    funds  = [s.strip() for s in (funds_str  or "").split("|") if s.strip()]
    tracks = [s.strip() for s in (tracks_str or "").split("|") if s.strip()]
    n = max(len(ws), len(funds))
    return [
        {
            "pct":   f"{int(round(float(ws[i])))}%" if i < len(ws) else "?",
            "fund":  funds[i]  if i < len(funds)  else "",
            "track": tracks[i] if i < len(tracks) else "",
        }
        for i in range(n)
    ]

def _weights_short(weights):
    if weights is None: return ""
    try:    w = [float(x) for x in weights]
    except: return ""
    return " / ".join(f"{int(round(x))}%" for x in w)

def _make_advantage(primary, row, base=None):
    score = row.get("score", 0)
    if primary == "דיוק":
        return f"מדויק ביותר ליעד (סטייה {score:.4f})"
    if primary == "שארפ":
        sh = float(row.get("שארפ משוקלל", 0) or 0)
        delta = sh - float((base or {}).get("שארפ משוקלל", sh) or sh)
        return f"שארפ {sh:.2f} (+{delta:.2f} מחלופה 1)"
    sv = float(row.get("שירות משוקלל", 0) or 0)
    delta = sv - float((base or {}).get("שירות משוקלל", sv) or sv)
    return f"שירות {sv:.1f} (+{delta:.1f} מחלופה 1)"


# ─────────────────────────────────────────────
# Render helpers
# ─────────────────────────────────────────────
def _normalize_series(s):
    s = pd.to_numeric(s, errors="coerce").fillna(0.0)
    mn, mx = float(s.min()), float(s.max())
    if abs(mx - mn) < 1e-12:
        return pd.Series([0.5] * len(s), index=s.index)
    return (s - mn) / (mx - mn)

def _pick_recommendations(df_sol_head):
    if df_sol_head is None or df_sol_head.empty:
        return {}
    df = df_sol_head.copy()
    score_n   = _normalize_series(df["score"])
    acc_n     = 1.0 - score_n
    sharpe_n  = _normalize_series(df.get("שארפ משוקלל", pd.Series([0]*len(df))))
    service_n = _normalize_series(df.get("שירות משוקלל", pd.Series([0]*len(df))))
    df["_weighted_pref"] = 0.45*acc_n + 0.15*sharpe_n + 0.40*service_n
    weighted     = df.loc[df["_weighted_pref"].idxmax()].to_dict()
    accurate     = df.loc[df["score"].idxmin()].to_dict()
    best_sh      = df.loc[df["שארפ משוקלל"].idxmax()].to_dict() if "שארפ משוקלל" in df.columns else accurate
    best_service = df.loc[df["שירות משוקלל"].idxmax()].to_dict() if "שירות משוקלל" in df.columns else accurate
    return {"weighted": weighted, "accurate": accurate, "sharpe": best_sh, "service": best_service}

def _manager_weights_from_items(items, manager_names):
    if not items: return []
    names = sorted([m for m in manager_names if isinstance(m, str) and m.strip()], key=len, reverse=True)
    agg = {}
    for it in items:
        fund = str(it.get("fund",""))
        pct  = float(str(it.get("pct","0")).replace("%","") or 0)
        chosen = None
        for n in names:
            if fund.strip().startswith(n) or (n in fund.strip()):
                chosen = n
                break
        if chosen is None: chosen = "אחר"
        agg[chosen] = agg.get(chosen, 0.0) + pct
    return sorted(agg.items(), key=lambda x: -x[1])

def _change_type_badge(cur_mgrs, prop_mgrs):
    cur_set  = set(m.strip() for m in cur_mgrs  if m.strip())
    prop_set = set(m.strip() for m in prop_mgrs if m.strip())
    if not cur_set:
        return ""
    if cur_set == prop_set:
        return "<span class='change-badge change-low'>✅ שינוי מסלול – אותו מנהל</span>"
    elif cur_set & prop_set:
        return "<span class='change-badge change-med'>⚠️ ניוד חלקי</span>"
    else:
        return "<span class='change-badge change-high'>🔴 ניוד מלא</span>"

# ─────────────────────────────────────────────
# AI explanation (Claude API)
# ─────────────────────────────────────────────
BAR_COLORS = ["#4f46e5","#2563eb","#0891b2","#7c3aed","#059669","#d97706"]

@st.cache_data(show_spinner=False, ttl=3600)
def _ai_explain(title: str, managers: str, weights_str: str,
                foreign: float, stocks: float, fx: float, illiquid: float,
                sharpe: float, service: float,
                has_baseline: bool, bl_foreign: float, bl_stocks: float,
                bl_sharpe: float, bl_service: float) -> str:
    """Call Claude API to generate a Hebrew explanation of this alternative."""
    import requests as _req

    api_key = ""
    try:
        if hasattr(st, "secrets") and "ANTHROPIC_API_KEY" in st.secrets:
            api_key = str(st.secrets["ANTHROPIC_API_KEY"])
    except Exception:
        pass
    if not api_key:
        import os
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return ""

    baseline_block = ""
    if has_baseline:
        baseline_block = (
            f"\nהמצב הנוכחי של הלקוח: חו\"ל {bl_foreign:.1f}%, מניות {bl_stocks:.1f}%, "
            f"שארפ {bl_sharpe:.2f}, שירות {bl_service:.1f}."
        )

    prompt = (
        f"אתה יועץ פיננסי ישראלי מנוסה המתמחה בקרנות השתלמות. "
        f"תפקידך לנסח הסבר תמציתי ומשכנע — 2-3 משפטים בלבד — למה החלופה הזו מתאימה ללקוח."
        f"\n\nהחלופה: {title}"
        f"\nמנהלים: {managers}"
        f"\nחלוקת משקלים: {weights_str}"
        f"\nחשיפות: חו\"ל {foreign:.1f}%, מניות {stocks:.1f}%, מט\"ח {fx:.1f}%, לא-סחיר {illiquid:.1f}%"
        f"\nמדד שארפ: {sharpe:.2f} | ציון שירות: {service:.1f}"
        f"{baseline_block}"
        f"\n\nכתוב בעברית תמציתית. התמקד בערך המוסף העיקרי. אל תציין ש'אתה AI'."
    )

    try:
        resp = _req.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": "claude-haiku-4-5-20251001", "max_tokens": 180,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=12,
        )
        if resp.status_code == 200:
            data = resp.json()
            for blk in data.get("content", []):
                if blk.get("type") == "text":
                    return str(blk["text"]).strip()
    except Exception:
        pass
    return ""


def _mini_alloc_bar_html(items: List[Dict]) -> str:
    """Generate compact horizontal stacked bar HTML for fund weights."""
    if not items:
        return ""
    colors = BAR_COLORS
    rows = ""
    for i, it in enumerate(items[:4]):
        pct_str = str(it.get("pct", "0")).replace("%", "")
        try:
            pct = float(pct_str)
        except Exception:
            pct = 0.0
        color = colors[i % len(colors)]
        width = max(2, min(100, int(pct)))
        name  = str(it.get("fund", ""))[:28]
        rows += (
            f"<div class='rc-fund-row'>"
            f"<span class='rc-fund-pct'>{pct_str}%</span>"
            f"<div class='rc-fund-bar-wrap'><div class='rc-fund-bar' style='width:{width}%;background:{color}'></div></div>"
            f"<span class='rc-fund-name'>{_esc(name)}</span>"
            f"</div>"
        )
    return f"<div class='rc-funds'>{rows}</div>"


def _kpi_chip_html(label: str, val: float, baseline_val: Optional[float] = None,
                   is_lower_better: bool = False, fmt: str = "{:.1f}%") -> str:
    val_str = fmt.format(val)
    delta_html = ""
    if baseline_val is not None:
        diff = val - baseline_val
        if abs(diff) < 0.1:
            cls = "flat"; arrow = "→"
        elif (diff > 0 and not is_lower_better) or (diff < 0 and is_lower_better):
            cls = "up";   arrow = "▲"
        else:
            cls = "down"; arrow = "▼"
        diff_str = ("+" if diff >= 0 else "") + fmt.format(diff)
        delta_html = f"<span class='rc-kpi-delta {cls}'>{arrow}{diff_str}</span>"
    return (
        f"<div class='rc-kpi'>"
        f"<span class='rc-kpi-label'>{_esc(label)}</span>"
        f"<span class='rc-kpi-val'>{_esc(val_str)}</span>"
        f"{delta_html}"
        f"</div>"
    )


def _delta_grid_html(row: Dict, baseline: Dict) -> str:
    """Inline 3-col delta grid comparing baseline vs proposed."""
    items = [
        ('חו"ל',     float(baseline.get("foreign",0)),  float(row.get('חו"ל (%)',0)),   False, "{:.1f}%"),
        ("מניות",    float(baseline.get("stocks",0)),   float(row.get("מניות (%)",0)),  False, "{:.1f}%"),
        ('מט"ח',     float(baseline.get("fx",0)),       float(row.get('מט"ח (%)',0)),   False, "{:.1f}%"),
        ("לא-סחיר",  float(baseline.get("illiquid",0)), float(row.get("לא־סחיר (%)",0)), True, "{:.1f}%"),
        ("שארפ",     float(baseline.get("sharpe",0)),   float(row.get("שארפ משוקלל",0)), False, "{:.2f}"),
        ("שירות",    float(baseline.get("service",0)),  float(row.get("שירות משוקלל",0)), False, "{:.0f}"),
    ]
    cells = ""
    for label, cur, new, lower_better, fmt in items:
        diff = new - cur
        if abs(diff) < 0.05:
            arrow_cls = "flat"; arrow = "→"
        elif (diff > 0 and not lower_better) or (diff < 0 and lower_better):
            arrow_cls = "up"; arrow = "▲"
        else:
            arrow_cls = "down"; arrow = "▼"
        cells += (
            f"<div class='rc-delta-item'>"
            f"<span class='rc-delta-item-label'>{_esc(label)}</span>"
            f"<div class='rc-delta-item-vals'>"
            f"<span class='rc-delta-item-cur'>{fmt.format(cur)}</span>"
            f"<span class='rc-delta-item-arrow {arrow_cls}'>{arrow}</span>"
            f"<span class='rc-delta-item-new'>{fmt.format(new)}</span>"
            f"</div></div>"
        )
    return f"<div class='rc-delta'><div class='rc-delta-title'>השוואה למצב קיים</div><div class='rc-delta-grid'>{cells}</div></div>"


def _render_compact_card(r: Dict, title: str, card_cls: str = "",
                         baseline: Optional[Dict] = None,
                         ai_text: str = "",
                         card_key: str = ""):
    """Render a compact Bloomberg-style result card fully in HTML."""
    items = r.get("weights_items") or _weights_items(r.get("weights"), r.get("קופות",""), r.get("מסלולים",""))

    # Change type badge
    prop_mgrs = [m.strip() for m in str(r.get("מנהלים","")).split("|") if m.strip()]
    cur_mgrs  = list(st.session_state.get("portfolio_managers", []))
    change_badge = _change_type_badge(cur_mgrs, prop_mgrs) if baseline else ""

    # Head badge
    badge_text = {"rc-primary": "⭐ ממולץ", "rc-service": "🤝 שירות"}.get(card_cls, "📊")
    badge_cls  = {"rc-primary": "rc-badge-blue", "rc-service": "rc-badge-green"}.get(card_cls, "rc-badge-amber")

    mgr_str = str(r.get("מנהלים",""))[:60]
    sharpe  = _to_float(r.get("שארפ משוקלל"))
    service = _to_float(r.get("שירות משוקלל"))
    foreign = _to_float(r.get('חו"ל (%)'))
    stocks  = _to_float(r.get("מניות (%)"))
    fx      = _to_float(r.get('מט"ח (%)'))
    illiquid= _to_float(r.get("לא־סחיר (%)"))

    bl_f  = float(baseline.get("foreign",0))  if baseline else None
    bl_s  = float(baseline.get("stocks",0))   if baseline else None
    bl_fx = float(baseline.get("fx",0))       if baseline else None
    bl_il = float(baseline.get("illiquid",0)) if baseline else None
    bl_sh = float(baseline.get("sharpe",0))   if baseline else None
    bl_sv = float(baseline.get("service",0))  if baseline else None

    kpis_html = (
        _kpi_chip_html('חו"ל',     foreign,  bl_f,  False) +
        _kpi_chip_html("מניות",    stocks,   bl_s,  False) +
        _kpi_chip_html('מט"ח',     fx,       bl_fx, False) +
        _kpi_chip_html("לא-סחיר",  illiquid, bl_il, True)  +
        _kpi_chip_html("שארפ",     sharpe,   bl_sh, False, "{:.2f}")  +
        _kpi_chip_html("שירות",    service,  bl_sv, False, "{:.0f}")
    )

    delta_section = _delta_grid_html(r, baseline) if baseline else ""

    ai_section = ""
    if ai_text:
        ai_section = f"<div class='rc-ai'><div class='rc-ai-label'>🤖 ניתוח AI</div><div class='rc-ai-text'>{_esc(ai_text)}</div></div>"
    elif ai_text == "":
        # placeholder while loading
        ai_section = "<div class='rc-ai'><div class='rc-ai-spinner'>טוען ניתוח AI...</div></div>"

    alloc_html = _mini_alloc_bar_html(items)

    st.markdown(f"""
    <div class='rc {card_cls}'>
      <div class='rc-head'>
        <span class='rc-title'>{_esc(title)}</span>
        <div style='display:flex;gap:6px;align-items:center;flex-wrap:wrap'>
          {change_badge}
          <span class='rc-badge {badge_cls}'>{badge_text}</span>
        </div>
      </div>
      <div style='padding:4px 14px 2px;font-size:11px;color:#64748b'>{_esc(mgr_str)}</div>
      {alloc_html}
      <div class='rc-kpis'>{kpis_html}</div>
      {delta_section}
      {ai_section}
    </div>
    """, unsafe_allow_html=True)

# Keep old helpers for comparison tab
def _alloc_plot(r):
    labels = ["מניות", 'חו"ל', 'מט"ח', "לא־סחיר"]
    vals = []
    for k in ["מניות (%)", 'חו"ל (%)', 'מט"ח (%)', "לא־סחיר (%)"]:
        try: vals.append(float(r.get(k) or 0))
        except: vals.append(0.0)
    text_labels = [f"{lbl} · {v:.1f}%" for lbl, v in zip(labels, vals)]
    fig = go.Figure(go.Bar(x=vals, y=labels, orientation='h', text=text_labels, textposition='outside',
        cliponaxis=False, marker=dict(color=['#6366f1','#8b5cf6','#a78bfa','#c4b5fd'])))
    fig.update_layout(height=200, margin=dict(l=10,r=120,t=0,b=0),
        xaxis=dict(range=[0,100], showgrid=False, zeroline=False, visible=False),
        yaxis=dict(autorange='reversed', tickfont=dict(size=12), showgrid=False, title=None),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
    return fig

def _manager_donut(mgr_break):
    labels=[m for m,_ in mgr_break] or ["ללא"]
    values=[float(p) for _,p in mgr_break] or [100.0]
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.62, textinfo='percent', sort=False))
    fig.update_traces(marker=dict(colors=['#4f46e5','#7c3aed','#06b6d4','#22c55e','#f59e0b','#ef4444']))
    fig.update_layout(height=180, margin=dict(l=0,r=0,t=0,b=0), showlegend=False, paper_bgcolor='rgba(0,0,0,0)')
    return fig


def _radar_chart(top_df, targets):
    categories = ['חו"ל', "מניות", 'מט"ח', "לא־סחיר", "שארפ×10", "שירות÷10"]
    fig = go.Figure()
    colors = ["#2563eb", "#16a34a", "#ea580c", "#7c3aed"]
    for i, row in top_df.iterrows():
        vals = [
            float(row.get('חו"ל (%)', 0) or 0),
            float(row.get("מניות (%)", 0) or 0),
            float(row.get('מט"ח (%)', 0) or 0),
            float(row.get("לא־סחיר (%)", 0) or 0),
            float(row.get("שארפ משוקלל", 0) or 0) * 10,
            float(row.get("שירות משוקלל", 0) or 0) / 10,
        ]
        fig.add_trace(go.Scatterpolar(
            r=vals + [vals[0]], theta=categories + [categories[0]],
            fill="toself", opacity=0.25,
            line=dict(color=colors[i % len(colors)], width=2),
            name=str(row.get("חלופה", f"חלופה {i+1}")),
        ))
    tgt_vals = [targets.get("foreign",0), targets.get("stocks",0), targets.get("fx",0), targets.get("illiquid",0), 0, 0]
    fig.add_trace(go.Scatterpolar(
        r=tgt_vals + [tgt_vals[0]], theta=categories + [categories[0]],
        mode="lines", line=dict(color="rgba(239,68,68,0.7)", width=1.5, dash="dot"), name="יעד",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=9)),
            angularaxis=dict(direction="clockwise"),
        ),
        showlegend=True, height=420,
        margin=dict(t=30, b=10, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.12),
        font=dict(family="sans-serif", size=11),
    )
    return fig

def _export_excel(top3, baseline=None):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        display_cols = [
            "חלופה", "יתרון", "קופות", "מסלולים", "משקלים",
            'חו"ל (%)', "מניות (%)", 'מט"ח (%)', "לא־סחיר (%)",
            "שארפ משוקלל", "שירות משוקלל", "score",
        ]
        cols_exist = [c for c in display_cols if c in top3.columns]
        sheet_df = top3[cols_exist].copy()

        # ── פיצ׳ר 4: הוסף עמודות מצב קיים ──
        if baseline:
            for key, col_name in [("foreign",'חו"ל קיים (%)'),("stocks","מניות קיים (%)"),
                                   ("fx",'מט"ח קיים (%)'),("illiquid","לא-סחיר קיים (%)")]:
                sheet_df[col_name] = baseline.get(key, "—")

        sheet_df.to_excel(writer, sheet_name="חלופות", index=False)

        for i, row in top3.iterrows():
            items = row.get("weights_items") or []
            if items:
                detail_df = pd.DataFrame(items)
                detail_df.columns = ["אחוז", "קרן", "מסלול"]
                sheet_name = f"חלופה {i+1}"[:31]
                detail_df.to_excel(writer, sheet_name=sheet_name, index=False)

    return output.getvalue()


# ─────────────────────────────────────────────
# Load data
# ─────────────────────────────────────────────
with st.spinner("🔄 טוען נתונים מ-Google Sheets..."):
    df_long, service_map, load_warnings = load_funds_long(FUNDS_GSHEET_ID, SERVICE_GSHEET_ID)
    if load_warnings:
        with st.expander('אזהרות טעינת נתונים', expanded=False):
            for w in load_warnings:
                st.warning(w)

if load_warnings:
    for w in load_warnings:
        st.warning(f"⚠️ {w}")

if df_long.empty:
    err_details = " | ".join(load_warnings) if load_warnings else "סיבה לא ידועה"
    st.error(
        f"❌ לא הצלחתי לטעון נתונים מ-Google Sheets.\n\n"
        f"**פרטי השגיאה:** {err_details}\n\n"
        "ודא שהגיליונות פתוחים לשיתוף ('Anyone with the link') ושמבנה הגיליון תקין."
    )
    st.stop()

n_tracks  = df_long["track"].nunique()
n_records = len(df_long)
all_funds = sorted(df_long["fund"].unique().tolist())


# ─────────────────────────────────────────────
# Session state defaults
# ─────────────────────────────────────────────
def _init_state():
    st.session_state.setdefault("n_funds",           2)
    st.session_state.setdefault("mix_policy",        "מותר לערבב מנהלים")
    st.session_state.setdefault("step",              5)
    st.session_state.setdefault("primary_rank",      "דיוק")
    st.session_state.setdefault("locked_fund",       "")
    st.session_state.setdefault("locked_amount",     0.0)   # פיצ׳ר 3
    st.session_state.setdefault("total_amount",      0.0)   # פיצ׳ר 3
    st.session_state.setdefault("selected_managers", None)
    st.session_state.setdefault("targets",      {"foreign": 30.0, "stocks": 40.0, "fx": 25.0, "illiquid": 20.0})
    st.session_state.setdefault("include",      {"foreign": True, "stocks": True, "fx": True, "illiquid": True})
    st.session_state.setdefault("constraint",   {
        "foreign":  ("רך", "בדיוק"),
        "stocks":   ("רך", "בדיוק"),
        "fx":       ("רך", "בדיוק"),
        "illiquid": ("רך", "בדיוק"),
    })
    st.session_state.setdefault("last_results",      None)
    st.session_state.setdefault("last_note",         "")
    st.session_state.setdefault("run_history",       [])
    # פיצ׳ר 1
    st.session_state.setdefault("portfolio_holdings",  None)
    st.session_state.setdefault("portfolio_baseline",  None)
    st.session_state.setdefault("portfolio_total",     0.0)
    st.session_state.setdefault("portfolio_managers",  [])
    # פיצ׳ר 2
    st.session_state.setdefault("quick_profile_active", None)
    st.session_state.setdefault("selected_alt", None)
    st.session_state.setdefault("voted_this_session", None)

_init_state()


# ─────────────────────────────────────────────
# Header – Premium Design
# ─────────────────────────────────────────────
portfolio_loaded = bool(st.session_state.get("portfolio_baseline"))
portfolio_total  = st.session_state.get("portfolio_total", 0.0)

st.markdown(f"""
<div class="app-header">
  <div class="app-logo">
    <div class="app-logo-icon">📊</div>
    <div>
      <div class="app-title">Profit Mix Optimizer</div>
      <div class="app-sub">מערכת אופטימיזציה לתמהיל מסלולי קרנות השתלמות</div>
    </div>
  </div>
  <div class="app-header-stats">
    <div class="header-stat">
      <div class="hval">{n_records:,}</div>
      <div class="hlbl">קופות במאגר</div>
    </div>
    <div class="header-stat">
      <div class="hval">{len(df_long['manager'].unique()):,}</div>
      <div class="hlbl">מנהלי השקעות</div>
    </div>
    {"<div class='header-stat'><div class='hval' style='color:#4ade80'>✅ טעון</div><div class='hlbl'>פורטפוליו נוכחי</div></div>" if portfolio_loaded else "<div class='header-stat'><div class='hval' style='color:#94a3b8'>—</div><div class='hlbl'>פורטפוליו נוכחי</div></div>"}
  </div>
</div>
""", unsafe_allow_html=True)

col_refresh_only, _ = st.columns([1, 5])
with col_refresh_only:
    if st.button("🔄 רענן נתונים", help="טוען מחדש נתונים מ-Google Sheets"):
        st.cache_data.clear()
        st.rerun()

all_managers = sorted(df_long["manager"].unique().tolist())

if st.session_state["selected_managers"] is None:
    st.session_state["selected_managers"] = all_managers.copy()
st.session_state["selected_managers"] = [m for m in st.session_state["selected_managers"] if m in all_managers]
if not st.session_state["selected_managers"]:
    st.session_state["selected_managers"] = all_managers.copy()

n_active_managers = len(st.session_state["selected_managers"])
n_total_managers  = len(all_managers)

# ─────────────────────────────────────────────
# Navigation  (above manager filter – item 7)
# ─────────────────────────────────────────────
NAV_OPTIONS = ["📂 פורטפוליו נוכחי", "⚙️ הגדרות יעד", "⚖️ השוואת מסלולים", "🕓 היסטוריה"]
st.session_state.setdefault("active_tab", "⚙️ הגדרות יעד")
if st.session_state.get("_next_active_tab") in NAV_OPTIONS:
    st.session_state["active_tab"] = st.session_state.pop("_next_active_tab")
st.markdown("<div class='nav-bar'>", unsafe_allow_html=True)
active_tab = st.radio(
    "ניווט", options=NAV_OPTIONS, horizontal=True, key="active_tab", label_visibility="collapsed",
)
st.markdown("</div>", unsafe_allow_html=True)

# ── Manager filter (item 6 fix: clear-all now works correctly) ──
with st.expander(
    f"🏢 סינון מנהלים — {'כולם נבחרו' if n_active_managers == n_total_managers else f'{n_active_managers}/{n_total_managers} נבחרו'}",
    expanded=False
):
    btn_col1, btn_col2, _ = st.columns([1, 1, 4])
    with btn_col1:
        if st.button("✅ בחר הכל", key="mgr_all", use_container_width=True):
            st.session_state["selected_managers"] = all_managers.copy()
            st.rerun()
    with btn_col2:
        if st.button("☐ נקה הכל", key="mgr_none", use_container_width=True):
            # Fix: set to a single placeholder so checkboxes render unchecked
            st.session_state["selected_managers"] = ["__none__"]
            st.rerun()
    st.markdown("---")
    mgr_cols = st.columns(4)
    new_selection = []
    for i, mgr_name in enumerate(all_managers):
        with mgr_cols[i % 4]:
            fund_count = df_long[df_long["manager"] == mgr_name]["fund"].nunique()
            checked = (mgr_name in st.session_state["selected_managers"])
            if st.checkbox(f"{mgr_name} ({fund_count})", value=checked, key=f"mgr_cb_{mgr_name}"):
                new_selection.append(mgr_name)
    if set(new_selection) != set(m for m in st.session_state["selected_managers"] if m != "__none__"):
        st.session_state["selected_managers"] = new_selection if new_selection else ["__none__"]
        st.rerun()

real_selected = [m for m in st.session_state["selected_managers"] if m != "__none__" and m in all_managers]
if real_selected and len(real_selected) < n_total_managers:
    df_active = df_long[df_long["manager"].isin(real_selected)].copy()
    st.info(f"🔍 מנותחות **{len(df_active)}** קרנות מתוך {n_records} (מנהלים: {', '.join(real_selected)})")
else:
    df_active = df_long

all_funds = sorted(df_active["fund"].unique().tolist())

# ─────────────────────────────────────────────
# פיצ׳ר 2: Quick Profile Buttons (item 2)
# ─────────────────────────────────────────────
st.markdown("""
<div class="profile-section">
  <div class="profile-title">🎯 הצגת מסלולי השקעה טהורים של:</div>
  <div class="profile-hint">לחץ על סוג המסלול הרצוי כדי לראות מיידית את הקרנות המובילות — <b>מסלול "טהור" = חשיפה של 90% ומעלה לאפיק זה</b></div>
</div>
""", unsafe_allow_html=True)

profile_cols = st.columns(len(QUICK_PROFILES))
for col, (profile_name, _) in zip(profile_cols, QUICK_PROFILES.items()):
    with col:
        if st.button(profile_name, use_container_width=True, key=f"profile_{profile_name}"):
            st.session_state["quick_profile_active"] = profile_name
            st.session_state["_next_active_tab"] = "⚖️ השוואת מסלולים"
            st.rerun()

if st.session_state["quick_profile_active"]:
    pname = st.session_state["quick_profile_active"]
    st.info(f"🎯 מסנן פעיל: **{pname}** — מציג קרנות עם חשיפה ≥90%")


# ─────────────────────────────────────────────
# Tab 0: Portfolio (פיצ׳ר 1)
# ─────────────────────────────────────────────
if active_tab == "📂 פורטפוליו נוכחי":
    st.subheader("📂 פורטפוליו נוכחי – ייבוא דו\"ח מסלקה")
    st.caption("העלה קובץ Excel שהורדת מגמל נט / אתר משרד האוצר (דו\"ח מסלקה). האפליקציה תשאב ממנו את ההחזקות הנוכחיות שלך.")

    uploaded = st.file_uploader(
        "העלאת דו\"ח מסלקה (Excel / XLSX)",
        type=["xlsx", "xls"],
        key="clearing_upload",
        help="קובץ Excel עם עמודות: שם קרן/גוף, שם מסלול, יתרה/ערך"
    )

    if uploaded:
        with st.spinner("מנתח דו\"ח מסלקה..."):
            xlsx_bytes = uploaded.read()
            result, err = parse_clearing_report(xlsx_bytes)

        if err or result is None:
            st.error(f"❌ שגיאה בניתוח הקובץ: {err}")
        else:
            holdings = result["holdings"]
            total    = result["total_amount"]

            # חשב baseline מהנתונים הנוכחיים של האפליקציה
            baseline = _compute_baseline_from_holdings(holdings, df_long)

            # שמור ב-session
            st.session_state["portfolio_holdings"] = holdings
            st.session_state["portfolio_baseline"] = baseline
            st.session_state["portfolio_total"]    = total
            st.session_state["portfolio_managers"] = list({h["manager"] for h in holdings if h["manager"]})

            st.success(f"✅ נטענו {len(holdings)} קרנות | סך נכסים: ₪{total:,.0f}")

            # הצגת ההחזקות
            st.subheader("ההחזקות שלך")
            holdings_df = pd.DataFrame(holdings)
            holdings_df["amount"]     = holdings_df["amount"].apply(lambda x: f"₪{x:,.0f}")
            holdings_df["weight_pct"] = holdings_df["weight_pct"].apply(lambda x: f"{x:.1f}%")
            holdings_df = holdings_df.rename(columns={"fund":"קרן","manager":"מנהל","track":"מסלול","amount":"סכום","weight_pct":"משקל"})
            st.dataframe(holdings_df, use_container_width=True, hide_index=True)

            # הצגת פרמטרי החשיפה הנוכחיים
            if baseline:
                st.subheader("פרמטרי החשיפה הנוכחיים (משוקללים)")
                st.caption("מחושב לפי ההתאמה לנתוני האפליקציה. ייתכנו אי-דיוקים בהתאם לאיכות ההתאמה.")

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("חו\"ל", f"{baseline['foreign']:.1f}%")
                m2.metric("מניות", f"{baseline['stocks']:.1f}%")
                m3.metric("מט\"ח", f"{baseline['fx']:.1f}%")
                m4.metric("לא-סחיר", f"{baseline['illiquid']:.1f}%")

                m5, m6, _, _ = st.columns(4)
                m5.metric("שארפ", f"{baseline['sharpe']:.2f}")
                m6.metric("ציון שירות", f"{baseline['service']:.0f}")

                # כפתור: מלא יעדים לפי מצב נוכחי
                st.divider()
                if st.button("📋 מלא יעדים לפי מצב נוכחי", type="primary"):
                    st.session_state["targets"]["foreign"]  = round(float(baseline["foreign"]),  1)
                    st.session_state["targets"]["stocks"]   = round(float(baseline["stocks"]),   1)
                    st.session_state["targets"]["fx"]       = round(float(baseline["fx"]),       1)
                    st.session_state["targets"]["illiquid"] = round(float(baseline["illiquid"]), 1)
                    st.session_state["include"]["foreign"]  = True
                    st.session_state["include"]["stocks"]   = True
                    st.session_state["_next_active_tab"] = "⚙️ הגדרות יעד"
                    st.success("✅ יעדים עודכנו! עוברים להגדרות...")
                    st.rerun()
            else:
                st.warning("⚠️ לא הצלחנו למצוא התאמה לנתוני האפליקציה. ניתן להזין יעדים ידנית בטאב הגדרות יעד.")

    elif st.session_state["portfolio_holdings"]:
        # פורטפוליו כבר טעון
        st.success(f"✅ פורטפוליו טעון — {len(st.session_state['portfolio_holdings'])} קרנות | ₪{st.session_state['portfolio_total']:,.0f}")
        baseline = st.session_state["portfolio_baseline"]
        if baseline:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("חו\"ל", f"{baseline['foreign']:.1f}%")
            m2.metric("מניות", f"{baseline['stocks']:.1f}%")
            m3.metric("מט\"ח", f"{baseline['fx']:.1f}%")
            m4.metric("לא-סחיר", f"{baseline['illiquid']:.1f}%")

        if st.button("🗑️ נקה פורטפוליו"):
            st.session_state["portfolio_holdings"] = None
            st.session_state["portfolio_baseline"] = None
            st.session_state["portfolio_total"]    = 0.0
            st.session_state["portfolio_managers"] = []
            st.rerun()

    else:
        st.info("לא הועלה דו\"ח מסלקה עדיין. ניתן לדלג ולהשתמש באפליקציה ללא פרטי פורטפוליו אישי.")
        st.markdown("""
        **מה ניתן לעשות ללא העלאה?**
        - הגדרת יעדים ידנית בטאב ⚙️ הגדרות יעד
        - כל הפונקציונליות הבסיסית זמינה

        **מה מתאפשר עם העלאת הדו"ח?**
        - מילוי אוטומטי של יעדים לפי מצבך הנוכחי
        - השוואה בין המצב המוצע למצב הקיים בכל חלופה
        - הצגת עוצמת השינוי הנדרשת (שינוי מסלול / ניוד)
        """)


# ─────────────────────────────────────────────
# Tab 1: Settings
# ─────────────────────────────────────────────
if active_tab == "⚙️ הגדרות יעד":
    # ── Compact 2-col layout for base settings ──
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        st.session_state["n_funds"] = st.selectbox(
            "מספר קופות לשלב", options=[1, 2, 3],
            index=[1, 2, 3].index(st.session_state["n_funds"]),
        )
    with c2:
        st.session_state["mix_policy"] = st.selectbox(
            "מדיניות מנהלים",
            options=["מותר לערבב מנהלים", "אותו מנהל בלבד"],
            index=0 if st.session_state["mix_policy"] == "מותר לערבב מנהלים" else 1,
        )
    with c3:
        lock_opts = ["ללא"] + all_funds
        lock_idx = 0
        if st.session_state["locked_fund"] in all_funds:
            lock_idx = all_funds.index(st.session_state["locked_fund"]) + 1
        locked = st.selectbox(
            "נעל קרן (אופציונלי)",
            options=lock_opts, index=lock_idx,
            help="האופטימייזר יסנן רק תמהילים הכוללים קרן זו",
        )
        st.session_state["locked_fund"] = "" if locked == "ללא" else locked

    # פיצ׳ר 3: locked amount – compact inline
    if st.session_state["locked_fund"]:
        la1, la2, la3 = st.columns(3)
        with la1:
            total_amt = st.number_input("סך לחלוקה (₪)", min_value=0.0,
                value=float(st.session_state["total_amount"] or st.session_state.get("portfolio_total", 0.0)),
                step=10000.0, format="%.0f")
            st.session_state["total_amount"] = total_amt
        with la2:
            max_locked = float(total_amt) if total_amt > 0 else 1e9
            locked_amt = st.number_input("סכום לקרן הנעולה (₪)", min_value=0.0, max_value=max_locked,
                value=float(min(st.session_state["locked_amount"], max_locked)), step=10000.0, format="%.0f")
            st.session_state["locked_amount"] = locked_amt
        with la3:
            if total_amt > 0 and locked_amt > 0:
                locked_pct = round(locked_amt / total_amt * 100, 1)
                st.metric("משקל נעול", f"{locked_pct:.1f}%")
            else:
                locked_pct = None
                st.metric("משקל נעול", "חופשי")
    else:
        locked_pct = None
        st.session_state["locked_amount"] = 0.0

    st.divider()

    st.markdown("""
    <div class="score-tip">
    💡 <b>Score</b> = סטיה מהיעד. 0 = התאמה מושלמת. <b>קשיח</b> = פסילה. <b>רך</b> = ניקוד בלבד.
    </div>
    """, unsafe_allow_html=True)

    header_cols = st.columns([1.4, 1.1, 1.3, 1.0, 1.1])
    for col, lbl in zip(header_cols, ["פרמטר", "כלול בדירוג", "יעד (%)", "קשיחות", "כיוון"]):
        col.markdown(f"**{lbl}**")

    def _metric_row(key, label, default_mode, max_val=100.0):
        cols = st.columns([1.4, 1.1, 1.3, 1.0, 1.1])
        with cols[0]: st.write(label)
        with cols[1]:
            inc = st.checkbox(" ", value=st.session_state["include"].get(key, False), key=f"inc_{key}")
        with cols[2]:
            val = st.slider(" ", 0.0, max_val,
                            float(st.session_state["targets"].get(key, 0.0)),
                            step=0.5, key=f"tgt_{key}", label_visibility="collapsed")
        with cols[3]:
            hard = st.selectbox(" ", ["רך", "קשיח"],
                                index=0 if st.session_state["constraint"].get(key, ("רך",))[0] == "רך" else 1,
                                key=f"hard_{key}", label_visibility="collapsed")
        with cols[4]:
            mode = st.selectbox(" ", ["בדיוק", "לפחות", "לכל היותר"],
                                index=["בדיוק", "לפחות", "לכל היותר"].index(
                                    st.session_state["constraint"].get(key, ("רך", default_mode))[1]),
                                key=f"mode_{key}", label_visibility="collapsed")
        st.session_state["include"][key]    = inc
        st.session_state["targets"][key]    = float(val)
        st.session_state["constraint"][key] = (hard, mode)

    _metric_row("foreign",  'חו"ל',     "בדיוק",       120.0)
    _metric_row("stocks",   "מניות",    "בדיוק")
    _metric_row("fx",       'מט"ח',     "בדיוק",       120.0)
    _metric_row("illiquid", "לא־סחיר",  "בדיוק")

    st.divider()
    run = st.button("🔍 חשב חלופות מיטביות", type="primary", use_container_width=True)

    if run:
        with st.spinner("מחשב... ⚡ (חיפוש מואץ עם NumPy)"):
            try:
                sols, note = find_best_solutions(
                    df=df_active,
                    n_funds=st.session_state["n_funds"],
                    step=st.session_state["step"],
                    mix_policy=st.session_state["mix_policy"],
                    include=st.session_state["include"],
                    constraint=st.session_state["constraint"],
                    targets=st.session_state["targets"],
                    primary_rank=st.session_state["primary_rank"],
                    locked_fund=st.session_state["locked_fund"],
                    locked_weight_pct=locked_pct,
                    max_solutions_scan=20000,
                )
                st.session_state["last_note"] = note
                if sols.empty:
                    st.session_state["last_results"] = None
                    st.error(f"לא נמצאו פתרונות. {note}")
                else:
                    top3 = _pick_three_distinct(sols, st.session_state["primary_rank"])
                    result = {
                        "solutions_all": sols.head(100),
                        "top3": top3,
                        "targets": dict(st.session_state["targets"]),
                        "ts": datetime.now().strftime("%H:%M:%S"),
                    }
                    del sols
                    st.session_state["last_results"] = result
                    # Reset vote for new results
                    st.session_state["voted_this_session"] = None
                    st.session_state["selected_alt"] = None
                    hist = st.session_state.get("run_history", [])
                    hist.insert(0, result)
                    st.session_state["run_history"] = hist[:2]
                    # JS scroll to results anchor
                    st.markdown("""
<script>
setTimeout(function(){
  var el = window.parent.document.getElementById('results-anchor');
  if(el){ el.scrollIntoView({behavior:'smooth', block:'start'}); }
}, 300);
</script>""", unsafe_allow_html=True)
            except Exception as _e:
                err_txt = traceback.format_exc()
                st.session_state["_last_error"] = err_txt
                st.error(f"שגיאה בחישוב: {_e}")


    # ── Inline Results ──
    res = st.session_state.get("last_results")
    if res is not None and active_tab == "⚙️ הגדרות יעד":
        targets_used = res.get("targets", {})
        df_head      = res.get("solutions_all")
        recs         = _pick_recommendations(df_head)
        baseline     = st.session_state.get("portfolio_baseline")

        if recs:
            st.markdown("<div id='results-anchor'></div>", unsafe_allow_html=True)
            st.markdown("---")
            note_disp = st.session_state.get("last_note", "")
            ts_disp   = res.get("ts", "")
            bl_total  = st.session_state.get("portfolio_total", 0)

            summary_parts = [f"<span style='color:#1e3a8a;font-weight:800'>חושב ב-{ts_disp}</span>"]
            if bl_total:
                summary_parts.append(f"פורטפוליו: <b>₪{bl_total:,.0f}</b>")
            if baseline:
                summary_parts.append("<span style='color:#10b981;font-weight:700'>✓ השוואה למצב קיים</span>")
            st.markdown(
                f"<div style='font-size:12px;color:#475569;margin-bottom:10px;text-align:right'>"
                f"{'&nbsp;&nbsp;|&nbsp;&nbsp;'.join(summary_parts)}"
                f"&nbsp;&nbsp;<span style='opacity:.6'>{_esc(note_disp)}</span></div>",
                unsafe_allow_html=True
            )

            rows: List[Dict] = []
            for _key, rrow, title in [
                ("weighted", recs["weighted"], "חלופה משוקללת"),
                ("accurate", recs["accurate"], "הכי מדויקת"),
                ("sharpe",   recs["sharpe"],   "שארפ מקסימלי"),
                ("service",  recs["service"],  "שירות מוביל"),
            ]:
                rrow = dict(rrow)
                rrow["חלופה"]         = title
                rrow["weights_items"] = _weights_items(rrow.get("weights"), rrow.get("קופות",""), rrow.get("מסלולים",""))
                rrow["משקלים"]        = _weights_short(rrow.get("weights"))
                rows.append(rrow)

            def _tracks_display(rrow: Dict) -> str:
                items = rrow.get("weights_items") or []
                parts = []
                for it in items:
                    pct   = str(it.get("pct","")).replace("%","").strip()
                    track = str(it.get("track","")).strip()
                    fund  = str(it.get("fund","")).strip()
                    label = track if track else fund
                    if label:
                        parts.append(f"<b>{pct}%</b> {_esc(label)}")
                return "<br>".join(parts) if parts else _esc(str(rrow.get("מסלולים","")))

            def _count_changes(rrow: Dict) -> str:
                holdings = st.session_state.get("portfolio_holdings") or []
                if not holdings: return "—"
                cur_managers = set(h["manager"].strip() for h in holdings if h.get("manager"))
                cur_tracks   = set(h["track"].strip()   for h in holdings if h.get("track"))
                prop_managers = [m.strip() for m in str(rrow.get("מנהלים","")).split("|") if m.strip()]
                prop_tracks   = [t.strip() for t in str(rrow.get("מסלולים","")).split("|") if t.strip()]
                nidud = shinui = 0
                for mgr, trk in zip(prop_managers, prop_tracks):
                    if mgr not in cur_managers: nidud += 1
                    elif trk not in cur_tracks: shinui += 1
                parts = []
                if shinui: parts.append(f"🔄 שינוי מסלול ×{shinui}")
                if nidud:  parts.append(f"🔁 ניוד ×{nidud}")
                if not parts: return "<span style='color:#16a34a;font-weight:700'>✅ ללא שינוי</span>"
                return "<br>".join(parts)

            has_baseline = baseline is not None
            has_holdings = bool(st.session_state.get("portfolio_holdings"))
            show_changes = has_holdings
            num_cols = ['חו"ל', "מניות", 'מט"ח', "לא-סחיר", "שארפ", "שירות"]
            row_keys = ['חו"ל (%)', "מניות (%)", 'מט"ח (%)', "לאדֹ-סחיר (%)", "שארפ משוקלל", "שירות משוקלל"]

            def _pct_fmt(v, key):
                try: return f"{float(v):.1f}%" if "%" in key else f"{float(v):.2f}"
                except: return "—"

            def _delta_style(proposed, current, lower_better=False):
                try:
                    diff = float(proposed) - float(current)
                    if abs(diff) < 0.05: return ""
                    good = (diff > 0 and not lower_better) or (diff < 0 and lower_better)
                    return f"color:{'#16a34a' if good else '#dc2626'};font-weight:800"
                except: return ""

            lower_better = {'חו"ל (%)': False, "מניות (%)": False, 'מט"ח (%)': False,
                            "לאדֹ-סחיר (%)": True, "שארפ משוקלל": False, "שירות משוקלל": False}

            change_th = "<th>שינויים</th>" if show_changes else ""
            header_html = (
                f"<tr>"
                f"<th style='min-width:100px'>חלופה</th>"
                f"<th style='min-width:160px'>מסלולים</th>"
                f"<th style='min-width:100px'>מנהלים</th>"
                f"{''.join(f'<th>{c}</th>' for c in num_cols)}"
                f"{change_th}"
                f"<th>▼ בחר</th>"
                f"</tr>"
            )

            selected_alt = st.session_state.get("selected_alt")

            def _make_row(label, d, row_style="", label_style="", is_alt=False, is_selected=False):
                cells = f"<td style='font-weight:800;{label_style}'>{_esc(label)}</td>"
                if d is not None and "weights_items" in d:
                    cells += f"<td style='font-size:11px;line-height:1.7'>{_tracks_display(d)}</td>"
                else:
                    cells += "<td>—</td>"
                if d is not None and "מנהלים" in d:
                    mgr_html = "<br>".join(_esc(m.strip()) for m in str(d.get("מנהלים","")).split("|") if m.strip())
                    cells += f"<td style='font-size:11px;color:#475569'>{mgr_html}</td>"
                else:
                    cells += "<td>—</td>"
                for col_lbl, col_key in zip(num_cols, row_keys):
                    if d is None:
                        cells += "<td>—</td>"
                    else:
                        val = d.get(col_key, d.get(col_lbl, "—"))
                        if col_key == "שארפ משוקלל" and is_alt:
                            if d.get("sharpe_incomplete") or (isinstance(val, float) and math.isnan(val)):
                                cells += "<td style='font-size:10px;color:#92400e'>לא כל המסלולים<br>פרסמו שארפ</td>"
                                continue
                        dstyle = ""
                        if has_baseline and is_alt:
                            cur = baseline.get({'חו"ל (%)': "foreign", "מניות (%)": "stocks",
                                'מט"ח (%)': "fx", "לאדֹ-סחיר (%)": "illiquid",
                                "שארפ משוקלל": "sharpe", "שירות משוקלל": "service"}.get(col_key,""), None)
                            if cur is not None:
                                dstyle = _delta_style(val, cur, lower_better.get(col_key, False))
                        cells += f"<td style='{dstyle}'>{_pct_fmt(val, col_key)}</td>"
                if show_changes:
                    cells += (f"<td style='font-size:11px'>{_count_changes(d)}</td>" if is_alt else "<td>—</td>")
                if is_alt:
                    icon = "✔" if is_selected else "○"
                    c = "#1e3a8a" if is_selected else "#94a3b8"
                    cells += f"<td style='font-weight:800;color:{c};font-size:16px'>{icon}</td>"
                else:
                    cells += "<td></td>"
                return f"<tr style='{row_style}'>{cells}</tr>"

            tgt_data = {
                'חו"ל (%)': targets_used.get("foreign","—"), "מניות (%)": targets_used.get("stocks","—"),
                'מט"ח (%)': targets_used.get("fx","—"), "לאדֹ-סחיר (%)": targets_used.get("illiquid","—"),
                "שארפ משוקלל": "—", "שירות משוקלל": "—",
            }
            bl_data = None
            if has_baseline:
                bl_data = {
                    'חו"ל (%)': baseline.get("foreign","—"), "מניות (%)": baseline.get("stocks","—"),
                    'מט"ח (%)': baseline.get("fx","—"), "לאדֹ-סחיר (%)": baseline.get("illiquid","—"),
                    "שארפ משוקלל": baseline.get("sharpe","—"), "שירות משוקלל": baseline.get("service","—"),
                }

            body_html = _make_row("🎯 יעדים", tgt_data,
                row_style="background:#fffbeb;border-bottom:2px solid #fde68a", label_style="color:#92400e")
            if bl_data:
                body_html += _make_row("📂 מצב קיים", bl_data,
                    row_style="background:#f0fdf4;border-bottom:2px solid #bbf7d0", label_style="color:#065f46")
            body_html += "<tr><td colspan='100' style='height:3px;background:#e2e8f0;padding:0'></td></tr>"

            alt_bg  = ["#eff6ff", "#fafafa", "#fafafa", "#f0fdf4"]
            alt_bdr = ["2px solid #bfdbfe", "none", "none", "2px solid #bbf7d0"]
            for i, rrow in enumerate(rows):
                is_sel = (rrow["חלופה"] == selected_alt)
                body_html += _make_row(
                    rrow["חלופה"], rrow,
                    row_style=f"background:{alt_bg[i]};border-bottom:{alt_bdr[i]}",
                    label_style="font-weight:900;color:#0f1e3d", is_alt=True, is_selected=is_sel,
                )

            st.markdown(f"""
<div style='overflow-x:auto;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;margin-bottom:6px'>
  <table class='res-tbl'>
    <thead>{header_html}</thead>
    <tbody>{body_html}</tbody>
  </table>
</div>""", unsafe_allow_html=True)
            st.caption("לחץ על שם חלופה כדי לבחור אותה ולראות פרטים וסטטיסטיקות")

            # ── Selection buttons row ──
            sel_cols = st.columns(len(rows))
            voting_configured = hasattr(st, "secrets") and "gcp_service_account" in st.secrets
            for col, rrow in zip(sel_cols, rows):
                with col:
                    label = rrow["חלופה"]
                    is_sel = (label == selected_alt)
                    if st.button(f"{'✔ ' if is_sel else ''}{label}", use_container_width=True,
                                 type="primary" if is_sel else "secondary", key=f"sel_{label}"):
                        if is_sel:
                            st.session_state["selected_alt"] = None
                        else:
                            st.session_state["selected_alt"] = label
                            if voting_configured:
                                ok = _write_vote(label, str(rrow.get("מנהלים","")), str(rrow.get("מסלולים","")))
                                if ok: _load_votes_cached.clear()
                        st.rerun()

            # ── Inline detail panel for selected alt ──
            if selected_alt:
                sel_row = next((r for r in rows if r["חלופה"] == selected_alt), None)
                with st.container():
                    st.markdown(f"""
<div style='background:#f0f9ff;border:1.5px solid #bae6fd;border-radius:12px;
padding:14px 18px 8px;margin:10px 0'>
  <div style='font-size:13px;font-weight:800;color:#0369a1;margin-bottom:8px;text-align:right'>
    📊 פרטי חלופה: {_esc(selected_alt)}
  </div>
</div>""", unsafe_allow_html=True)
                    if sel_row:
                        dc1, dc2, dc3, dc4 = st.columns(4)
                        with dc1:
                            st.metric('חו"ל', _pct_fmt(sel_row.get('חו"ל (%)', "—"), 'חו"ל (%)'))
                            st.metric("מניות", _pct_fmt(sel_row.get("מניות (%)", "—"), "מניות (%)"))
                        with dc2:
                            st.metric('מט"ח', _pct_fmt(sel_row.get('מט"ח (%)', "—"), 'מט"ח (%)'))
                            st.metric("לא-סחיר", _pct_fmt(sel_row.get("לאדֹ-סחיר (%)", "—"), "לאדֹ-סחיר (%)"))
                        with dc3:
                            sv = sel_row.get("שארפ משוקלל","—")
                            if sel_row.get("sharpe_incomplete") or (isinstance(sv, float) and math.isnan(sv)):
                                st.metric("שארפ", "—")
                                st.caption("⚠️ לא כל המסלולים פרסמו שארפ")
                            else:
                                st.metric("שארפ", _pct_fmt(sv,""))
                            st.metric("שירות", _pct_fmt(sel_row.get("שירות משוקלל","—"),""))
                        with dc4:
                            mgr_list = [m.strip() for m in str(sel_row.get("מנהלים","")).split("|") if m.strip()]
                            trk_list = [t.strip() for t in str(sel_row.get("מסלולים","")).split("|") if t.strip()]
                            st.markdown("**מנהלים:**")
                            for m in mgr_list: st.markdown(f"• {m}")
                            if trk_list:
                                st.markdown("**מסלולים:**")
                                for t in trk_list: st.markdown(f"• {t}")

                if voting_configured:
                    st.divider()
                    st.markdown("**📊 סטטיסטיקות בחירת כלל המשתמשים**")
                    _render_votes_stats()
                else:
                    st.caption("💡 הצבעות לא מופעלות — עקוב אחר `SETUP_VOTING.md` להגדרת Service Account")

            # ── Export ──
            top4 = pd.DataFrame(rows)
            excel_bytes = _export_excel(top4, baseline=baseline)
            exp_col, _ = st.columns([1, 5])
            with exp_col:
                st.download_button("⬇️ ייצוא לאקסל", data=excel_bytes,
                    file_name="profit_mix_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="dl_results_inline")

# Tab 3: Fund Comparison (with quick profile filter)
# ─────────────────────────────────────────────
if active_tab == "⚖️ השוואת מסלולים":
    # compact: no subheader/caption wasted space
    qp = st.session_state.get("quick_profile_active")
    if qp:
        profile_filters = QUICK_PROFILES.get(qp, {})
        filter_parts = []
        if "stocks_min"   in profile_filters: filter_parts.append(f"מניות ≥ {profile_filters['stocks_min']}%")
        if "stocks_max"   in profile_filters: filter_parts.append(f"מניות ≤ {profile_filters['stocks_max']}%")
        if "foreign_min"  in profile_filters: filter_parts.append(f"חו\"ל ≥ {profile_filters['foreign_min']}%")
        if "foreign_max"  in profile_filters: filter_parts.append(f"חו\"ל ≤ {profile_filters['foreign_max']}%")
        if "fx_min"       in profile_filters: filter_parts.append(f"מט\"ח ≥ {profile_filters['fx_min']}%")
        if "illiquid_max" in profile_filters: filter_parts.append(f"לא-סחיר ≤ {profile_filters['illiquid_max']}%")

        col_banner, col_clear = st.columns([5, 1])
        with col_banner:
            st.info(f"🎯 מסלול מהיר פעיל: **{qp}** — {' | '.join(filter_parts)}")
        with col_clear:
            st.markdown("<div style='padding-top:8px'>", unsafe_allow_html=True)
            if st.button("✖ נקה", key="clear_profile"):
                st.session_state["quick_profile_active"] = None
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    all_tracks = sorted(df_active["track"].unique().tolist())

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        compare_tracks = st.multiselect(
            "🔍 בחר לפי מסלול",
            options=all_tracks, placeholder="הקלד שם מסלול...",
        )
    with col_s2:
        compare_funds_direct = st.multiselect(
            "🔍 בחר לפי שם קרן ספציפית",
            options=all_funds, placeholder="הקלד שם קרן...", max_selections=10,
        )

    selected_rows = []
    for track in (compare_tracks or []):
        subset = df_active[df_active["track"] == track]
        if not subset.empty:
            for _, row in subset.sort_values("sharpe", ascending=False).iterrows():
                selected_rows.append(row)
    for fund_name in (compare_funds_direct or []):
        rows = df_active[df_active["fund"] == fund_name]
        if not rows.empty:
            selected_rows.append(rows.iloc[0])

    # פיצ׳ר 2: אם quick profile פעיל ואין בחירה ידנית — הצג את כל הקרנות שעומדות בתנאי
    if qp and not compare_tracks and not compare_funds_direct:
        pf = QUICK_PROFILES[qp]
        filtered_by_profile = df_active.copy()
        if "stocks_min"   in pf: filtered_by_profile = filtered_by_profile[filtered_by_profile["stocks"]   >= pf["stocks_min"]]
        if "stocks_max"   in pf: filtered_by_profile = filtered_by_profile[filtered_by_profile["stocks"]   <= pf["stocks_max"]]
        if "foreign_min"  in pf: filtered_by_profile = filtered_by_profile[filtered_by_profile["foreign"]  >= pf["foreign_min"]]
        if "foreign_max"  in pf: filtered_by_profile = filtered_by_profile[filtered_by_profile["foreign"]  <= pf["foreign_max"]]
        if "fx_min"       in pf: filtered_by_profile = filtered_by_profile[filtered_by_profile["fx"]       >= pf["fx_min"]]
        if "illiquid_max" in pf: filtered_by_profile = filtered_by_profile[filtered_by_profile["illiquid"] <= pf["illiquid_max"]]
        for _, row in filtered_by_profile.sort_values("sharpe", ascending=False).head(20).iterrows():
            selected_rows.append(row)
        if filtered_by_profile.empty:
            st.warning(f"לא נמצאו קרנות שעומדות בתנאי המסלול: {qp}")

    # De-duplicate
    seen_funds: set = set()
    unique_rows = []
    for r in selected_rows:
        key = str(r["fund"])
        if key not in seen_funds:
            seen_funds.add(key)
            unique_rows.append(r)

    if not unique_rows:
        st.info("בחר לפחות מסלול או קרן אחת כדי לראות את ההשוואה.")
    else:
        comp_data = []
        for r in unique_rows:
            comp_data.append({
                "קרן":          str(r.get("fund", "")),
                "מסלול":        str(r.get("track", "")),
                "מנהל":         str(r.get("manager", "")),
                'חו"ל (%)':     r.get("foreign",  np.nan),
                "ישראל (%)":    round(100.0 - float(r.get("foreign", 0) or 0), 2),
                "מניות (%)":    r.get("stocks",   np.nan),
                'מט"ח (%)':     r.get("fx",       np.nan),
                "לא־סחיר (%)":  r.get("illiquid", np.nan),
                "שארפ":         r.get("sharpe",   np.nan),
                "ציון שירות":   r.get("service",  np.nan),
            })
        comp_df = pd.DataFrame(comp_data)
        numeric_cols_cmp = ['חו"ל (%)', "ישראל (%)", "מניות (%)", 'מט"ח (%)', "לא־סחיר (%)", "שארפ", "ציון שירות"]

        with st.expander("🔎 סינון חכם – הצג רק שורות שעומדות בתנאי", expanded=qp is not None):
            st.caption("הגדר עד 3 תנאי סינון.")
            filters = []
            for fi in range(3):
                fc1, fc2, fc3 = st.columns([2, 1.5, 1.5])
                with fc1:
                    param = st.selectbox("פרמטר" if fi == 0 else " ", options=["—"] + numeric_cols_cmp, key=f"flt_param_{fi}", label_visibility="visible" if fi == 0 else "collapsed")
                with fc2:
                    direction = st.selectbox("כיוון" if fi == 0 else " ", options=["לפחות (≥)", "לכל היותר (≤)", "בדיוק (=)"], key=f"flt_dir_{fi}", label_visibility="visible" if fi == 0 else "collapsed")
                with fc3:
                    threshold = st.number_input("ערך" if fi == 0 else " ", value=0.0, step=1.0, key=f"flt_val_{fi}", label_visibility="visible" if fi == 0 else "collapsed")
                if param != "—":
                    filters.append((param, direction, float(threshold)))

        filtered_df = comp_df.copy()
        active_filter_desc = []
        for (param, direction, threshold) in filters:
            if param not in filtered_df.columns: continue
            col_numeric = pd.to_numeric(filtered_df[param], errors="coerce")
            if "לפחות" in direction:
                mask = col_numeric >= threshold
                active_filter_desc.append(f"{param} ≥ {threshold:.1f}")
            elif "לכל היותר" in direction:
                mask = col_numeric <= threshold
                active_filter_desc.append(f"{param} ≤ {threshold:.1f}")
            else:
                mask = col_numeric.between(threshold - 0.5, threshold + 0.5)
                active_filter_desc.append(f"{param} = {threshold:.1f}")
            filtered_df = filtered_df[mask]

        if active_filter_desc:
            n_before, n_after = len(comp_df), len(filtered_df)
            if n_after == 0:
                st.warning(f"אין שורות שעומדות בתנאי: {' | '.join(active_filter_desc)}")
                filtered_df = comp_df.copy()
            else:
                st.success(f"✅ מציג {n_after} מתוך {n_before} שורות — תנאי: {' | '.join(active_filter_desc)}")

        def _cell_bg(val, col_name, col_series):
            try:
                v = float(val)
                nums = col_series.dropna().astype(float).tolist()
                if len(nums) < 2: return ""
                mn, mx = min(nums), max(nums)
                if mx == mn: return ""
                ratio = 1.0 - (v - mn)/(mx - mn) if col_name == "לא־סחיר (%)" else (v - mn)/(mx - mn)
                g = int(220 + ratio * 35)
                r_ch = int(255 - ratio * 80)
                return f"background: rgba({r_ch},{g},200,0.28);"
            except Exception:
                return ""

        header_cells = "".join(f"<th>{_esc(c)}</th>" for c in filtered_df.columns)
        rows_html = ""
        for _, row in filtered_df.iterrows():
            cells = ""
            for col in filtered_df.columns:
                val   = row[col]
                style = _cell_bg(val, col, filtered_df[col]) if col in numeric_cols_cmp else ""
                if col in numeric_cols_cmp:
                    try:
                        dec = 1 if col in ["שארפ", "ציון שירות"] else 2
                        unit = "%" if "%" in col else ""
                        display = f"{float(val):.{dec}f}{unit}"
                    except Exception:
                        display = "—"
                else:
                    display = _esc(str(val))
                cells += f"<td style='{style}'>{display}</td>"
            rows_html += f"<tr>{cells}</tr>"

        st.markdown(f"""
        <style>
        .cmp-table {{
          width:100%; border-collapse:separate; border-spacing:0;
          border:1px solid #e2e8f0; border-radius:12px; overflow:hidden;
          font-size:13px; direction:rtl; margin-top:4px;
        }}
        .cmp-table th {{
          background:#0f172a; color:#f8fafc; padding:10px 12px;
          font-weight:700; white-space:nowrap; text-align:right;
        }}
        .cmp-table td {{
          padding:9px 12px; border-bottom:1px solid #f1f5f9;
          text-align:right; vertical-align:middle;
        }}
        .cmp-table tr:last-child td {{ border-bottom:none; }}
        .cmp-table tr:hover td {{ filter:brightness(0.97); }}
        @media (prefers-color-scheme:dark) {{
          .cmp-table {{ border-color:#334155; }}
          .cmp-table td {{ border-color:#1e293b; color:#cbd5e1; }}
        }}
        </style>
        <div style="overflow-x:auto">
          <table class="cmp-table">
            <thead><tr>{header_cells}</tr></thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>
        <p style="font-size:11px;color:#94a3b8;margin-top:6px;">
          🟢 ירוק = ערך גבוה יותר (טוב יותר) | 🔴 אדום = ערך נמוך יותר | עבור לא-סחיר: הפוך
        </p>
        """, unsafe_allow_html=True)

        # ── Bar chart comparison (compact, no radar) ──
        bc1, bc2 = st.columns([2, 1])
        with bc2:
            bar_metric = st.selectbox("השוואה לפי:", options=['חו"ל (%)', "מניות (%)", 'מט"ח (%)', "לא־סחיר (%)", "שארפ", "ציון שירות"], key="cmp_bar_metric", label_visibility="collapsed")
        bar_df = filtered_df[["קרן", bar_metric]].dropna().sort_values(bar_metric, ascending=False)
        if not bar_df.empty:
            unit = "%" if "%" in bar_metric else ""
            colors = ["#2563eb"] * len(bar_df)
            if len(bar_df) > 1:
                colors[0] = "#16a34a"; colors[-1] = "#ef4444"
                if bar_metric == "לא־סחיר (%)": colors[0], colors[-1] = "#ef4444", "#16a34a"
            fig_bar = go.Figure(go.Bar(
                x=bar_df["קרן"], y=bar_df[bar_metric],
                marker_color=colors,
                text=bar_df[bar_metric].apply(lambda v: f"{v:.1f}{unit}"),
                textposition="outside",
            ))
            fig_bar.update_layout(
                height=260, margin=dict(t=20, b=70, l=10, r=10),
                xaxis=dict(tickangle=-30, tickfont=dict(size=10)),
                yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            )
            with bc1:
                _safe_plotly(fig_bar)

        cmp_out = io.BytesIO()
        with pd.ExcelWriter(cmp_out, engine="openpyxl") as writer:
            filtered_df.to_excel(writer, sheet_name="השוואת מסלולים", index=False)
        st.download_button(
            "⬇️ ייצוא לאקסל", data=cmp_out.getvalue(),
            file_name="fund_comparison.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


# ─────────────────────────────────────────────
# Tab 4: Transparency (hidden from nav – kept for debug)
# ─────────────────────────────────────────────
if active_tab == "🔍 שקיפות":  # tab removed from nav; accessible only programmatically
    st.subheader("פירוט חישוב")
    if st.session_state.get("_last_error"):
        with st.expander("⚠️ שגיאה אחרונה (לדיבוג)", expanded=True):
            st.code(st.session_state["_last_error"], language="python")

    with st.expander("פרמטרי הריצה האחרונה"):
        st.json({
            "מספר קופות":   st.session_state["n_funds"],
            "מדיניות":      st.session_state["mix_policy"],
            "צעד":          st.session_state["step"],
            "דירוג ראשי":   st.session_state["primary_rank"],
            "קרן נעולה":    st.session_state["locked_fund"] or "ללא",
            "משקל נעול":    f"{st.session_state.get('locked_amount',0)/st.session_state.get('total_amount',1)*100:.1f}%" if st.session_state.get('total_amount',0) > 0 and st.session_state.get('locked_amount',0) > 0 else "חופשי",
            "כולל בדירוג":  st.session_state["include"],
            "יעדים":        st.session_state["targets"],
            "קשיחות/כיוון": {k: list(v) for k, v in st.session_state["constraint"].items()},
            "הערת ריצה":    st.session_state.get("last_note", ""),
            "פורטפוליו טעון": "כן" if st.session_state.get("portfolio_baseline") else "לא",
        }, expanded=False)

    res = st.session_state.get("last_results")
    if res is None:
        st.info("אין נתונים – הרץ חיפוש תחילה.")
    else:
        st.markdown("**מועמדים (200 ראשונים לאחר מיון):**")
        cand = res["solutions_all"].head(200).copy()
        show_cols = ["מנהלים", "קופות", "מסלולים", 'חו"ל (%)', "מניות (%)", 'מט"ח (%)', "לא־סחיר (%)", "שארפ משוקלל", "שירות משוקלל", "score", "weights"]
        exist = [c for c in show_cols if c in cand.columns]
        cand = cand[exist].copy()
        if "weights" in cand.columns:
            cand["משקלים"] = cand["weights"].apply(lambda w: " / ".join(f"{int(x)}%" for x in w) if isinstance(w, (tuple, list)) else str(w))
            cand = cand.drop(columns=["weights"])
        cand = cand.rename(columns={"score": "Score"})
        st.dataframe(cand, use_container_width=True, hide_index=True,
                     column_config={"קופות": st.column_config.TextColumn(width="large"), "מסלולים": st.column_config.TextColumn(width="large")})


# ─────────────────────────────────────────────
# Tab 5: History
# ─────────────────────────────────────────────
if active_tab == "🕓 היסטוריה":
    st.subheader("🕓 3 ריצות אחרונות")
    history = st.session_state.get("run_history", [])
    if not history:
        st.info("עדיין לא בוצעה ריצה.")
    else:
        for hi, h_res in enumerate(history):
            ts = h_res.get("ts", f"ריצה {hi+1}")
            tgts = h_res.get("targets", {})
            tgt_str = " | ".join(f"{k}={v:.0f}%" for k, v in tgts.items())
            with st.expander(f"🕐 {ts}  –  יעדים: {tgt_str}"):
                h_top3 = h_res.get("top3")
                if h_top3 is not None and not h_top3.empty:
                    for _, row in h_top3.iterrows():
                        funds  = row.get("קופות", "")
                        weights = row.get("משקלים", "")
                        score  = row.get("score", "")
                        alt    = row.get("חלופה", "")
                        st.markdown(f"**{alt}** — {funds} ({weights}) — Score: {score:.4f}" if isinstance(score, float) else f"**{alt}** — {funds}")
                    excel_h = _export_excel(h_top3)
                    st.download_button(
                        "⬇️ ייצוא ריצה זו", data=excel_h,
                        file_name=f"profit_mix_{ts.replace(':','-')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"hist_dl_{hi}",
                    )


st.caption("© Profit Mix Optimizer v3.0 | ישראל = 100% − חו״ל | חיפוש מואץ עם NumPy vectorized")
