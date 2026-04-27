import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import engine as E
import time

st.set_page_config(page_title="AL7EBI PRO", page_icon="🔶", layout="wide")

if "theme" not in st.session_state: st.session_state.theme = "dark"
if "density" not in st.session_state: st.session_state.density = "comfortable"
if "colorblind" not in st.session_state: st.session_state.colorblind = False

THEMES = {
    "dark": {"BG":"#0A0E14","CARD":"#121821","TXT":"#E2E8F5","BL":"#D4AF37"},
    "light": {"BG":"#F8FAFC","CARD":"#FFFFFF","TXT":"#0F172A","BL":"#B8941F"},
}
C = THEMES[st.session_state.theme]
GR = "#0EA5E9" if st.session_state.colorblind else "#10B981"
RD = "#F97316" if st.session_state.colorblind else "#EF4444"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&family=JetBrains+Mono:wght@400;700&display=swap');
html,body{{background:{C['BG']}!important;font-family:'Tajawal',sans-serif!important;color:{C['TXT']}!important;direction:rtl!important;}}
.mono{{font-family:'JetBrains Mono',monospace!important;}}
.trade-card{{background:{C['CARD']};border:1px solid #1E293B;border-radius:14px;padding:{'12px' if st.session_state.density=='compact' else '18px'};margin-bottom:10px;transition:all 0.2s;}}
.trade-card:hover{{transform:translateY(-2px);box-shadow:0 8px 24px rgba(212,175,55,0.15);}}
.trade-card.long{{border-right:4px solid {GR};}}
.trade-card.short{{border-right:4px solid {RD};}}
.skeleton{{background:linear-gradient(90deg,#1E293B 25%,#334155 50%,#1E293B 75%);background-size:200% 100%;animation:shimmer 1.5s infinite;border-radius:8px;height:80px;}}
@keyframes shimmer{{0%{{background-position:-200% 0}}100%{{background-position:200% 0}}}}
</style>
""", unsafe_allow_html=True)

for k in ["radar_df","radar_ts","favorites","paper_trades"]:
    if k not in st.session_state: st.session_state[k] = [] if "fav" in k or "trade" in k else None

@st.cache_data(ttl=300)
def _row(t,s):
    try: r=E.run_engine(t,s); return E.extract_row(r[0],t,s)
    except: return {"Ticker":t,"Grade":"ERR"}

def do_scan(wl):
    ph = st.empty()
    with ph.container():
        for _ in range(3): st.markdown('<div class="skeleton"></div>', unsafe_allow_html=True)
    res=[]
    with ThreadPoolExecutor(max_workers=5) as p:
        futs={p.submit(_row,t,s):t for t,s in wl}
        for f in as_completed(futs): res.append(f.result())
    ph.empty()
    df=pd.DataFrame(res)
    st.session_state.radar_df=df
    st.session_state.radar_ts=datetime.now(timezone.utc)
    st.toast(f"✅ تم تحليل {len(df)} سهم", icon="🎯")

# ===== الهيدر - مصحح =====
col_h1, col_h2, col_h3 = st.columns([3, 2, 1]) # ← تم التصحيح هنا
with col_h1:
    st.markdown(f"<h2 style='margin:0;color:{C['BL']}'>🔶 AL7EBI PRO</h2>", unsafe_allow_html=True)
with col_h2:
    cmd = st.text_input("بحث", placeholder="AAPL...", label_visibility="collapsed")
with col_h3:
    if st.session_state.radar_ts:
        age = int((datetime.now(timezone.utc)-st.session_state.radar_ts).total_seconds())
        st.markdown(f"<div class='mono' style='text-align:left;color:{C['BL']}'>{age}ث</div>", unsafe_allow_html=True)

# أدوات
t1,t2,t3,t4,t5 = st.columns(5)
with t1:
    if st.button("🌙/☀️"): st.session_state.theme = "light" if st.session_state.theme=="dark" else "dark"; st.rerun()
with t2:
    if st.button("📏"): st.session_state.density = "compact" if st.session_state.density=="comfortable" else "comfortable"; st.rerun()
with t3:
    if st.button("👁️"): st.session_state.colorblind = not st.session_state.colorblind; st.rerun()
with t4:
    if st.button("📤"):
        if st.session_state.radar_df is not None:
            st.session_state.radar_df.to_csv("export.csv", index=False)
            st.toast("تم التصدير")
with t5:
    if st.button("🎓"): st.info("1- مسح 2- اختر 3- حلل")

tabs = st.tabs(["🏠 الرئيسية","🎯 الأوبشن","📋 الخطة","📊 المصفوفة","🧮 الحاسبة"])

with tabs[0]:
    if st.button("📡 مسح الرادار", type="primary", use_container_width=True):
        wl=[(t,"QQQ") for t in ["MSFT","GOOGL","TSLA","AAPL","NVDA"]]
        do_scan(wl)

    df = st.session_state.radar_df
    if df is not None:
        for _,r in df.iterrows():
            bias=r.get("Bias","Long"); cls="long" if bias=="Long" else "short"
            st.markdown(f'<div class="trade-card {cls}">', unsafe_allow_html=True)
            c1,c2,c3 = st.columns([2,2,1])
            with c1:
                st.markdown(f"**{r.get('Ticker')}** {r.get('Grade','?')}")
            with c2:
                st.markdown(f"<span class='mono'>دخول: {r.get('Entry','—')}</span>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<span style='color:{GR if bias=='Long' else RD}'>{'CALL' if bias=='Long' else 'PUT'}</span>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

with tabs[1]:
    df = st.session_state.radar_df
    if df is not None:
        st.write("توصيات الأوبشن")
        st.dataframe(df[["Ticker","Grade","Bias"]], use_container_width=True)

with tabs[2]:
    df = st.session_state.radar_df
    if df is not None:
        st.dataframe(df, use_container_width=True)

with tabs[3]:
    df = st.session_state.radar_df
    if df is not None:
        st.dataframe(df.head(10), use_container_width=True)

with tabs[4]:
    capital = st.number_input("رأس المال", value=10000)
    risk = st.slider("مخاطرة %", 1,5,2)
    if st.button("احسب"):
        st.success(f"تخاطر بـ ${capital*risk/100:.2f}")
