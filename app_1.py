"""
app_1.py — AL7EBI ICT v2.2
بطاقات ملونة حسب الاتجاه والحالة
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import engine as E

st.set_page_config(page_title="AL7EBI ICT", page_icon="🔶", layout="wide")

_DEFAULTS = {"radar_df":None,"radar_ts":None,"main_tab":"الرئيسية","matrix_tf":"يومي 1D"}
for k,v in _DEFAULTS.items():
    if k not in st.session_state: st.session_state[k]=v

BG="#0A0E14"; CARD="#121821"; BRD="#1E293B"; TXT="#E2E8F5"; TXT2="#94A3B8"; TXT3="#64748B"
BL="#D4AF37"; GR="#10B981"; RD="#EF4444"; AM="#F59E0B"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;800&display=swap');
html,body{{background:{BG}!important;font-family:'Tajawal',sans-serif!important;color:{TXT}!important;direction:rtl!important;}}
.card-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:18px;}}
.trade-card{{background:{CARD};border:1px solid {BRD};border-radius:16px;padding:20px;transition:all.2s;position:relative;}}
.trade-card.long-active{{border-top:3px solid {GR};background:linear-gradient(180deg,rgba(16,185,129,0.06),{CARD});}}
.trade-card.short-active{{border-top:3px solid {RD};background:linear-gradient(180deg,rgba(239,68,68,0.06),{CARD});}}
.trade-card.waiting{{border-top:3px solid {AM};background:linear-gradient(180deg,rgba(245,158,11,0.06),{CARD});}}
.trade-card.closed{{border-top:3px solid {TXT3};background:{CARD};opacity:0.7;}}
.grade-badge{{background:#1E293B;padding:6px 12px;border-radius:8px;font-weight:800;color:{BL};display:inline-block;}}
.stars{{color:{BL};font-size:1.1rem;margin-top:6px;}}
.card-top{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px;}}
.ticker{{font-size:1.4rem;font-weight:900;}}
.date{{color:{TXT3};font-size:0.85rem;}}
.field-row{{display:flex;justify-content:space-between;margin:8px 0;font-size:0.95rem;}}
.field-label{{color:{TXT2};}}
.field-val{{font-weight:700;}}
.status-active{{background:rgba(16,185,129,0.15);color:{GR};padding:5px 14px;border-radius:20px;font-size:0.8rem;font-weight:700;}}
.status-wait{{background:rgba(245,158,11,0.15);color:{AM};padding:5px 14px;border-radius:20px;font-size:0.8rem;font-weight:700;}}
.status-closed{{background:rgba(100,116,139,0.15);color:{TXT3};padding:5px 14px;border-radius:20px;font-size:0.8rem;font-weight:700;}}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def _row(t,s):
    try: r=E.run_engine(t,s); return E.extract_row(r[0],t,s)
    except: return E.extract_row(None,t,s)

def _stars(g): n={"A+":3,"A":3,"B":2}.get(g,1); return "★"*n

def do_scan():
    wl=[(t,"QQQ") for t in ["MSFT","GOOGL","TSLA","ORCL","ADBE","AAPL","NVDA","META"]]
    res=[]; pb=st.progress(0)
    with ThreadPoolExecutor(max_workers=4) as p:
        futs={p.submit(_row,t,s):t for t,s in wl}
        for i,f in enumerate(as_completed(futs)): res.append(f.result()); pb.progress((i+1)/len(wl))
    pb.empty(); df=pd.DataFrame(res); df["scan_date"]=datetime.now().strftime("%Y-%m-%d")
    st.session_state.radar_df=df

# ===== HEADER =====
st.markdown(f"""<div style="background:{CARD};padding:16px 32px;border-bottom:2px solid {BL};display:flex;justify-content:space-between;align-items:center;">
<div style="display:flex;gap:12px;align-items:center;"><div style="width:44px;height:44px;background:linear-gradient(135deg,{BL},#B8941F);border-radius:12px;display:flex;align-items:center;justify-content:center;font-weight:900;color:#000;">ح</div>
<div style="font-weight:800;font-size:1.2rem;">AL7EBI ICT</div></div><div style="color:{BL};font-weight:700;">{datetime.now().strftime("%H:%M")}</div></div>""", unsafe_allow_html=True)

tabs=st.columns(4)
for i,t in enumerate(["الرئيسية","الأوبشن","الخطة","المصفوفة"]):
    with tabs[i]:
        if st.button(t,use_container_width=True,type="primary" if st.session_state.main_tab==t else "secondary"):
            st.session_state.main_tab=t; st.rerun()

st.markdown('<div style="padding:24px 32px;">',unsafe_allow_html=True)

if st.session_state.main_tab=="الرئيسية":
    if st.button("📡 مسح الرادار",type="primary"): do_scan()
    df=st.session_state.radar_df

    if df is not None:
        # إحصائيات
        c1,c2,c3,c4=st.columns(4)
        c1.metric("إجمالي",len(df)); c2.metric("نشطة",len(df[df["Grade"].isin(["A+","A"])]))
        c3.metric("منتظرة",len(df[df["Grade"]=="B"])); c4.metric("مغلقة",len(df[~df["Grade"].isin(["A+","A","B"])]))

        # ===== البطاقات الملونة =====
        html='<div class="card-grid">'
        for _,r in df.iterrows():
            tkr=r.get("Ticker","?"); grd=r.get("Grade","?"); bias=r.get("Bias","Long")
            entry=r.get("Entry","—"); sl=r.get("SL","—"); tp1=r.get("TP1","—"); tp2=r.get("TP2 (Ext)","—")
            rr=r.get("Best R:R","—"); date=r.get("scan_date","2026-04-27")

            # تحديد الحالة واللون
            if grd in ["A+","A"]:
                status="نشط"; status_cls="status-active"
                card_cls="long-active" if bias=="Long" else "short-active"
            elif grd=="B":
                status="منتظر"; status_cls="status-wait"; card_cls="waiting"
            else:
                status="منتهية"; status_cls="status-closed"; card_cls="closed"

            dir_txt="شراء ▲" if bias=="Long" else "بيع ▼"
            dir_color=GR if bias=="Long" else RD

            html+=f"""
            <div class="trade-card {card_cls}">
                <div class="card-top">
                    <div>
                        <div class="grade-badge">{grd}</div>
                        <div class="stars">{_stars(grd)}</div>
                    </div>
                    <div style="text-align:left;">
                        <div class="ticker">{tkr}</div>
                        <div class="date">{date}</div>
                    </div>
                </div>
                <div class="field-row">
                    <span class="field-label">الاتجاه:</span>
                    <span class="field-val" style="color:{dir_color};">{dir_txt}</span>
                </div>
                <div class="field-row">
                    <span class="field-label">الدخول:</span>
                    <span class="field-val">{entry}</span>
                </div>
                <div class="field-row">
                    <span class="field-label">الوقف:</span>
                    <span class="field-val" style="color:{RD};">{sl}</span>
                </div>
                <div class="field-row">
                    <span class="field-label">هدف1:</span>
                    <span class="field-val" style="color:{GR};">{tp1}</span>
                </div>
                <div class="field-row">
                    <span class="field-label">الموجة:</span>
                    <span class="field-val" style="color:{AM};">{tp2}</span>
                </div>
                <div class="field-row">
                    <span class="field-label" style="color:{TXT3};">R:R:</span>
                    <span class="field-val">{rr}</span>
                </div>
                <div style="margin-top:16px;padding-top:14px;border-top:1px solid {BRD};">
                    <span class="{status_cls}">{status}</span>
                </div>
            </div>
            """
        html+='</div>'
        st.markdown(html, unsafe_allow_html=True)

# باقي التبويبات (الأوبشن، الخطة، المصفوفة) كما في الكود السابق
elif st.session_state.main_tab=="الأوبشن":
    st.markdown("### 🎯 الأوبشن")
    df=st.session_state.radar_df
    if df is not None:
        for _,r in df.head(5).iterrows():
            is_call=r.get("Bias")=="Long"
            color=GR if is_call else RD
            st.markdown(f"<div style='padding:12px;background:{CARD};margin:6px 0;border-right:4px solid {color};border-radius:8px;'>{r['Ticker']} | {'CALL' if is_call else 'PUT'} | دخول {r.get('Entry')}</div>", unsafe_allow_html=True)

st.markdown('</div>',unsafe_allow_html=True)
