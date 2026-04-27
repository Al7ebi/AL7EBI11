"""
app_1.py — منصة الحبي (النسخة المستقرة)
نفس كودك الأصلي + بطاقات ملونة فقط
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
import engine as E

st.set_page_config(page_title="منصة الحبي للتداول", page_icon="ح", layout="wide", initial_sidebar_state="collapsed")

_DEFAULTS = {
    "theme": "dark", "market_tab": "US", "radar_df": None, "radar_ts": None,
    "drill": None, "search_q": "", "sort_by": "القوة", "filter_grade": "جميع القوة", "view_mode": "بطاقات",
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state: st.session_state[k] = v

DARK = True
BG="#0C0E16"; CARD="#12151F"; BRD="#1C2136"; TXT="#E2E8F5"; TXT2="#8896B2"
BL="#3B82F6"; GR="#10B981"; RD="#EF4444"; AM="#F59E0B"

# CSS الأصلي + إضافة بسيطة للبطاقات الملونة
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
html,body{{background:{BG}!important;font-family:'Tajawal',sans-serif!important;color:{TXT}!important;direction:rtl!important;}}
.main.block-container{{padding:20px!important;}}
.trade-card{{background:{CARD};border:1px solid {BRD};border-radius:12px;padding:16px;margin-bottom:12px;}}
.trade-card.long{{border-right:4px solid {GR};}}
.trade-card.short{{border-right:4px solid {RD};}}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300, show_spinner=False)
def _row(ticker, smt):
    try: res = E.run_engine(ticker, smt); return E.extract_row(res[0], ticker, smt)
    except: return E.extract_row(None, ticker, smt)

SA_WATCHLIST = [("2222","2222"),("1120","2222"),("2010","2222"),("7010","2222")]
US_WATCHLIST = [(t,"QQQ") for t in ["AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","MSFT","GOOGL","TSLA"]]

# هيدر بسيط
st.markdown(f"<h2 style='color:{BL};text-align:center;'>🔶 منصة الحبي للتداول</h2>", unsafe_allow_html=True)

# اختيار السوق
col1, col2 = st.columns(2)
with col1:
    if st.button("🇸🇦 السوق السعودي", use_container_width=True): st.session_state.market_tab="SA"
with col2:
    if st.button("🇺🇸 السوق الأمريكي", use_container_width=True): st.session_state.market_tab="US"

watchlist = SA_WATCHLIST if st.session_state.market_tab=="SA" else US_WATCHLIST

# زر المسح
if st.button("📡 مسح الرادار الآن", type="primary", use_container_width=True):
    results = []
    with st.spinner("جاري التحليل..."):
        with ThreadPoolExecutor(max_workers=4) as pool:
            futs = {pool.submit(_row, t, s): t for t, s in watchlist}
            for f in as_completed(futs): results.append(f.result())
    df = pd.DataFrame(results)
    st.session_state.radar_df = df
    st.session_state.radar_ts = datetime.now(timezone.utc)
    st.success(f"تم تحليل {len(df)} سهم")

# عرض النتائج
df = st.session_state.radar_df
if df is not None and not df.empty:
    st.markdown("---")
    for _, r in df.iterrows():
        ticker = r.get("Ticker","?")
        grade = r.get("Grade","?")
        bias = r.get("Bias","Long")
        entry = r.get("Entry","—")
        tp1 = r.get("TP1","—")
        sl = r.get("SL","—")

        # تحديد اللون
        card_class = "long" if bias=="Long" else "short"
        dir_text = "شراء 🟢" if bias=="Long" else "بيع 🔴"
        dir_color = GR if bias=="Long" else RD

        st.markdown(f"""
        <div class="trade-card {card_class}">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div><b style="font-size:18px;">{ticker}</b> <span style="color:{BL};">{grade}</span></div>
                <div style="color:{dir_color};font-weight:bold;">{dir_text}</div>
                <div>دخول: <b>{entry}</b> | هدف: <b style="color:{GR};">{tp1}</b> | وقف: <b style="color:{RD};">{sl}</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("اضغط 'مسح الرادار' لبدء التحليل")
