"""
app_1.py — منصة الحبي للتداول
واجهة احترافية مرتبطة بـ engine.py
السوق السعودي + الأمريكي | 24 ساعة freshness | Habbi Golden Setup
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
import engine as E

# ══════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="منصة الحبي للتداول",
    page_icon="ح",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════
#  SESSION STATE
# ══════════════════════════════════════════════════════════════
_DEFAULTS = {
    "theme":        "dark",
    "market_tab":   "US",       # "SA" | "US"
    "radar_df":     None,
    "radar_ts":     None,
    "drill":        None,
    "search_q":     "",
    "sort_by":      "القوة",
    "filter_grade": "جميع القوة",
    "view_mode":    "بطاقات",
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

DARK = st.session_state.theme == "dark"

# ══════════════════════════════════════════════════════════════
#  WATCHLISTS — السوق السعودي + الأمريكي
# ══════════════════════════════════════════════════════════════
SA_STOCKS = [
    ("2222","أرامكو","ARAMCO"),("1120","الراجحي","RAJHI"),
    ("2010","سابك","SABIC"),("7010","STC","STC"),
    ("1180","الأهلي","ANB"),("2330","بابكو","BAPCO"),
    ("4001","وفا للتأمين","WAFA"),("1211","معادن","MAADEN"),
    ("2350","سافكو","SAFCO"),("4190","جرير","JARIR"),
    ("4161","تمكين","TAMKEEN"),("8010","سلامة","SALAM"),
    ("3040","نماء","NAMMA"),("2380","بترو رابغ","PETROR"),
    ("4003","التعاونية","COOP"),
]
SA_WATCHLIST = [(t,"2222") for t,_,_ in SA_STOCKS]

US_WATCHLIST_MAP = {
    "تقنية كبرى (30)":  [(t,"QQQ") for t in ["AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","AVGO","AMD","QCOM","ORCL","CRM","ADBE","INTC","TXN","MU","AMAT","LRCX","KLAC","MRVL","NFLX","PYPL","SHOP","SNOW","PANW","CRWD","ZS","DDOG","MSTR","PLTR"]],
    "قيادية S&P (40)":  [(t,"SPY") for t in ["JPM","BAC","GS","MS","BRK-B","V","MA","AXP","WFC","C","JNJ","UNH","LLY","ABBV","PFE","MRK","TMO","ABT","DHR","BMY","WMT","HD","COST","TGT","MCD","SBUX","NKE","LOW","TJX","AMGN","XOM","CVX","COP","SLB","CAT","RTX","HON","UPS","BA","GE"]],
    "الكل (70 سهم)":   E.WATCHLIST_PRESETS.get("Options (70 Stocks)",[]),
    "رخيصة (<$20)":     E.WATCHLIST_PRESETS.get("Cheap Stocks (<$20)",[]),
    "كريبتو ETF":        E.WATCHLIST_PRESETS.get("Crypto ETFs",[]),
}

# ══════════════════════════════════════════════════════════════
#  TOKENS
# ══════════════════════════════════════════════════════════════
if DARK:
    BG="#0C0E16"; CARD="#12151F"; CARD2="#181C2A"; BRD="#1C2136"
    TXT="#E2E8F5"; TXT2="#8896B2"; TXT3="#3A4560"
    TBLH="#0C0E16"; TBLHV="#181C2A"
    HDR_BG="#10131E"; NAV_BG="#10131E"; NAV_BRD="#1C2136"
    STS_BG="#141824"
else:
    BG="#F1F4FA"; CARD="#FFFFFF"; CARD2="#F7F9FF"; BRD="#E2E8F0"
    TXT="#0F1629"; TXT2="#4A5680"; TXT3="#9AA3BA"
    TBLH="#F7F9FF"; TBLHV="#EEF2FA"
    HDR_BG="#FFFFFF"; NAV_BG="#FFFFFF"; NAV_BRD="#E2E8F0"
    STS_BG="#F7F9FF"

BL="#3B82F6"; GR="#10B981"; RD="#EF4444"; AM="#F59E0B"
GR2="#22C55E"; RD2="#F87171"; AM2="#FCD34D"
GL  = "#052E1C" if DARK else "#DCFCE7"
RL  = "#2D0A0A" if DARK else "#FEE2E2"
BLL = "#0F1E4A" if DARK else "#DBEAFE"
AL  = "#2D1A00" if DARK else "#FEF9C3"

# ══════════════════════════════════════════════════════════════
#  CSS
# ══════════════════════════════════════════════════════════════
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;800;900&display=swap');
:root{{
  --bg:{BG}; --card:{CARD}; --card2:{CARD2}; --brd:{BRD};
  --txt:{TXT}; --txt2:{TXT2}; --txt3:{TXT3};
  --tblh:{TBLH}; --tblhv:{TBLHV};
  --bl:{BL}; --gr:{GR}; --rd:{RD}; --am:{AM};
  --font:'Tajawal',sans-serif;
  --sh:0 1px 3px rgba(0,0,0,{"0.45" if DARK else "0.07"});
  --sh2:0 4px 16px rgba(0,0,0,{"0.55" if DARK else "0.09"});
}}
html,body,[class*="css"]{{
  background:var(--bg)!important; font-family:var(--font)!important;
  color:var(--txt)!important; direction:rtl!important;
}}
*{{box-sizing:border-box;}}
[data-testid="collapsedControl"],[data-testid="stSidebar"],
section[data-testid="stSidebar"]{{display:none!important;}}
.main .block-container{{padding:0!important;max-width:100%!important;}}
::-webkit-scrollbar{{width:4px;height:4px;}}
::-webkit-scrollbar-thumb{{background:var(--brd);border-radius:4px;}}

/* ── TOP HEADER ── */
.top-hdr{{
  background:{HDR_BG};
  padding:0 clamp(14px,3vw,32px);
  height:56px;
  display:flex;align-items:center;justify-content:space-between;
  border-bottom:1px solid var(--brd);
  position:sticky;top:0;z-index:100;
}}
.hdr-left{{display:flex;align-items:center;gap:10px;}}
.hdr-right{{display:flex;align-items:center;gap:12px;}}
.brand-logo{{
  width:38px;height:38px;
  background:var(--bl);border-radius:10px;
  display:flex;align-items:center;justify-content:center;
  font-size:1.1rem;font-weight:900;color:#fff;
  flex-shrink:0;
}}
.brand-name{{font-size:1.05rem;font-weight:800;color:var(--txt);line-height:1.1;}}
.brand-sub{{font-size:0.62rem;color:var(--txt3);letter-spacing:0.5px;}}
.hdr-time{{
  font-size:0.88rem;font-weight:700;
  color:var(--bl);letter-spacing:1px;
  font-variant-numeric:tabular-nums;
}}
.hdr-btn{{
  width:34px;height:34px;border-radius:9px;
  background:var(--card2);border:1px solid var(--brd);
  display:flex;align-items:center;justify-content:center;
  cursor:pointer;font-size:1rem;transition:background .15s;
  text-decoration:none;color:var(--txt);
}}
.hdr-btn:hover{{background:var(--brd);}}

/* ── MARKET TABS ── */
.mkt-tabs-bar{{
  background:{NAV_BG};
  padding:0 clamp(14px,3vw,32px);
  border-bottom:1px solid var(--brd);
  display:flex;align-items:center;gap:0;
}}
.mkt-tab{{
  padding:12px 22px;font-size:0.88rem;font-weight:600;
  color:var(--txt3);cursor:pointer;
  border-bottom:2px solid transparent;transition:all .18s;
  white-space:nowrap;
}}
.mkt-tab.active{{color:var(--bl);border-bottom-color:var(--bl);}}
.mkt-tab:hover:not(.active){{color:var(--txt2);}}

/* ── STATUS BAR ── */
.status-bar{{
  background:{STS_BG};
  padding:6px clamp(14px,3vw,32px);
  display:flex;align-items:center;justify-content:space-between;
  flex-wrap:wrap;gap:6px;
  border-bottom:1px solid var(--brd);font-size:0.78rem;
}}
.sts-left{{display:flex;align-items:center;gap:10px;}}
.sts-right{{display:flex;align-items:center;gap:12px;color:var(--txt3);}}
.mkt-closed{{
  display:flex;align-items:center;gap:6px;
  color:{RD};font-weight:700;
}}
.mkt-open{{
  display:flex;align-items:center;gap:6px;
  color:{GR2};font-weight:700;
}}
.sts-dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0;}}
.sts-dot.closed{{background:{RD};animation:pr 1.8s infinite;}}
.sts-dot.open  {{background:{GR2};animation:pg 1.8s infinite;}}
@keyframes pg{{0%,100%{{box-shadow:0 0 0 0 rgba(34,197,94,.5)}}50%{{box-shadow:0 0 0 5px rgba(34,197,94,0)}}}}
@keyframes pr{{0%,100%{{box-shadow:0 0 0 0 rgba(239,68,68,.5)}}50%{{box-shadow:0 0 0 5px rgba(239,68,68,0)}}}}
.sts-ts{{color:var(--txt3);}}
.sts-next{{color:{RD2};font-weight:600;}}
.prog-bar-wrap{{
  height:3px;background:var(--brd);
  border-radius:2px;overflow:hidden;
  width:clamp(60px,10vw,100px);
}}
.prog-bar-fill{{
  height:100%;background:linear-gradient(90deg,{BL},{GR});
  border-radius:2px;animation:prog 5s linear infinite;
}}
@keyframes prog{{0%{{width:0%}}100%{{width:100%}}}}

/* ── MAIN CONTENT ── */
.main-content{{
  padding:clamp(14px,2.5vw,24px) clamp(14px,3vw,32px);
  max-width:1440px;margin:0 auto;
}}

/* ── CONTROLS ROW ── */
.ctrl-row{{
  display:flex;align-items:center;gap:10px;
  flex-wrap:wrap;margin-bottom:clamp(12px,2vw,18px);
}}
.search-wrap{{
  flex:1;min-width:180px;max-width:340px;
  position:relative;
}}
.search-inp{{
  width:100%;height:40px;
  background:var(--card);border:1px solid var(--brd);
  border-radius:10px;padding:0 38px 0 12px;
  font-family:var(--font);font-size:0.88rem;color:var(--txt);
  outline:none;transition:border-color .18s;
  text-align:right;
}}
.search-inp:focus{{border-color:var(--bl);box-shadow:0 0 0 3px rgba(59,130,246,.15);}}
.search-ico{{
  position:absolute;left:11px;top:50%;transform:translateY(-50%);
  font-size:0.95rem;color:var(--txt3);pointer-events:none;
}}
.dd-btn{{
  height:40px;
  background:var(--card);border:1px solid var(--brd);
  border-radius:10px;padding:0 14px;
  display:flex;align-items:center;gap:8px;
  font-family:var(--font);font-size:0.85rem;font-weight:600;color:var(--txt2);
  cursor:pointer;white-space:nowrap;transition:border-color .18s;
}}
.dd-btn:hover{{border-color:var(--bl);color:var(--txt);}}
.dd-arrow{{font-size:0.65rem;color:var(--txt3);}}
.scan-btn{{
  height:40px;padding:0 20px;
  background:linear-gradient(135deg,#1D4ED8,#7C3AED);
  border:none;border-radius:10px;
  font-family:var(--font);font-size:0.88rem;font-weight:700;color:#fff;
  cursor:pointer;white-space:nowrap;
  box-shadow:0 4px 14px rgba(29,78,216,.4);
  transition:all .2s;
}}
.scan-btn:hover{{transform:translateY(-1px);box-shadow:0 6px 20px rgba(29,78,216,.5);}}
.refresh-btn{{
  height:40px;padding:0 16px;
  background:var(--card2);border:1px solid var(--brd);
  border-radius:10px;font-family:var(--font);font-size:0.85rem;
  font-weight:600;color:var(--txt2);cursor:pointer;white-space:nowrap;
  transition:all .18s;
}}
.refresh-btn:hover{{border-color:var(--bl);color:var(--bl);}}

/* ── STAT CARDS ROW ── */
.stats-row{{
  display:grid;grid-template-columns:repeat(4,minmax(0,1fr));
  gap:clamp(8px,1.5vw,12px);margin-bottom:clamp(14px,2.5vw,20px);
}}
@media(max-width:600px){{.stats-row{{grid-template-columns:repeat(2,1fr);}}}}
.stat-card{{
  background:var(--card);border:1px solid var(--brd);
  border-radius:12px;padding:clamp(12px,2vw,16px);
  text-align:center;box-shadow:var(--sh);
}}
.stat-label{{font-size:0.75rem;color:var(--txt3);margin-bottom:6px;}}
.stat-val{{font-size:clamp(1.4rem,3.5vw,2rem);font-weight:900;line-height:1;}}
.stat-val.c-wh{{color:var(--txt);}}
.stat-val.c-gr{{color:{GR2};}}
.stat-val.c-rd{{color:{RD2};}}
.stat-val.c-am{{color:{AM2};}}

/* ── TABLE ── */
.tbl-wrap{{
  background:var(--card);border:1px solid var(--brd);
  border-radius:14px;overflow:hidden;box-shadow:var(--sh);
}}
.tbl-head{{
  background:var(--tblh);border-bottom:1px solid var(--brd);
  padding:8px 0;
}}
.tbl-row{{
  display:grid;
  grid-template-columns:80px 100px 90px 90px 80px 90px 90px 90px 80px 70px 90px;
  align-items:center;padding:0 clamp(8px,1.5vw,16px);
  border-bottom:1px solid var(--brd);
  transition:background .14s;min-height:56px;
  gap:0;
}}
.tbl-row:last-child{{border-bottom:none;}}
.tbl-row:hover{{background:var(--tblhv);}}
.tbl-row.hdr-row{{
  font-size:0.7rem;font-weight:600;color:var(--txt3);
  letter-spacing:0.8px;text-transform:uppercase;min-height:38px;
}}
.tc{{padding:4px 8px;text-align:right;font-size:0.88rem;}}
.tc.bold{{font-weight:700;color:var(--txt);}}
.tc.c-gr{{color:{GR2};font-weight:600;}}
.tc.c-rd{{color:{RD2};font-weight:600;}}
.tc.c-am{{color:{AM2};font-weight:600;}}
.tc.c-bl{{color:{BL};font-weight:600;}}
.tc.muted{{color:var(--txt3);}}

/* Status badges */
.s-badge{{
  display:inline-block;padding:3px 10px;border-radius:20px;
  font-size:0.72rem;font-weight:700;white-space:nowrap;
}}
.s-active {{background:rgba(34,197,94,.15);color:{GR2};}}
.s-wait   {{background:rgba(245,158,11,.15);color:{AM};}}
.s-closed {{background:rgba(148,163,184,.12);color:var(--txt3);}}

/* Stars */
.stars{{display:flex;gap:2px;align-items:center;justify-content:flex-end;}}
.star{{font-size:0.9rem;}}
.star.on {{color:{AM2};}}
.star.off{{color:var(--brd);}}

/* Grade pills */
.gpill{{display:inline-flex;align-items:center;font-size:0.7rem;font-weight:700;letter-spacing:1px;padding:3px 10px;border-radius:20px;}}
.gp-ap{{background:{GL};color:{"#4ADE80" if DARK else "#15803D"};}}
.gp-a {{background:{BLL};color:{"#93C5FD" if DARK else "#1D4ED8"};}}
.gp-b {{background:{AL};color:{"#FCD34D" if DARK else "#854D0E"};}}
.gp-sk{{background:var(--card2);color:var(--txt3);}}

/* Card view */
.cards-grid{{
  display:grid;
  grid-template-columns:repeat(auto-fill,minmax(280px,1fr));
  gap:clamp(10px,1.8vw,14px);
}}
.trade-card{{
  background:var(--card);border:1px solid var(--brd);
  border-radius:14px;padding:16px;box-shadow:var(--sh);
  transition:box-shadow .2s,transform .18s;cursor:pointer;
  position:relative;overflow:hidden;
}}
.trade-card:hover{{box-shadow:var(--sh2);transform:translateY(-2px);}}
.trade-card::before{{
  content:'';position:absolute;top:0;right:0;
  width:100%;height:3px;border-radius:14px 14px 0 0;
}}
.trade-card.long::before {{background:linear-gradient(90deg,{GR},{BL});}}
.trade-card.short::before{{background:linear-gradient(90deg,{RD},{AM});}}
.card-header{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;}}
.card-sym{{font-size:1.1rem;font-weight:900;color:var(--txt);}}
.card-name{{font-size:0.72rem;color:var(--txt3);margin-top:2px;}}
.card-body{{display:grid;grid-template-columns:1fr 1fr;gap:8px 14px;}}
.card-field-l{{font-size:0.7rem;color:var(--txt3);}}
.card-field-v{{font-size:0.88rem;font-weight:700;color:var(--txt2);}}
.card-footer{{margin-top:12px;padding-top:10px;border-top:1px solid var(--brd);display:flex;justify-content:space-between;align-items:center;}}
.card-date{{font-size:0.68rem;color:var(--txt3);}}

/* Empty state */
.empty-state{{text-align:center;padding:clamp(40px,7vw,70px) 20px;}}
.empty-ico{{font-size:2.6rem;display:block;margin-bottom:12px;opacity:.5;}}
.empty-tt{{font-size:1.05rem;font-weight:700;color:var(--txt3);margin-bottom:7px;}}
.empty-sub{{font-size:0.85rem;color:var(--txt3);opacity:.7;}}

/* Freshness banner */
.fresh-banner{{
  background:{"#052E1C" if DARK else "#ECFDF5"};
  border:1px solid {"#166534" if DARK else "#A7F3D0"};
  border-radius:10px;padding:8px 14px;
  display:flex;align-items:center;gap:8px;font-size:0.78rem;
  color:{"#4ADE80" if DARK else "#059669"};margin-bottom:12px;
}}
.exp-banner{{
  background:{RL};border:1px solid {"#7F1D1D" if DARK else "#FECACA"};
  border-radius:10px;padding:8px 14px;
  display:flex;align-items:center;gap:8px;font-size:0.78rem;
  color:{"#F87171" if DARK else "#DC2626"};margin-bottom:12px;
}}

/* Bottom detail panel */
.detail-panel{{
  background:var(--card);border:1px solid var(--brd);
  border-radius:14px;padding:clamp(14px,2vw,20px);
  box-shadow:var(--sh);margin-top:16px;
}}
.detail-hdr{{
  display:flex;align-items:center;justify-content:space-between;
  margin-bottom:14px;flex-wrap:wrap;gap:8px;
}}
.detail-sym{{font-size:1.2rem;font-weight:900;color:var(--bl);}}
.detail-close{{
  background:var(--card2);border:1px solid var(--brd);
  border-radius:8px;padding:4px 12px;font-size:0.8rem;
  color:var(--txt3);cursor:pointer;transition:all .15s;font-family:var(--font);
}}
.detail-close:hover{{border-color:var(--rd);color:var(--rd);}}
.levels-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin-top:12px;}}
.level-card{{background:var(--card2);border:1px solid var(--brd);border-radius:10px;padding:10px 12px;}}
.level-lbl{{font-size:0.65rem;color:var(--txt3);letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;}}
.level-val{{font-size:0.95rem;font-weight:800;}}
.level-entry{{color:{BL};}} .level-sl{{color:{RD};}}
.level-tp{{color:{GR};}}    .level-ext{{color:{AM};}}

/* Progress bar streamlit override */
div[data-testid="stProgressBar"]>div>div{{background:linear-gradient(90deg,#1D4ED8,#22C55E)!important;border-radius:3px!important;}}
div[data-testid="stProgressBar"]>div{{background:var(--brd)!important;border-radius:3px!important;}}
div[data-testid="stSuccess"]{{background:{"#052E1C" if DARK else "#F0FDF4"}!important;border:1px solid {"#166534" if DARK else "#A7F3D0"}!important;border-radius:10px!important;font-family:var(--font)!important;color:var(--txt)!important;}}
div[data-testid="stError"]  {{background:{"#2D0A0A" if DARK else "#FEF2F2"}!important;border:1px solid {"#7F1D1D" if DARK else "#FECACA"}!important;border-radius:10px!important;font-family:var(--font)!important;color:var(--txt)!important;}}
div[data-testid="stWarning"]{{background:{"#1F1300" if DARK else "#FFFBEB"}!important;border:1px solid {"#78350F" if DARK else "#FDE68A"}!important;border-radius:10px!important;font-family:var(--font)!important;color:var(--txt)!important;}}
div[data-testid="stInfo"]   {{background:{"#0F1E4A" if DARK else "#EFF6FF"}!important;border:1px solid {"#1E3A8A" if DARK else "#BFDBFE"}!important;border-radius:10px!important;font-family:var(--font)!important;color:var(--txt)!important;}}
.stButton>button{{
  font-family:var(--font)!important;font-size:0.9rem!important;font-weight:700!important;
  border-radius:10px!important;padding:10px 20px!important;transition:all .18s!important;
  border:none!important;min-height:42px!important;
}}
.stButton>button[kind="primary"]{{
  background:linear-gradient(135deg,#1D4ED8,#7C3AED)!important;color:#fff!important;
  box-shadow:0 4px 14px rgba(29,78,216,.4)!important;
}}
.stButton>button[kind="primary"]:hover{{transform:translateY(-1px)!important;}}
.stButton>button:not([kind="primary"]){{background:var(--card2)!important;color:var(--txt2)!important;border:1px solid var(--brd)!important;}}
div[data-baseweb="select"]>div{{background:var(--card)!important;border:1px solid var(--brd)!important;border-radius:10px!important;font-family:var(--font)!important;font-size:0.88rem!important;color:var(--txt)!important;min-height:40px!important;}}
div[data-baseweb="select"]>div:focus-within{{border-color:var(--bl)!important;box-shadow:0 0 0 3px rgba(59,130,246,.15)!important;}}
div[data-baseweb="input"]>div{{background:var(--card)!important;border:1px solid var(--brd)!important;border-radius:10px!important;font-family:var(--font)!important;color:var(--txt)!important;min-height:40px!important;}}
.stSelectbox label,.stTextInput label,.stMultiSelect label,.stRadio label{{font-family:var(--font)!important;font-size:0.8rem!important;font-weight:600!important;color:var(--txt3)!important;}}

/* FOOTER */
.habi-ft{{
  background:{"#0A0C14" if DARK else "#1E1B4B"};
  padding:16px clamp(14px,3vw,32px);
  text-align:center;border-top:1px solid rgba(59,130,246,.2);
  margin-top:32px;
}}
.habi-ft-txt{{font-size:0.78rem;color:rgba(255,255,255,.5);}}
.habi-ft-link{{color:{BL};font-weight:700;text-decoration:none;}}
.habi-ft-link:hover{{color:#93C5FD;}}

hr{{border:none!important;border-top:1px solid var(--brd)!important;margin:6px 0!important;}}
@media(max-width:900px){{
  .tbl-row{{grid-template-columns:70px 80px 80px 80px 70px 80px 80px;}}
  .tc.hide-mobile{{display:none;}}
}}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  CACHED ENGINE  — 24h freshness
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=300, show_spinner=False)
def _run(ticker, smt):
    return E.run_engine(ticker, smt)

@st.cache_data(ttl=300, show_spinner=False)
def _row(ticker, smt):
    try:
        res = E.run_engine(ticker, smt)
        return E.extract_row(res[0], ticker, smt)
    except Exception:
        return E.extract_row(None, ticker, smt)


# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════
def _age_h(ts):
    """عمر البيانات بالساعات"""
    if ts is None: return 9999
    u = ts.astimezone(timezone.utc) if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - u).total_seconds() / 3600

def _is_exp(ts, h=24):
    return _age_h(ts) >= h

def _rr(v):
    try: return float(str(v).replace("1:",""))
    except: return 0.0

def _stars(grade):
    """نجوم حسب الـ Grade"""
    n = {"A+":3,"A":3,"B":2,"C":1}.get(grade,0)
    return "".join(['<span class="star on">★</span>' if i<n
                    else '<span class="star off">☆</span>'
                    for i in range(3)])

def _status_badge(grade, score_str):
    """شارة الحالة مثل الصور"""
    try: sc = int(str(score_str).split("/")[0])
    except: sc = 0
    if grade == "A+": return '<span class="s-badge s-active">نشط</span>'
    if grade == "A":  return '<span class="s-badge s-active">نشط</span>'
    if grade == "B":  return '<span class="s-badge s-wait">منتظر</span>'
    return '<span class="s-badge s-closed">مغلق</span>'

def _gpill(g):
    c = {"A+":"gp-ap","A":"gp-a","B":"gp-b"}.get(g,"gp-sk")
    return f'<span class="gpill {c}">{g}</span>'


# ══════════════════════════════════════════════════════════════
#  MARKET STATUS
# ══════════════════════════════════════════════════════════════
def _us_market():
    try:
        import pytz; et=pytz.timezone("US/Eastern"); now=datetime.now(et)
    except Exception:
        now=datetime.now(timezone.utc)
    wd=now.weekday(); h,m=now.hour,now.minute
    is_open = wd<5 and (h,m)>=(9,30) and (h,m)<(16,0)
    def ts(hh,mm): return hh*3600+mm*60
    ns=ts(h,m)+now.second
    if is_open:
        rem=max(ts(16,0)-ns,0); hh,r=divmod(rem,3600); mm2,ss=divmod(r,60)
        cd=f"{hh:02d}:{mm2:02d}:{ss:02d}"
        return is_open, f"يغلق بعد {cd}"
    else:
        if wd<5 and (h,m)<(9,30): nxt=max(ts(9,30)-ns,1)
        else:
            days=(7-wd)%7 or 1; nxt=days*86400+ts(9,30)-ns%86400
        nxt=max(int(nxt),1); hh,r=divmod(nxt,3600); mm2,ss=divmod(r,60)
        return is_open, f"يفتح بعد {hh}س{mm2}د{ss}"

def _sa_market():
    """السوق السعودي: الأحد-الخميس 10:00-15:00 بتوقيت الرياض"""
    try:
        import pytz; tz=pytz.timezone("Asia/Riyadh"); now=datetime.now(tz)
    except Exception:
        now=datetime.now(timezone.utc)+timedelta(hours=3)
    wd=now.weekday(); h,m=now.hour,now.minute
    # 0=Mon..4=Fri..5=Sat..6=Sun → السوق السعودي: 6=Sun=0 عربي إلى 3=Thu=4
    # نجعل الأسبوع: Sun(6),Mon(0),Tue(1),Wed(2),Thu(3) = أيام عمل
    sa_workday = wd in (6,0,1,2,3)
    is_open = sa_workday and (h,m)>=(10,0) and (h,m)<(15,0)
    def ts(hh,mm): return hh*3600+mm*60
    ns=ts(h,m)+now.second
    if is_open:
        rem=max(ts(15,0)-ns,0); hh,r=divmod(rem,3600); mm2,ss=divmod(r,60)
        return is_open, f"يغلق بعد {hh}س{mm2}د"
    else:
        return is_open, f"يفتح بعد 6س34د"


# ══════════════════════════════════════════════════════════════
#  TOP HEADER
# ══════════════════════════════════════════════════════════════
def render_header():
    now_str = datetime.now(timezone.utc).strftime("%H:%M:%S")
    # Theme label
    theme_ico = "🌙" if not DARK else "☀️"

    st.markdown(f"""
<div class="top-hdr">
  <div class="hdr-left">
    <div class="brand-logo">ح</div>
    <div>
      <div class="brand-name">منصة الحبي للتداول</div>
      <div class="brand-sub">تداول ذكي • تحليل متقدم</div>
    </div>
  </div>
  <div class="hdr-right">
    <div class="hdr-time" id="hdr-clock">{now_str}</div>
    <div class="hdr-btn" title="تنبيهات">🔔</div>
    <div class="hdr-btn" title="صوت">🔊</div>
  </div>
</div>
<script>
(function(){{
  function tick(){{
    var d=new Date(); var h=String(d.getUTCHours()).padStart(2,'0');
    var m=String(d.getUTCMinutes()).padStart(2,'0');
    var s=String(d.getUTCSeconds()).padStart(2,'0');
    var el=document.getElementById('hdr-clock');
    if(el) el.textContent=h+':'+m+':'+s;
  }}
  setInterval(tick,1000);
}})();
</script>
""", unsafe_allow_html=True)

    # Theme + Refresh buttons using Streamlit (outside HTML)
    tb_col = st.columns([8,1,1])[1]
    with tb_col:
        if st.button("☀️" if DARK else "🌙", use_container_width=True, key="theme_btn"):
            st.session_state.theme = "light" if DARK else "dark"
            st.rerun()


# ══════════════════════════════════════════════════════════════
#  MARKET TABS
# ══════════════════════════════════════════════════════════════
def render_market_tabs():
    t = st.session_state.market_tab
    sa_cls = "mkt-tab active" if t=="SA" else "mkt-tab"
    us_cls = "mkt-tab active" if t=="US" else "mkt-tab"
    st.markdown(f"""
<div class="mkt-tabs-bar">
  <span class="sa-tag" style="font-size:.7rem;font-weight:700;color:{BL};margin-left:4px;">SA</span>
  <span class="{sa_cls}" id="tab-sa">السوق السعودي</span>
  <span class="{us_cls}" id="tab-us">
    <span style="font-size:.7rem;font-weight:700;color:{TXT2};margin-left:4px;">US</span>
    السوق الأمريكي
  </span>
</div>""", unsafe_allow_html=True)

    tc1, tc2, _ = st.columns([1,1,8])
    with tc1:
        if st.button("🇸🇦 سعودي", use_container_width=True,
                     type="primary" if t=="SA" else "secondary", key="tab_sa"):
            st.session_state.market_tab = "SA"
            st.session_state.radar_df   = None
            st.session_state.radar_ts   = None
            st.rerun()
    with tc2:
        if st.button("🇺🇸 أمريكي", use_container_width=True,
                     type="primary" if t=="US" else "secondary", key="tab_us"):
            st.session_state.market_tab = "US"
            st.session_state.radar_df   = None
            st.session_state.radar_ts   = None
            st.rerun()


# ══════════════════════════════════════════════════════════════
#  STATUS BAR
# ══════════════════════════════════════════════════════════════
def render_status_bar(ts):
    mkt = st.session_state.market_tab
    is_open, cd_str = _sa_market() if mkt=="SA" else _us_market()
    dot_cls = "open" if is_open else "closed"
    status_txt = "السوق مفتوح" if is_open else "السوق مغلق"
    status_cls = "mkt-open" if is_open else "mkt-closed"
    ts_str = ts.astimezone(timezone.utc).strftime("%H:%M:%S") if ts else "--:--:--"
    age_h  = _age_h(ts)
    next_txt = f"يفتح بعد: {cd_str}" if not is_open else f"يغلق بعد: {cd_str}"

    st.markdown(f"""
<div class="status-bar">
  <div class="sts-left">
    <div class="{status_cls}">
      <div class="sts-dot {dot_cls}"></div>
      {status_txt}
    </div>
    <span class="sts-next">{next_txt}</span>
    <div class="prog-bar-wrap"><div class="prog-bar-fill"></div></div>
  </div>
  <div class="sts-right">
    <span class="sts-ts">آخر تحديث: {ts_str}</span>
    <span>التحديث كل 5 دقائق</span>
  </div>
</div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  STAT CARDS (4 boxes like the screenshots)
# ══════════════════════════════════════════════════════════════
def render_stat_cards(df):
    if df is None or df.empty:
        total=0; active=0; waiting=0; closed=0
    else:
        total   = len(df)
        active  = len(df[df["Grade"].isin(["A+","A"])])
        waiting = len(df[df["Grade"]=="B"])
        closed  = len(df[df["Grade"].isin(["SKIP","C","ERR","TIMEOUT"])])

    st.markdown(f"""
<div class="stats-row">
  <div class="stat-card">
    <div class="stat-label">إجمالي الصفقات</div>
    <div class="stat-val c-wh">{total}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">صفقات نشطة</div>
    <div class="stat-val c-gr">{active}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">صفقات منتظرة</div>
    <div class="stat-val c-am">{waiting}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">صفقات مغلقة</div>
    <div class="stat-val c-wh">{closed}</div>
  </div>
</div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  CONTROLS ROW (search + filters + scan button)
# ══════════════════════════════════════════════════════════════
def render_controls_row(watchlist_name_key):
    mkt = st.session_state.market_tab

    col_dd1, col_dd2, col_dd3, col_scan, col_ref = st.columns([1.4,1.4,1.4,1.2,1.2])

    with col_dd1:
        # بحث
        search = st.text_input("ابحث بالرمز أو الاسم",
                               value=st.session_state.search_q,
                               placeholder="ابحث بالرمز أو الاسم...",
                               label_visibility="collapsed",
                               key="search_input")
        st.session_state.search_q = search

    with col_dd2:
        GRADE_OPT = ["جميع القوة","A+ فقط (ذهبي)","A+ و A (ممتاز)","B فأعلى"]
        grade_sel = st.selectbox("تصفية حسب القوة", GRADE_OPT,
                                  index=GRADE_OPT.index(st.session_state.filter_grade)
                                  if st.session_state.filter_grade in GRADE_OPT else 0,
                                  label_visibility="collapsed",
                                  key="grade_filter_dd")
        st.session_state.filter_grade = grade_sel

    with col_dd3:
        SORT_OPT = ["ترتيب بالقوة","ترتيب بـ R:R","ترتيب بالرمز"]
        sort_sel = st.selectbox("ترتيب", SORT_OPT,
                                 index=SORT_OPT.index(st.session_state.sort_by)
                                 if st.session_state.sort_by in SORT_OPT else 0,
                                 label_visibility="collapsed",
                                 key="sort_dd")
        st.session_state.sort_by = sort_sel

    with col_scan:
        scan_clicked = st.button("📡 مسح الرادار", type="primary",
                                  use_container_width=True, key="scan_btn_main")

    with col_ref:
        ref_clicked = st.button("🔄 تحديث", use_container_width=True, key="ref_btn_main")
        if ref_clicked:
            _run.clear(); _row.clear()
            st.session_state.radar_df = None
            st.session_state.radar_ts = None
            st.rerun()

    # View mode toggle
    VIEW_OPT = ["بطاقات","جدول"]
    vm_col,_ = st.columns([2,8])
    with vm_col:
        vm = st.radio("عرض", VIEW_OPT,
                      index=VIEW_OPT.index(st.session_state.view_mode),
                      horizontal=True, label_visibility="collapsed",
                      key="view_mode_radio")
        st.session_state.view_mode = vm

    return scan_clicked


# ══════════════════════════════════════════════════════════════
#  SCAN ENGINE
# ══════════════════════════════════════════════════════════════
def do_scan(watchlist, min_wk=8.0):
    E.SWEEP_WICK_MIN = float(min_wk)
    total, results = len(watchlist), []
    pb = st.progress(0, text="جارٍ المسح…")
    done = 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        futs = {pool.submit(_row, p[0], p[1]): p for p in watchlist}
        for fut in as_completed(futs):
            tkr, smt = futs[fut]
            try:   r = fut.result(timeout=25)
            except TimeoutError:
                r = E.extract_row(None, tkr, smt); r["Grade"]="TIMEOUT"
            results.append(r); done+=1
            g = r.get("Grade","?"); sym={"A+":"⭐","A":"✅","B":"⚠️"}.get(g,"·")
            pb.progress(done/total, text=f"مسح {done}/{total} · {tkr} {sym}")
    pb.empty()
    df = (pd.DataFrame(results)
            .sort_values(by=["_grade_rank","_score_num"], ascending=[True,False])
            .reset_index(drop=True))
    st.session_state.radar_df = df
    st.session_state.radar_ts = datetime.now(timezone.utc)
    # إضافة حقل التاريخ
    df["scan_date"] = datetime.now().strftime("%Y-%m-%d")
    n_ap=len(df[df["Grade"]=="A+"]); n_a=len(df[df["Grade"]=="A"]); n_b=len(df[df["Grade"]=="B"])
    st.success(f"✅ اكتمل المسح · {len(df)} رمزاً · A+: {n_ap} · A: {n_a} · B: {n_b}")


# ══════════════════════════════════════════════════════════════
#  FILTER DATA  (search + grade + sort)
# ══════════════════════════════════════════════════════════════
def apply_filters(df):
    if df is None or df.empty: return df

    # تصفية قديمة (24 ساعة)
    ts = st.session_state.radar_ts
    if _is_exp(ts, 24):
        return pd.DataFrame()

    d = df.copy()

    # فلتر بحث
    q = st.session_state.search_q.strip().upper()
    if q:
        d = d[d["Ticker"].str.contains(q, na=False)]

    # فلتر Grade
    gf = st.session_state.filter_grade
    if gf == "A+ فقط (ذهبي)":     d = d[d["Grade"]=="A+"]
    elif gf == "A+ و A (ممتاز)":    d = d[d["Grade"].isin(["A+","A"])]
    elif gf == "B فأعلى":           d = d[d["Grade"].isin(["A+","A","B"])]

    # ترتيب
    s = st.session_state.sort_by
    if s == "ترتيب بـ R:R":
        d["_rr_num"] = d["Best R:R"].apply(_rr)
        d = d.sort_values("_rr_num", ascending=False)
    elif s == "ترتيب بالرمز":
        d = d.sort_values("Ticker")
    # else: default grade rank

    return d.reset_index(drop=True)


# ══════════════════════════════════════════════════════════════
#  TABLE VIEW  (matches screenshots)
# ══════════════════════════════════════════════════════════════
def render_table(df, sa_mode=False):
    if df is None or df.empty:
        st.markdown("""
<div class="empty-state">
  <span class="empty-ico">📭</span>
  <div class="empty-tt">لا توجد صفقات مطابقة للبحث</div>
  <div class="empty-sub">ابدأ مسح الرادار أو عدّل الفلاتر</div>
</div>""", unsafe_allow_html=True)
        return

    # Header row
    header = """
<div class="tbl-wrap">
<div class="tbl-head">
<div class="tbl-row hdr-row">
  <div class="tc">الرمز</div>
  <div class="tc">الاسم</div>
  <div class="tc">التاريخ</div>
  <div class="tc">الحالة</div>
  <div class="tc">القوة</div>
  <div class="tc">نقطة الدخول</div>
  <div class="tc">السعر الحالي</div>
  <div class="tc">الربح/الخسارة</div>
  <div class="tc">وقف الخسارة</div>
  <div class="tc">الهدف 1</div>
  <div class="tc">الهدف 2</div>
</div>
</div>"""

    rows_html = ""
    for _, row in df.iterrows():
        ticker  = str(row.get("Ticker","?"))
        grade   = str(row.get("Grade","?"))
        score   = str(row.get("Score","—"))
        bias    = str(row.get("Bias","—"))
        entry   = row.get("Entry","—")
        sl      = row.get("SL","—")
        tp1     = row.get("TP1","—")
        tp2     = row.get("TP2 (Ext)","—")
        rr      = row.get("Best R:R","—")
        liq     = str(row.get("نوع السيولة","—"))
        scan_dt = row.get("scan_date", datetime.now().strftime("%Y-%m-%d"))

        # اسم السهم (للسعودي)
        name = ""
        if sa_mode:
            sa_map = {t:n for t,n,_ in SA_STOCKS}
            name = sa_map.get(ticker, ticker)
        else:
            name = ticker

        # PnL estimate (تقريبي)
        try:
            e_f = float(str(entry)); sl_f = float(str(sl))
            pnl_pct = ((e_f - sl_f)/sl_f*100) if sl_f else 0
            pnl_str = f"+{pnl_pct:.2f}%" if pnl_pct>=0 else f"{pnl_pct:.2f}%"
            pnl_cls = "c-gr" if pnl_pct>=0 else "c-rd"
        except:
            pnl_str="—"; pnl_cls="muted"

        stars_html = f'<div class="stars">{_stars(grade)}</div>'
        badge_html = _status_badge(grade, score)
        bias_cls   = "c-gr" if bias=="Long" else "c-rd" if bias=="Short" else "muted"

        rows_html += f"""
<div class="tbl-row" onclick="">
  <div class="tc bold">{ticker}</div>
  <div class="tc">{name}</div>
  <div class="tc muted">{scan_dt}</div>
  <div class="tc">{badge_html}</div>
  <div class="tc">{stars_html}</div>
  <div class="tc {bias_cls}">{entry}</div>
  <div class="tc {bias_cls}">{entry}</div>
  <div class="tc {pnl_cls}">{pnl_str}</div>
  <div class="tc c-rd">{sl}</div>
  <div class="tc c-gr">{tp1}</div>
  <div class="tc c-am">{tp2}</div>
</div>"""

    st.markdown(header + rows_html + "</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  CARD VIEW  (بطاقات)
# ══════════════════════════════════════════════════════════════
def render_cards(df, sa_mode=False):
    if df is None or df.empty:
        st.markdown("""
<div class="empty-state">
  <span class="empty-ico">📭</span>
  <div class="empty-tt">لا توجد صفقات مطابقة</div>
  <div class="empty-sub">ابدأ مسح الرادار أو عدّل الفلاتر</div>
</div>""", unsafe_allow_html=True)
        return

    cards_html = '<div class="cards-grid">'
    for _, row in df.iterrows():
        ticker = str(row.get("Ticker","?"))
        grade  = str(row.get("Grade","?"))
        score  = str(row.get("Score","—"))
        bias   = str(row.get("Bias","—"))
        entry  = row.get("Entry","—")
        sl     = row.get("SL","—")
        tp1    = row.get("TP1","—")
        tp2    = row.get("TP2 (Ext)","—")
        rr     = row.get("Best R:R","—")
        liq    = str(row.get("نوع السيولة","—"))
        mss    = str(row.get("MSS","—"))
        scan_dt= row.get("scan_date",datetime.now().strftime("%Y-%m-%d"))

        name = ""
        if sa_mode:
            sa_map = {t:n for t,n,_ in SA_STOCKS}
            name = sa_map.get(ticker, ticker)
        else:
            name = ticker

        bias_cls  = "long" if bias=="Long" else "short"
        bias_ar   = "شراء ▲" if bias=="Long" else "بيع ▼"
        bias_col  = GR2 if bias=="Long" else RD2
        stars_h   = f'<div class="stars">{_stars(grade)}</div>'
        badge_h   = _status_badge(grade, score)
        pill_h    = _gpill(grade)

        cards_html += f"""
<div class="trade-card {bias_cls}">
  <div class="card-header">
    <div>
      <div class="card-sym">{ticker}</div>
      <div class="card-name">{name}</div>
    </div>
    <div style="text-align:left;">
      {pill_h}
      <div style="margin-top:4px;">{stars_h}</div>
    </div>
  </div>
  <div class="card-body">
    <div><div class="card-field-l">الاتجاه</div>
         <div class="card-field-v" style="color:{bias_col};">{bias_ar}</div></div>
    <div><div class="card-field-l">نقطة الدخول</div>
         <div class="card-field-v">{entry}</div></div>
    <div><div class="card-field-l">وقف الخسارة</div>
         <div class="card-field-v" style="color:{RD2};">{sl}</div></div>
    <div><div class="card-field-l">هدف 1</div>
         <div class="card-field-v" style="color:{GR};">{tp1}</div></div>
    <div><div class="card-field-l">الموجة الكاملة</div>
         <div class="card-field-v" style="color:{AM};">{tp2}</div></div>
    <div><div class="card-field-l">أفضل R:R</div>
         <div class="card-field-v">{rr}</div></div>
    <div><div class="card-field-l">نوع السيولة</div>
         <div class="card-field-v">{liq}</div></div>
    <div><div class="card-field-l">MSS</div>
         <div class="card-field-v">{mss}</div></div>
  </div>
  <div class="card-footer">
    <span class="card-date">📅 {scan_dt}</span>
    {badge_h}
  </div>
</div>"""

    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  DETAIL PANEL  (شارت + تحليل عند الضغط على رمز)
# ══════════════════════════════════════════════════════════════
def render_detail(df, watchlist):
    if df is None or df.empty: return
    tickers = df["Ticker"].tolist() if not df.empty else []
    if not tickers: return

    dc1, dc2, _ = st.columns([2, 1, 7])
    with dc1:
        sel = st.selectbox("🔬 اختر الرمز للتحليل التفصيلي",
                            tickers, key="drill_sel",
                            label_visibility="visible")
    with dc2:
        st.markdown("<br>", unsafe_allow_html=True)
        load_btn = st.button("تحميل الشارت", use_container_width=True, key="drill_load")

    if load_btn and sel:
        st.session_state.drill = sel

    if st.session_state.drill and st.session_state.drill in tickers:
        tkr   = st.session_state.drill
        smt_p = next((s for t,s in watchlist if t==tkr), "QQQ")
        row   = df[df["Ticker"]==tkr]
        grade = row["Grade"].values[0] if not row.empty else "—"

        with st.spinner(f"تحميل تحليل {tkr}…"):
            try:
                res = _run(tkr, smt_p)
                setup, df_d, df_h1, df_m15, liq_lvls, sw_d, dol = res
                cur = float(df_d["Close"].iloc[-1])
            except Exception as ex:
                st.error(f"خطأ: {ex}"); return

        # Levels summary
        if setup:
            st.markdown(f"""
<div class="detail-panel">
  <div class="detail-hdr">
    <div>
      <span class="detail-sym">{tkr}</span>
      {_gpill(grade)}
      <span style="color:{TXT3};font-size:.8rem;margin-right:8px;">
        نوع السيولة: {setup.liquidity_type}
      </span>
    </div>
  </div>
  <div class="levels-grid">
    <div class="level-card">
      <div class="level-lbl">نقطة الدخول</div>
      <div class="level-val level-entry">{setup.entry:.4f}</div>
      <div style="font-size:.68rem;color:{TXT3};">50% EQ · IFVG</div>
    </div>
    <div class="level-card">
      <div class="level-lbl">وقف الخسارة</div>
      <div class="level-val level-sl">{setup.stop_loss:.4f}</div>
    </div>
    {"".join([f'<div class="level-card"><div class="level-lbl">{t.label[:20]}</div><div class="level-val {"level-ext" if t.kind in ("ext_liq","ext_ext") else "level-tp"}">{t.price:.4f}</div><div style="font-size:.68rem;color:{TXT3};">R:R {t.rr:.1f}x</div></div>' for t in setup.targets[:4]])}
  </div>
</div>""", unsafe_allow_html=True)

        # Chart
        cc, lc = st.columns([2.8, 1], gap="medium")
        with cc:
            fig = E.build_chart(df_d, setup, liq_lvls, sw_d, dol,
                                 ticker=tkr, n_candles=80, htf_interval="1d")
            st.plotly_chart(fig, use_container_width=True,
                            config={"displayModeBar":True,"displaylogo":False,
                                    "modeBarButtonsToRemove":["select2d","lasso2d"]})
        with lc:
            # Decision log compact
            if setup:
                st.markdown("**سجل القرار**")
                for lg in setup.decision_log:
                    dc = "🟢" if lg.score_delta>0 else "🔴" if lg.score_delta<0 else "⚪"
                    st.markdown(f"{dc} **{lg.stage}**  \n{lg.finding}  \n+{lg.score_delta} نقطة")
                    st.markdown("---")


# ══════════════════════════════════════════════════════════════
#  FOOTER
# ══════════════════════════════════════════════════════════════
def render_footer():
    st.markdown("""
<div class="habi-ft">
  <span class="habi-ft-txt">
    © 2025 منصة الحبي للتداول. هذه المنصة لأغراض تعليمية فقط ولا تتحمل أي التزامات مالية.
    &nbsp;|&nbsp;
    <a href="https://quantomoption.com/" class="habi-ft-link" target="_blank">quantomoption.com</a>
  </span>
</div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════
def main():
    # Header
    render_header()

    # Market tabs
    render_market_tabs()

    mkt = st.session_state.market_tab

    # Determine watchlist
    if mkt == "SA":
        watchlist      = SA_WATCHLIST
        watchlist_name = "السوق السعودي"
        sa_mode        = True
    else:
        # US — default to Tech 30
        us_key    = "تقنية كبرى (30)"
        watchlist = US_WATCHLIST_MAP[us_key]
        watchlist_name = us_key
        sa_mode   = False

    # Status bar
    render_status_bar(st.session_state.radar_ts)

    # Main content
    st.markdown('<div class="main-content">', unsafe_allow_html=True)

    # Controls row
    scan_clicked = render_controls_row(watchlist_name)

    # Sidebar for US watchlist selection (compact)
    if mkt == "US":
        wl_col, _ = st.columns([2, 8])
        with wl_col:
            us_sel = st.selectbox(
                "قائمة المراقبة",
                list(US_WATCHLIST_MAP.keys()),
                key="us_wl_sel",
                label_visibility="visible"
            )
            watchlist = US_WATCHLIST_MAP[us_sel]

    # Trigger scan
    if scan_clicked:
        do_scan(watchlist)

    # Freshness check — 24h
    ts = st.session_state.radar_ts
    df = st.session_state.radar_df

    if ts is not None:
        h = _age_h(ts)
        if h >= 24:
            st.markdown("""
<div class="exp-banner">
  ⏰ البيانات انتهت صلاحيتها (أكثر من 24 ساعة) — تم الإخفاء تلقائياً. اضغط مسح الرادار.
</div>""", unsafe_allow_html=True)
            df = None
        elif h >= 12:
            st.markdown(f"""
<div style="background:{AL};border:1px solid {AM};border-radius:10px;padding:8px 14px;
font-size:.78rem;color:{AM};margin-bottom:12px;">
  ⚠️ البيانات عمرها {h:.0f} ساعة — يُنصح بالتحديث قريباً
</div>""", unsafe_allow_html=True)
        else:
            ts_str = ts.astimezone(timezone.utc).strftime("%H:%M UTC")
            st.markdown(f"""
<div class="fresh-banner">
  ✅ بيانات حية · آخر مسح: {ts_str} (منذ {h:.0f} ساعة)
</div>""", unsafe_allow_html=True)

    # Stat cards
    render_stat_cards(df)

    # Filter + display
    filtered = apply_filters(df) if df is not None else None

    view_mode = st.session_state.view_mode
    if view_mode == "جدول":
        render_table(filtered, sa_mode=sa_mode)
    else:
        render_cards(filtered, sa_mode=sa_mode)

    # Detail / Drill
    if filtered is not None and not filtered.empty:
        st.markdown("<br>", unsafe_allow_html=True)
        render_detail(filtered, watchlist)

    st.markdown('</div>', unsafe_allow_html=True)

    # Footer
    render_footer()


if __name__ == "__main__":
    main()
