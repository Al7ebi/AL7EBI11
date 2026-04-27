"""
app_1.py — منصة الحبي (النسخة الثابتة)
يحافظ على كل دوال engine.py + يضيف الألوان والتبويبات
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
import engine as E

st.set_page_config(page_title="منصة الحبي", page_icon="🔶", layout="wide", initial_sidebar_state="collapsed")

_DEFAULTS = {
    "theme":"dark","market_tab":"US","main_tab":"الرئيسية",
    "radar_df":None,"radar_ts":None,"drill":None,
    "search_q":"","sort_by":"القوة","filter_grade":"جميع القوة","view_mode":"بطاقات",
}
for k,v in _DEFAULTS.items():
    if k not in st.session_state: st.session_state[k]=v

DARK = True
BG="#0A0E14"; CARD="#121821"; BRD="#1E293B"; TXT="#E2E8F5"; TXT2="#94A3B8"; TXT3="#64748B"
BL="#D4AF37"; GR="#10B981"; RD="#EF4444"; AM="#F59E0B"

# ===== CSS الأصلي + ألوان البطاقات =====
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;800&display=swap');
html,body{{background:{BG}!important;font-family:'Tajawal',sans-serif!important;color:{TXT}!important;direction:rtl!important;}}
.main.block-container{{padding:0!important;max-width:100%!important;}}
[data-testid="stSidebar"]{{display:none!important;}}
.trade-card{{background:{CARD};border:1px solid {BRD};border-radius:14px;padding:16px;margin-bottom:12px;}}
.trade-card.long{{border-right:4px solid {GR};background:linear-gradient(90deg,rgba(16,185,129,0.08),{CARD});}}
.trade-card.short{{border-right:4px solid {RD};background:linear-gradient(90deg,rgba(239,68,68,0.08),{CARD});}}
.trade-card.wait{{border-right:4px solid {AM};background:linear-gradient(90deg,rgba(245,158,11,0.08),{CARD});}}
.trade-card.closed{{border-right:4px solid {TXT3};opacity:0.7;}}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300, show_spinner=False)
def _run(t,s): return E.run_engine(t,s)

@st.cache_data(ttl=300, show_spinner=False)
def _row(t,s):
    try: r=E.run_engine(t,s); return E.extract_row(r[0],t,s)
    except: return E.extract_row(None,t,s)

def _age_h(ts):
    if not ts: return 999
    u=ts.astimezone(timezone.utc) if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc)-u).total_seconds()/3600

def do_scan(watchlist):
    total=len(watchlist); res=[]
    pb=st.progress(0,text="جارٍ المسح...")
    with ThreadPoolExecutor(max_workers=4) as pool:
        futs={pool.submit(_row,p[0],p[1]):p for p in watchlist}
        for i,f in enumerate(as_completed(futs)):
            try: r=f.result(timeout=25)
            except: t,_=futs[f]; r=E.extract_row(None,t,"QQQ"); r["Grade"]="TIMEOUT"
            res.append(r); pb.progress((i+1)/total)
    pb.empty()
    df=pd.DataFrame(res).sort_values(by=["_grade_rank","_score_num"],ascending=[True,False]).reset_index(drop=True)
    df["scan_date"]=datetime.now().strftime("%Y-%m-%d")
    st.session_state.radar_df=df; st.session_state.radar_ts=datetime.now(timezone.utc)
    st.success(f"✅ اكتمل {len(df)} سهم")

# ===== الهيدر والتبويبات =====
st.markdown(f"""<div style="background:{CARD};padding:14px 32px;border-bottom:2px solid {BL};display:flex;justify-content:space-between;">
<div style="display:flex;gap:10px;align-items:center;"><div style="width:40px;height:40px;background:{BL};border-radius:10px;display:flex;align-items:center;justify-content:center;font-weight:900;color:#000;">ح</div>
<div style="font-weight:800;">AL7EBI ICT</div></div><div style="color:{BL};">{datetime.now().strftime("%H:%M:%S")}</div></div>""", unsafe_allow_html=True)

tabs=st.columns(4)
for i,name in enumerate(["الرئيسية","الأوبشن","الخطة","المصفوفة"]):
    with tabs[i]:
        if st.button(name,use_container_width=True,type="primary" if st.session_state.main_tab==name else "secondary"):
            st.session_state.main_tab=name; st.rerun()

# ===== المنطق الأصلي =====
SA_WATCHLIST=[("2222","2222"),("1120","2222"),("2010","2222")]
US_WATCHLIST=[(t,"QQQ") for t in ["MSFT","GOOGL","TSLA","AAPL","NVDA","ORCL","ADBE","META"]]

watchlist = SA_WATCHLIST if st.session_state.market_tab=="SA" else US_WATCHLIST

st.markdown('<div style="padding:20px 32px;">',unsafe_allow_html=True)

# ===== الرئيسية =====
if st.session_state.main_tab=="الرئيسية":
    c1,c2=st.columns([4,1])
    with c2:
        if st.button("📡 مسح الرادار",type="primary",use_container_width=True): do_scan(watchlist)

    df=st.session_state.radar_df
    if df is not None and not df.empty:
        # بطاقات ملونة حسب الأصل
        for _,r in df.iterrows():
            grd=r.get("Grade","?"); bias=r.get("Bias","Long")
            if grd in ["A+","A"]: cls="long" if bias=="Long" else "short"
            elif grd=="B": cls="wait"
            else: cls="closed"

            st.markdown(f"""<div class="trade-card {cls}">
                <div style="display:flex;justify-content:space-between;">
                    <div><b>{r.get('Ticker')}</b> | {grd} | {'شراء' if bias=='Long' else 'بيع'}</div>
                    <div>{r.get('Entry','—')} → {r.get('TP1','—')}</div>
                </div>
            </div>""", unsafe_allow_html=True)

# ===== الأوبشن - يعمل من نفس df =====
elif st.session_state.main_tab=="الأوبشن":
    st.markdown("### 🎯 الأوبشن")
    df=st.session_state.radar_df
    if df is None: st.warning("امسح الرادار أولاً من الرئيسية")
    else:
        for _,r in df[df["Grade"].isin(["A+","A","B"])].iterrows():
            is_call=r.get("Bias")=="Long"; color=GR if is_call else RD
            st.markdown(f"""<div style="background:{CARD};border-right:4px solid {color};padding:14px;margin:8px 0;border-radius:8px;">
                {r.get('Ticker')} | {'CALL' if is_call else 'PUT'} | دخول {r.get('Entry','—')}
            </div>""", unsafe_allow_html=True)

# ===== الخطة - تعمل من نفس df =====
elif st.session_state.main_tab=="الخطة":
    st.markdown("### 📋 الخطة")
    df=st.session_state.radar_df
    if df is None: st.warning("امسح الرادار أولاً")
    else:
        filt=st.selectbox("فلترة",["الكل","نشط","منتظر","منتهي"])
        if filt=="نشط": df=df[df["Grade"].isin(["A+","A"])]
        elif filt=="منتظر": df=df[df["Grade"]=="B"]
        elif filt=="منتهي": df=df[~df["Grade"].isin(["A+","A","B"])]

        for _,r in df.iterrows():
            st.write(f"✓ {r['Ticker']} - {r.get('Bias')} - {r.get('Entry')}")

# ===== المصفوفة - تعمل من نفس df =====
elif st.session_state.main_tab=="المصفوفة":
    st.markdown("### 📊 المصفوفة")
    df=st.session_state.radar_df
    if df is None: st.warning("امسح الرادار أولاً")
    else:
        tf=st.selectbox("الفريم",["1D","4H","1H","15m"])
        st.write(f"الفريم: {tf}")
        data=[]
        for _,r in df.head(10).iterrows():
            data.append({
                "الأصل":r.get("Ticker"),
                "القوة":"★"*3 if r.get("Grade") in ["A+","A"] else "★"*2,
                "الهدف":r.get("TP1"),
                "الحالة":"دخول" if r.get("Grade") in ["A+","A"] else "مراقبة"
            })
        st.dataframe(pd.DataFrame(data),use_container_width=True,hide_index=True)

st.markdown('</div>',unsafe_allow_html=True)
