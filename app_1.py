"""
app_1.py — AL7EBI ICT منصة الحبي للتداول
نسخة احترافية كاملة - ذهبي + مصفوفة + أوبشن + خطة
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
import engine as E

# ══════════════════════════════════════════════════════════════
st.set_page_config(page_title="AL7EBI ICT", page_icon="🔶", layout="wide", initial_sidebar_state="collapsed")

_DEFAULTS = {
    "theme": "dark", "market_tab": "US", "main_tab": "الرئيسية",
    "radar_df": None, "radar_ts": None, "drill": None,
    "search_q": "", "sort_by": "القوة", "filter_grade": "جميع القوة",
    "view_mode": "بطاقات", "filter_mode": "كامل", "manual_tickers": [],
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state: st.session_state[k] = v

DARK = st.session_state.theme == "dark"

# ══════════════════════════════════════════════════════════════
SA_STOCKS = [
    ("2222","أرامكو"),("1120","الراجحي"),("2010","سابك"),("7010","STC"),
    ("1180","الأهلي"),("1211","معادن"),("4190","جرير"),("2380","بترو رابغ"),
]
SA_WATCHLIST = [(t,"2222") for t,_ in SA_STOCKS]

US_WATCHLIST_MAP = {
    "تقنية كبرى (30)": [(t,"QQQ") for t in ["AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","AVGO","AMD","QCOM","ORCL","CRM","ADBE","INTC","NFLX","PYPL","SHOP","SNOW","PANW","CRWD","ZS","PLTR"]],
    "قيادية S&P (40)": [(t,"SPY") for t in ["JPM","BAC","GS","V","MA","JNJ","UNH","LLY","WMT","HD","COST","XOM","CVX"]],
    "الكل (70 سهم)": E.WATCHLIST_PRESETS.get("Options (70 Stocks)", []),
}
ALL_TICKERS = sorted(list(set([t for lst in US_WATCHLIST_MAP.values() for t,_ in lst] + [t for t,_ in SA_STOCKS])))

# ══════════════════════════════════════════════════════════════
if DARK:
    BG="#0A0E14"; CARD="#121821"; CARD2="#1A2332"; BRD="#1E293B"
    TXT="#E2E8F5"; TXT2="#94A3B8"; TXT3="#475569"
else:
    BG="#F8FAFC"; CARD="#FFFFFF"; CARD2="#F1F5F9"; BRD="#E2E8F0"
    TXT="#0F172A"; TXT2="#475569"; TXT3="#94A3B8"

BL="#D4AF37"; GR="#10B981"; RD="#EF4444"; AM="#F59E0B"
GR2="#22C55E"; RD2="#F87171"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;800&display=swap');
html,body,[class*="css"]{{background:{BG}!important;font-family:'Tajawal',sans-serif!important;color:{TXT}!important;direction:rtl!important;}}
.main.block-container{{padding:0!important;max-width:100%!important;}}
[data-testid="stSidebar"]{{display:none!important;}}
.top-hdr{{background:{CARD};padding:0 32px;height:64px;display:flex;align-items:center;justify-content:space-between;border-bottom:2px solid {BL};position:sticky;top:0;z-index:100;}}
.brand-logo{{width:44px;height:44px;background:linear-gradient(135deg,{BL},#B8941F);border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:1.3rem;font-weight:900;color:#000;}}
.brand-name{{font-size:1.2rem;font-weight:800;color:{TXT};}}
.main-tabs{{display:flex;gap:0;padding:0 32px;background:{CARD};border-bottom:1px solid {BRD};}}
.main-tab{{padding:14px 28px;font-size:0.95rem;font-weight:700;color:{TXT3};cursor:pointer;border-bottom:3px solid transparent;transition:all.2s;}}
.main-tab.active{{color:{BL};border-bottom-color:{BL};background:rgba(212,175,55,0.08);}}
.stats-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:20px 0;}}
.stat-card{{background:{CARD};border:1px solid {BRD};border-radius:14px;padding:18px;text-align:center;}}
.stat-val{{font-size:2rem;font-weight:900;}}
.cards-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;}}
.trade-card{{background:{CARD};border:1px solid {BRD};border-radius:14px;padding:18px;transition:all.2s;}}
.trade-card:hover{{transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,0.3);border-color:{BL};}}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300, show_spinner=False)
def _run(ticker, smt): return E.run_engine(ticker, smt)

@st.cache_data(ttl=300, show_spinner=False)
def _row(ticker, smt):
    try: res = E.run_engine(ticker, smt); return E.extract_row(res[0], ticker, smt)
    except: return E.extract_row(None, ticker, smt)

def _age_h(ts):
    if ts is None: return 9999
    u = ts.astimezone(timezone.utc) if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - u).total_seconds() / 3600

def _stars(grade):
    n = {"A+":3,"A":3,"B":2,"C":1}.get(grade,0)
    return "★"*n + "☆"*(3-n)

def _status_badge(grade):
    if grade in ["A+","A"]: return f'<span style="background:rgba(16,185,129,.15);color:{GR2};padding:4px 12px;border-radius:20px;font-size:0.75rem;font-weight:700;">نشط</span>'
    if grade == "B": return f'<span style="background:rgba(245,158,11,.15);color:{AM};padding:4px 12px;border-radius:20px;font-size:0.75rem;font-weight:700;">منتظر</span>'
    return f'<span style="background:rgba(100,116,139,.15);color:{TXT3};padding:4px 12px;border-radius:20px;font-size:0.75rem;font-weight:700;">مغلق</span>'

def render_header():
    st.markdown(f"""<div class="top-hdr">
      <div style="display:flex;align-items:center;gap:12px;">
        <div class="brand-logo">ح</div>
        <div><div class="brand-name">AL7EBI ICT</div><div style="font-size:0.7rem;color:{TXT3};">منصة الحبي الذكية</div></div>
      </div>
      <div style="color:{BL};font-weight:700;font-size:1.1rem;">{datetime.now().strftime("%H:%M:%S")}</div>
    </div>""", unsafe_allow_html=True)

def render_main_tabs():
    tabs = ["الرئيسية", "الأوبشن", "الخطة", "المصفوفة"]
    cols = st.columns(4)
    for i, tab in enumerate(tabs):
        with cols[i]:
            active = "active" if st.session_state.main_tab == tab else ""
            if st.button(tab, key=f"mt_{i}", use_container_width=True, type="primary" if active else "secondary"):
                st.session_state.main_tab = tab; st.rerun()
    st.markdown(f"""<div class="main-tabs">{''.join([f'<div class="main-tab {"active" if st.session_state.main_tab==t else ""}">{t}</div>' for t in tabs])}</div>""", unsafe_allow_html=True)

def do_scan(watchlist):
    total = len(watchlist); results = []
    pb = st.progress(0, text="جارٍ المسح...")
    with ThreadPoolExecutor(max_workers=4) as pool:
        futs = {pool.submit(_row, p[0], p[1]): p for p in watchlist}
        for i, fut in enumerate(as_completed(futs)):
            tkr, smt = futs[fut]
            try: r = fut.result(timeout=25)
            except: r = E.extract_row(None, tkr, smt); r["Grade"]="TIMEOUT"
            results.append(r); pb.progress((i+1)/total, text=f"مسح {i+1}/{total} - {tkr}")
    pb.empty()
    df = pd.DataFrame(results).sort_values(by=["_grade_rank","_score_num"], ascending=[True,False]).reset_index(drop=True)
    df["scan_date"] = datetime.now().strftime("%Y-%m-%d")
    st.session_state.radar_df = df; st.session_state.radar_ts = datetime.now(timezone.utc)
    st.success(f"✅ اكتمل المسح - {len(df)} سهم")

def render_stats(df):
    if df is None or df.empty: total=active=waiting=closed=0
    else:
        total=len(df); active=len(df[df["Grade"].isin(["A+","A"])]); waiting=len(df[df["Grade"]=="B"]); closed=total-active-waiting
    st.markdown(f"""<div class="stats-row">
      <div class="stat-card"><div style="color:{TXT3};font-size:0.85rem;">إجمالي</div><div class="stat-val" style="color:{TXT};">{total}</div></div>
      <div class="stat-card"><div style="color:{TXT3};font-size:0.85rem;">نشطة</div><div class="stat-val" style="color:{GR2};">{active}</div></div>
      <div class="stat-card"><div style="color:{TXT3};font-size:0.85rem;">منتظرة</div><div class="stat-val" style="color:{AM};">{waiting}</div></div>
      <div class="stat-card"><div style="color:{TXT3};font-size:0.85rem;">مغلقة</div><div class="stat-val" style="color:{TXT3};">{closed}</div></div>
    </div>""", unsafe_allow_html=True)

def render_cards(df):
    if df is None or df.empty: st.info("📭 لا توجد بيانات - اضغط مسح الرادار"); return
    html = '<div class="cards-grid">'
    for _, r in df.iterrows():
        tkr=r.get("Ticker","?"); grd=r.get("Grade","?"); bias=r.get("Bias","—")
        entry=r.get("Entry","—"); sl=r.get("SL","—"); tp1=r.get("TP1","—"); tp2=r.get("TP2 (Ext)","—")
        rr=r.get("Best R:R","—"); stars=_stars(grd); badge=_status_badge(grd)
        color = GR2 if bias=="Long" else RD2; btxt = "شراء ▲" if bias=="Long" else "بيع ▼"
        html += f"""<div class="trade-card">
          <div style="display:flex;justify-content:space-between;margin-bottom:12px;">
            <div><div style="font-size:1.3rem;font-weight:900;color:{TXT};">{tkr}</div><div style="font-size:0.75rem;color:{TXT3};">{r.get('scan_date','')}</div></div>
            <div style="text-align:left;"><div style="background:{CARD2};padding:4px 10px;border-radius:8px;font-weight:700;color:{BL};">{grd}</div><div style="color:{BL};margin-top:4px;">{stars}</div></div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:0.9rem;">
            <div><span style="color:{TXT3};">الاتجاه:</span> <span style="color:{color};font-weight:700;">{btxt}</span></div>
            <div><span style="color:{TXT3};">الدخول:</span> <span style="font-weight:700;">{entry}</span></div>
            <div><span style="color:{TXT3};">الوقف:</span> <span style="color:{RD2};">{sl}</span></div>
            <div><span style="color:{TXT3};">هدف1:</span> <span style="color:{GR2};">{tp1}</span></div>
            <div><span style="color:{TXT3};">الموجة:</span> <span style="color:{AM};">{tp2}</span></div>
            <div><span style="color:{TXT3};">R:R:</span> <span style="font-weight:700;">{rr}</span></div>
          </div>
          <div style="margin-top:12px;padding-top:10px;border-top:1px solid {BRD};text-align:left;">{badge}</div>
        </div>"""
    html += '</div>'; st.markdown(html, unsafe_allow_html=True)

def render_matrix(df):
    st.markdown("### 📊 مصفوفة الفرص المؤسسية")
    if df is None or df.empty: st.info("قم بالمسح أولاً"); return
    html = f"""<div style="background:{CARD};border:1px solid {BRD};border-radius:14px;overflow:hidden;">
    <table style="width:100%;border-collapse:collapse;">
      <thead><tr style="background:{BG};border-bottom:1px solid {BRD};">
        <th style="padding:14px;text-align:right;color:{TXT2};">الأصل</th>
        <th style="padding:14px;text-align:right;color:{TXT2};">النموذج</th>
        <th style="padding:14px;text-align:right;color:{TXT2};">القوة</th>
        <th style="padding:14px;text-align:right;color:{TXT2};">السبب</th>
        <th style="padding:14px;text-align:right;color:{TXT2};">الهدف</th>
        <th style="padding:14px;text-align:right;color:{TXT2};">الحالة</th>
      </tr></thead><tbody>"""
    for _, r in df.head(12).iterrows():
        grd=r.get("Grade","?"); stars=_stars(grd)
        if grd=="A+": model,reason,status,col="Breaker+FVG","سحب سيولة + Breaker","دخول فوري",GR2
        elif grd=="A": model,reason,status,col="Turtle Soup","اختراق كاذب + SMT","مراقبة",BL
        elif grd=="B": model,reason,status,col="Model 2022","تغير هيكل + FVG","تأمين",AM
        else: model,reason,status,col="Silver Bullet","تمركز زمني","انتظار",TXT3
        html += f"""<tr style="border-bottom:1px solid {BRD};">
          <td style="padding:12px;font-weight:700;color:{TXT};">{r.get('Ticker')}</td>
          <td style="padding:12px;color:{TXT2};">{model}</td>
          <td style="padding:12px;color:{BL};font-size:1.2rem;">{stars}</td>
          <td style="padding:12px;color:{TXT3};font-size:0.85rem;">{reason}</td>
          <td style="padding:12px;font-weight:600;">{r.get('TP1','—')}</td>
          <td style="padding:12px;color:{col};font-weight:700;">{status}</td>
        </tr>"""
    html += "</tbody></table></div>"; st.markdown(html, unsafe_allow_html=True)

def render_options(df):
    st.markdown("### 🎯 الأوبشن - ICT")
    if df is None or df.empty: st.warning("لا توجد بيانات"); return
    data=[]
    for _, r in df[df["Grade"].isin(["A+","A"])].head(8).iterrows():
        try:
            e=float(r.get("Entry",0)); bias=r.get("Bias")
            strike=round(e*1.02,2) if bias=="Long" else round(e*0.98,2)
            data.append({"الرمز":r.get("Ticker"),"النوع":"CALL" if bias=="Long" else "PUT","Strike":strike,"الدخول":r.get("Entry"),"الهدف":r.get("TP1"),"القوة":_stars(r.get("Grade"))})
        except: continue
    if data: st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
    else: st.info("لا توجد فرص")

def render_plan(df):
    st.markdown("### 📋 الخطة الكاملة - 5 مراحل")
    if df is None or df.empty: st.info("قم بالمسح"); return
    c1,c2,c3,c4,c5=st.columns(5)
    s1=len(df); s2=len(df[df["Grade"].isin(["A+","A"])]); s3=len(df[df["Grade"]=="A+"]); s4=s3; s5=s1
    c1.metric("1- سحب سيولة", f"{s1} سهم"); c2.metric("2- كسر بنية", f"{s2} سهم")
    c3.metric("3- SMT", f"{s3} سهم"); c4.metric("4- IFVG", f"{s4} سهم"); c5.metric("5- سيولة خارجية", f"{s5} سهم")
    st.markdown("---"); ready=df[df["Grade"]=="A+"]
    if not ready.empty:
        for _, r in ready.iterrows(): st.success(f"✅ {r['Ticker']} | {r.get('Bias')} | دخول {r.get('Entry')}")
    else: st.warning("لا توجد أسهم جاهزة")

def main():
    render_header(); render_main_tabs()
    mkt = st.session_state.market_tab
    col1,col2 = st.columns([1,4])
    with col1:
        if st.button("🇸🇦 سعودي", use_container_width=True, type="primary" if mkt=="SA" else "secondary"): st.session_state.market_tab="SA"; st.rerun()
    with col2:
        if st.button("🇺🇸 أمريكي", use_container_width=True, type="primary" if mkt=="US" else "secondary"): st.session_state.market_tab="US"; st.rerun()

    watchlist = SA_WATCHLIST if mkt=="SA" else US_WATCHLIST_MAP["تقنية كبرى (30)"]

    st.markdown('<div style="padding:20px 32px;">', unsafe_allow_html=True)

    if st.session_state.main_tab == "الرئيسية":
        c1,c2,c3,c4 = st.columns([2,1,1,1])
        with c1:
            mode = st.radio("وضع الفلتر", ["كامل","يدوي"], horizontal=True, key="fm")
            st.session_state.filter_mode = mode
        with c2:
            if mode=="يدوي":
                tickers = st.multiselect("اختر أسهم", ALL_TICKERS, default=st.session_state.manual_tickers, label_visibility="collapsed")
                st.session_state.manual_tickers = tickers
        with c3:
            if st.button("📡 مسح الرادار", type="primary", use_container_width=True):
                wl = [(t,"QQQ") for t in st.session_state.manual_tickers] if mode=="يدوي" and tickers else watchlist
                do_scan(wl)
        with c4:
            if st.button("🔄 تحديث", use_container_width=True): st.session_state.radar_df=None; st.rerun()

        # بحث شامل
        search = st.selectbox("🔍 ابحث عن سهم", [""]+ALL_TICKERS, key="search_all")
        if search: st.session_state.search_q = search

        render_stats(st.session_state.radar_df)
        df = st.session_state.radar_df
        if df is not None and st.session_state.search_q:
            df = df[df["Ticker"].str.contains(st.session_state.search_q, na=False)]
        render_cards(df)

    elif st.session_state.main_tab == "الأوبشن": render_options(st.session_state.radar_df)
    elif st.session_state.main_tab == "الخطة": render_plan(st.session_state.radar_df)
    elif st.session_state.main_tab == "المصفوفة": render_matrix(st.session_state.radar_df)

    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()
