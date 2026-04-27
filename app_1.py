import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import engine as E

# 1. إعدادات الصفحة الأساسية
st.set_page_config(page_title="منصة الحبي", page_icon="🔶", layout="wide", initial_sidebar_state="collapsed")

# 2. تعريف المخازن (Session State) لكي لا تضيع البيانات عند التنقل
_DEFAULTS = {
    "theme":"dark","market_tab":"US","main_tab":"الرئيسية",
    "radar_df":None,"radar_ts":None
}
for k,v in _DEFAULTS.items():
    if k not in st.session_state: st.session_state[k]=v

# 3. الألوان والتنسيق (CSS) الذي اخترته أنت
BG="#0A0E14"; CARD="#121821"; BRD="#1E293B"; TXT="#E2E8F5"; BL="#D4AF37"; GR="#10B981"; RD="#EF4444"; AM="#F59E0B"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;800&display=swap');
html,body{{background:{BG}!important;font-family:'Tajawal',sans-serif!important;color:{TXT}!important;direction:rtl!important;}}
.main.block-container{{padding:0!important;max-width:100%!important;}}
[data-testid="stSidebar"]{{display:none!important;}}
.trade-card{{background:{CARD};border:1px solid {BRD};border-radius:14px;padding:16px;margin-bottom:12px;}}
.trade-card.long{{border-right:4px solid {GR};}}
.trade-card.short{{border-right:4px solid {RD};}}
.trade-card.wait{{border-right:4px solid {AM};}}
.trade-card.closed{{border-right:4px solid #64748B;opacity:0.7;}}
</style>
""", unsafe_allow_html=True)

# 4. دالة جلب البيانات من المحرك (Engine)
def _row(t,s):
    try: 
        r=E.run_engine(t,s)
        return E.extract_row(r[0],t,s)
    except: 
        return E.extract_row(None,t,s)

def do_scan(watchlist):
    total=len(watchlist); res=[]
    pb=st.progress(0,text="جارٍ المسح...")
    with ThreadPoolExecutor(max_workers=4) as pool:
        futs={pool.submit(_row,p[0],p[1]):p for p in watchlist}
        for i,f in enumerate(as_completed(futs)):
            r=f.result()
            res.append(r)
            pb.progress((i+1)/total)
    pb.empty()
    df=pd.DataFrame(res)
    # ترتيب البيانات
    if not df.empty and "_grade_rank" in df.columns:
        df = df.sort_values(by=["_grade_rank"], ascending=True)
    st.session_state.radar_df=df
    st.success(f"✅ اكتمل مسح {len(df)} سهم")

# 5. الهيدر (رأس الصفحة)
st.markdown(f"""<div style="background:{CARD};padding:14px 32px;border-bottom:2px solid {BL};display:flex;justify-content:space-between;">
<div style="display:flex;gap:10px;align-items:center;"><div style="width:40px;height:40px;background:{BL};border-radius:10px;display:flex;align-items:center;justify-content:center;font-weight:900;color:#000;">ح</div>
<div style="font-weight:800;">AL7EBI ICT</div></div><div style="color:{BL};">{datetime.now().strftime("%H:%M:%S")}</div></div>""", unsafe_allow_html=True)

# 6. أزرار التبويبات
tabs=st.columns(4)
menu = ["الرئيسية","الأوبشن","الخطة","المصفوفة"]
for i,name in enumerate(menu):
    with tabs[i]:
        if st.button(name,use_container_width=True,type="primary" if st.session_state.main_tab==name else "secondary"):
            st.session_state.main_tab=name
            st.rerun()

# 7. قائمة الأسهم
US_WATCHLIST=[(t,"QQQ") for t in ["MSFT","GOOGL","TSLA","AAPL","NVDA","META"]]
watchlist = US_WATCHLIST

st.markdown('<div style="padding:20px 32px;">',unsafe_allow_html=True)

# --- تبويب الرئيسية ---
if st.session_state.main_tab=="الرئيسية":
    if st.button("📡 مسح الرادار",type="primary"): 
        do_scan(watchlist)

    df=st.session_state.radar_df
    if df is not None:
        for _,r in df.iterrows():
            grd=r.get("Grade","?")
            bias=r.get("Bias","Long")
            if grd in ["A+","A"]: cls="long" if bias=="Long" else "short"
            elif grd=="B": cls="wait"
            else: cls="closed"

            st.markdown(f"""<div class="trade-card {cls}">
                <b>{r.get('Ticker')}</b> | {grd} | {'شراء' if bias=='Long' else 'بيع'} | دخول: {r.get('Entry')}
            </div>""", unsafe_allow_html=True)

# --- تبويب الأوبشن ---
elif st.session_state.main_tab=="الأوبشن":
    st.write("### 🎯 توصيات الأوبشن")
    df=st.session_state.radar_df
    if df is None: 
        st.warning("الرجاء الضغط على 'مسح الرادار' في الصفحة الرئيسية أولاً")
    else:
        for _,r in df[df["Grade"].isin(["A+","A","B"])].iterrows():
            color = GR if r.get("Bias")=="Long" else RD
            st.write(f"Sighal: {r['Ticker']} - {'CALL' if r.get('Bias')=='Long' else 'PUT'}")

# --- تبويب الخطة ---
elif st.session_state.main_tab=="الخطة":
    st.write("### 📋 خطة التداول")
    df=st.session_state.radar_df
    if df is None: 
        st.warning("لا توجد بيانات، اذهب للرئيسية وامسح السوق")
    else:
        st.table(df[["Ticker", "Grade", "Bias", "Entry"]])

# --- تبويب المصفوفة ---
elif st.session_state.main_tab=="المصفوفة":
    st.write("### 📊 مصفوفة الأسهم")
    df=st.session_state.radar_df
    if df is None: 
        st.warning("لا توجد بيانات")
    else:
        st.dataframe(df[["Ticker", "Grade", "TP1"]], use_container_width=True)

st.markdown('</div>',unsafe_allow_html=True)
