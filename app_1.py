import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import engine as E

st.set_page_config(page_title="منصة الحبي", page_icon="🔶", layout="wide")

# ألوان ثابتة
BG="#0A0E14"; CARD="#121821"; BL="#D4AF37"; GR="#10B981"; RD="#EF4444"; TXT="#E2E8F5"

st.markdown(f"""
<style>
body{{background:{BG};color:{TXT};direction:rtl;font-family:'Tajawal',sans-serif;}}
.card{{background:{CARD};border-radius:12px;padding:15px;margin:8px 0;border-right:4px solid #333;}}
.card.long{{border-right-color:{GR};}}
.card.short{{border-right-color:{RD};}}
</style>
""", unsafe_allow_html=True)

if "radar_df" not in st.session_state: st.session_state.radar_df = None

@st.cache_data(ttl=300)
def _row(t,s):
    try: r=E.run_engine(t,s); return E.extract_row(r[0],t,s)
    except: return E.extract_row(None,t,s)

# قوائم
US = [(t,"QQQ") for t in ["MSFT","GOOGL","TSLA","AAPL","NVDA","META","AMZN","ORCL"]]
SA = [("2222","2222"),("1120","2222"),("2010","2222")]

st.title("🔶 منصة الحبي")

# ===== التبويبات الأربعة =====
tab1, tab2, tab3, tab4 = st.tabs(["🏠 الرئيسية", "🎯 الأوبشن", "📋 الخطة", "📊 المصفوفة"])

# ===== 1- الرئيسية =====
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🇺🇸 أمريكي", use_container_width=True): st.session_state.market="US"
    with col2:
        if st.button("🇸🇦 سعودي", use_container_width=True): st.session_state.market="SA"

    market = st.session_state.get("market","US")
    wl = US if market=="US" else SA

    if st.button("📡 مسح الرادار", type="primary"):
        res=[]
        with st.spinner("يحلل..."):
            with ThreadPoolExecutor(max_workers=4) as p:
                for f in as_completed([p.submit(_row,t,s) for t,s in wl]): res.append(f.result())
        st.session_state.radar_df = pd.DataFrame(res)
        st.success(f"تم {len(res)} سهم")

    df = st.session_state.radar_df
    if df is not None:
        for _,r in df.iterrows():
            bias = r.get("Bias","Long")
            cls = "long" if bias=="Long" else "short"
            st.markdown(f"""<div class="card {cls}">
                <b>{r.get('Ticker')}</b> | {r.get('Grade')} | {'شراء' if bias=='Long' else 'بيع'}<br>
                دخول: {r.get('Entry','—')} | هدف: {r.get('TP1','—')}
            </div>""", unsafe_allow_html=True)

# ===== 2- الأوبشن =====
with tab2:
    st.subheader("توصيات الأوبشن")
    df = st.session_state.radar_df
    if df is None:
        st.warning("امسح الرادار من الرئيسية أولاً")
    else:
        for _,r in df.iterrows():
            if r.get("Grade") in ["A+","A","B"]:
                is_call = r.get("Bias")=="Long"
                color = GR if is_call else RD
                st.markdown(f"<div style='background:{CARD};padding:10px;margin:5px;border-right:4px solid {color};border-radius:8px;'>{r.get('Ticker')} - {'CALL' if is_call else 'PUT'} - {r.get('Entry')}</div>", unsafe_allow_html=True)

# ===== 3- الخطة =====
with tab3:
    st.subheader("الخطة اليومية")
    df = st.session_state.radar_df
    if df is None:
        st.warning("امسح الرادار أولاً")
    else:
        f = st.radio("فلتر", ["الكل","نشط","منتظر"], horizontal=True)
        d = df.copy()
        if f=="نشط": d = d[d["Grade"].isin(["A+","A"])]
        if f=="منتظر": d = d[d["Grade"]=="B"]
        st.dataframe(d[["Ticker","Grade","Bias","Entry","SL","TP1"]], use_container_width=True, hide_index=True)

# ===== 4- المصفوفة =====
with tab4:
    st.subheader("مصفوفة القوة")
    df = st.session_state.radar_df
    if df is None:
        st.warning("امسح الرادار أولاً")
    else:
        tf = st.selectbox("الفريم", ["1D","4H","1H","15m"])
        data = []
        for _,r in df.iterrows():
            data.append({
                "الأصل": r.get("Ticker"),
                "القوة": "★★★" if r.get("Grade") in ["A+","A"] else "★★",
                "الاتجاه": "صاعد" if r.get("Bias")=="Long" else "هابط",
                "الهدف": r.get("TP1"),
                "الفريم": tf
            })
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
