import streamlit as st
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import engine as E

# 1. إعدادات الصفحة
st.set_page_config(page_title="AL7EBI PRO", layout="wide", initial_sidebar_state="collapsed")

# 2. مخازن البيانات
if "main_tab" not in st.session_state: st.session_state.main_tab = "الرئيسية"
if "radar_df" not in st.session_state: st.session_state.radar_df = None

# 3. التصميم الاحترافي (CSS)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    
    /* الخلفية العامة */
    .stApp { background-color: #0E1117; font-family: 'Tajawal', sans-serif; }
    
    /* تصميم الهيدر العلوي */
    .header-box {
        background: linear-gradient(90deg, #161B22 0%, #0D1117 100%);
        padding: 20px;
        border-bottom: 2px solid #D4AF37;
        margin-bottom: 30px;
        border-radius: 0 0 15px 15px;
    }
    
    /* تصميم البطاقات الاحترافي */
    .data-card {
        background: #1C2128;
        border: 1px solid #30363D;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        transition: 0.3s;
    }
    .data-card:hover { border-color: #D4AF37; transform: translateY(-2px); }
    
    /* الأزرار */
    .stButton>button {
        background-color: #D4AF37 !important;
        color: #000 !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: none !important;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# 4. الهيدر
st.markdown('<div class="header-box"><h1 style="color:#D4AF37; text-align:center; margin:0;">منصة الحبي للتحليل الذكي</h1></div>', unsafe_allow_html=True)

# 5. التبويبات
t_cols = st.columns(4)
menu = ["الرئيسية", "الأوبشن", "الخطة", "المصفوفة"]
for i, name in enumerate(menu):
    with t_cols[i]:
        if st.button(name):
            st.session_state.main_tab = name
            st.rerun()

# 6. الوظائف
def run_scan():
    watchlist = [("AAPL","QQQ"), ("TSLA","QQQ"), ("NVDA","QQQ"), ("MSFT","QQQ")]
    res = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futs = {pool.submit(E.run_engine, p[0], p[1]): p for p in watchlist}
        for f in as_completed(futs):
            raw = f.result()
            res.append(E.extract_row(raw[0], futs[f][0], futs[f][1]))
    st.session_state.radar_df = pd.DataFrame(res)

# 7. المحتوى حسب التبويب
df = st.session_state.radar_df

if st.session_state.main_tab == "الرئيسية":
    if st.button("📡 بدء فحص الرادار"): run_scan()
    if df is not None:
        for _, r in df.iterrows():
            st.markdown(f"""
            <div class="data-card">
                <span style="color:#D4AF37; font-size:20px; font-weight:900;">{r['Ticker']}</span> 
                <span style="float:left; color:#10B981;">{r['Grade']}</span>
                <br><small style="color:#8B949E;">نقطة الدخول: {r['Entry']} | الهدف: {r['TP1']}</small>
            </div>
            """, unsafe_allow_html=True)

elif st.session_state.main_tab == "الأوبشن":
    if df is not None:
        st.subheader("🎯 صفقات الأوبشن المختارة")
        for _, r in df[df["Grade"].isin(["A+","A"])].iterrows():
            st.info(f"عقد مقترح لـ {r['Ticker']} - الاتجاه: {r['Bias']}")
    else: st.warning("يجب إجراء المسح من الرئيسية أولاً")

elif st.session_state.main_tab == "الخطة":
    if df is not None:
        st.table(df[["Ticker", "Entry", "SL", "TP1"]])

elif st.session_state.main_tab == "المصفوفة":
    if df is not None:
        st.dataframe(df.style.highlight_max(axis=0, color='#D4AF37'), use_container_width=True)
