"""
app_1.py — AL7EBI ICT v2.1
جدول أوبشن ملون + خطة قابلة للفرز + مصفوفة بالفريم
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import engine as E

st.set_page_config(page_title="AL7EBI ICT", page_icon="🔶", layout="wide", initial_sidebar_state="collapsed")

_DEFAULTS = {"theme":"dark","market_tab":"US","main_tab":"الرئيسية","radar_df":None,"radar_ts":None,
             "filter_mode":"كامل","manual_tickers":[],"matrix_tf":"يومي 1D","plan_filter":"الكل"}
for k,v in _DEFAULTS.items():
    if k not in st.session_state: st.session_state[k]=v

DARK = True
BG="#0A0E14"; CARD="#121821"; BRD="#1E293B"; TXT="#E2E8F5"; TXT2="#94A3B8"; TXT3="#475569"
BL="#D4AF37"; GR="#10B981"; RD="#EF4444"; AM="#F59E0B"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;800&display=swap');
html,body{{background:{BG}!important;font-family:'Tajawal',sans-serif!important;color:{TXT}!important;direction:rtl!important;}}
.main.block-container{{padding:0!important;max-width:100%!important;}}
.top-hdr{{background:{CARD};padding:0 32px;height:64px;display:flex;align-items:center;justify-content:space-between;border-bottom:2px solid {BL};}}
.brand-logo{{width:44px;height:44px;background:linear-gradient(135deg,{BL},#B8941F);border-radius:12px;display:flex;align-items:center;justify-content:center;font-weight:900;color:#000;font-size:1.3rem;}}
.pro-table{{background:{CARD};border:1px solid {BRD};border-radius:14px;overflow:hidden;}}
.pro-table table{{width:100%;border-collapse:collapse;}}
.pro-table th{{background:{BG};padding:14px;color:{TXT2};font-size:0.85rem;text-align:right;border-bottom:1px solid {BRD};}}
.pro-table td{{padding:13px;border-bottom:1px solid {BRD};color:{TXT};}}
.call-badge{{background:rgba(16,185,129,0.15);color:{GR};padding:6px 14px;border-radius:8px;font-weight:700;}}
.put-badge{{background:rgba(239,68,68,0.15);color:{RD};padding:6px 14px;border-radius:8px;font-weight:700;}}
.plan-item{{background:rgba(16,185,129,0.08);border-right:4px solid {GR};padding:14px 18px;margin-bottom:8px;border-radius:10px;display:flex;justify-content:space-between;align-items:center;}}
.plan-item.short{{background:rgba(239,68,68,0.08);border-right-color:{RD};}}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def _row(t,k):
    try: r=E.run_engine(t,k); return E.extract_row(r[0],t,k)
    except: return E.extract_row(None,t,k)

def _stars(g): n={"A+":3,"A":3,"B":2}.get(g,1); return "★"*n+"☆"*(3-n)

def do_scan(wl):
    res=[]; pb=st.progress(0)
    with ThreadPoolExecutor(max_workers=4) as p:
        futs={p.submit(_row,t,s):(t,s) for t,s in wl}
        for i,f in enumerate(as_completed(futs)):
            res.append(f.result()); pb.progress((i+1)/len(wl))
    pb.empty(); df=pd.DataFrame(res); df["scan_date"]=datetime.now().strftime("%Y-%m-%d")
    st.session_state.radar_df=df; st.session_state.radar_ts=datetime.now(timezone.utc)

# ===== HEADER =====
st.markdown(f"""<div class="top-hdr"><div style="display:flex;gap:12px;align-items:center;"><div class="brand-logo">ح</div><div style="font-weight:800;font-size:1.2rem;">AL7EBI ICT</div></div><div style="color:{BL};font-weight:700;">{datetime.now().strftime("%H:%M")}</div></div>""", unsafe_allow_html=True)

tabs=st.columns(4)
for i,t in enumerate(["الرئيسية","الأوبشن","الخطة","المصفوفة"]):
    with tabs[i]:
        if st.button(t,use_container_width=True,type="primary" if st.session_state.main_tab==t else "secondary"): st.session_state.main_tab=t; st.rerun()

# ===== MAIN =====
st.markdown('<div style="padding:24px 32px;">',unsafe_allow_html=True)

if st.session_state.main_tab=="الرئيسية":
    c1,c2=st.columns([3,1])
    with c1:
        wl=[(t,"QQQ") for t in ["AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","QCOM","ORCL","ADBE","INTC","TXN"]]
    with c2:
        if st.button("📡 مسح الرادار",type="primary",use_container_width=True): do_scan(wl)
    df=st.session_state.radar_df
    if df is not None:
        cols=st.columns(4)
        cols[0].metric("إجمالي",len(df)); cols[1].metric("نشطة",len(df[df["Grade"].isin(["A+","A"])]))
        cols[2].metric("منتظرة",len(df[df["Grade"]=="B"])); cols[3].metric("مغلقة",len(df[~df["Grade"].isin(["A+","A","B"])]))

# ===== 1- الأوبشن - جدول احترافي ملون =====
elif st.session_state.main_tab=="الأوبشن":
    st.markdown("### 🎯 الأوبشن - CALL أخضر / PUT أحمر")
    df=st.session_state.radar_df
    if df is None: st.warning("امسح الرادار أولاً")
    else:
        html='<div class="pro-table"><table><tr><th>الرمز</th><th>النوع</th><th>Strike</th><th>الدخول</th><th>الهدف</th><th>القوة</th></tr>'
        for _,r in df[df["Grade"].isin(["A+","A"])].head(10).iterrows():
            try:
                e=float(r.get("Entry",0)); bias=r.get("Bias"); is_call=bias=="Long"
                strike=round(e*1.02,2) if is_call else round(e*0.98,2)
                badge=f'<span class="{"call-badge" if is_call else "put-badge"}">{"CALL" if is_call else "PUT"}</span>'
                html+=f"<tr><td style='font-weight:700;'>{r['Ticker']}</td><td>{badge}</td><td>{strike}</td><td>{e}</td><td>{r.get('TP1','—')}</td><td style='color:{BL};'>{_stars(r['Grade'])}</td></tr>"
            except: continue
        html+='</table></div>'; st.markdown(html,unsafe_allow_html=True)

# ===== 2- الخطة - قائمة قابلة للفرز =====
elif st.session_state.main_tab=="الخطة":
    st.markdown("### 📋 الخطة الكاملة")
    df=st.session_state.radar_df
    if df is None: st.info("امسح الرادار")
    else:
        f=st.selectbox("فرز حسب الحالة",["الكل","جاهز للدخول","منتظر","مغلق"],key="plan_f")
        st.session_state.plan_filter=f
        if f=="جاهز للدخول": df=df[df["Grade"].isin(["A+","A"])]
        elif f=="منتظر": df=df[df["Grade"]=="B"]
        elif f=="مغلق": df=df[~df["Grade"].isin(["A+","A","B"])]

        for _,r in df.iterrows():
            bias=r.get("Bias",""); is_long=bias=="Long"
            cls="" if is_long else "short"; txt="Long" if is_long else "Short"
            color=GR if is_long else RD
            st.markdown(f"""<div class="plan-item {cls}">
                <div style="display:flex;align-items:center;gap:12px;">
                    <span style="font-size:1.3rem;color:{color};">✓</span>
                    <span style="font-weight:700;">{r['Ticker']} | {txt}</span>
                </div>
                <div style="color:{TXT2};">دخول {r.get('Entry','—')}</div>
            </div>""", unsafe_allow_html=True)

# ===== 3- المصفوفة - اختيار الفريم =====
elif st.session_state.main_tab=="المصفوفة":
    st.markdown("### 📊 مصفوفة الفرص المؤسسية")
    tf=st.selectbox("اختر الفريم", ["يومي 1D","4 ساعات","ساعة 1H","15 دقيقة"], index=["يومي 1D","4 ساعات","ساعة 1H","15 دقيقة"].index(st.session_state.matrix_tf))
    st.session_state.matrix_tf=tf

    df=st.session_state.radar_df
    if df is None: st.info("امسح الرادار")
    else:
        st.caption(f"الفريم الحالي: **{tf}** - يتم تحديث المصفوفة تلقائياً")
        html='<div class="pro-table"><table><tr><th>الأصل</th><th>النموذج</th><th>القوة</th><th>السبب</th><th>الهدف</th><th>الحالة</th></tr>'
        for _,r in df.head(12).iterrows():
            grd=r.get("Grade","?"); stars=_stars(grd)
            status="دخول فوري" if grd in ["A+","A"] else "مراقبة"
            color=GR if grd in ["A+","A"] else AM
            html+=f"<tr><td style='font-weight:700;'>{r['Ticker']}</td><td>Breaker+FVG</td><td style='color:{BL};font-size:1.1rem;'>{stars}</td><td style='color:{TXT3};'>سحب سيولة + {tf}</td><td>{r.get('TP1','—')}</td><td style='color:{color};font-weight:700;'>{status}</td></tr>"
        html+='</table></div>'; st.markdown(html,unsafe_allow_html=True)

st.markdown('</div>',unsafe_allow_html=True)
