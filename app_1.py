import streamlit as st
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import engine as E

# 1. إعدادات الصفحة الفنية
st.set_page_config(page_title="AL7EBI PRO", page_icon="🔶", layout="wide", initial_sidebar_state="collapsed")

# 2. لوحة الألوان الاحترافية (Habbi Premium Palette)
BG = "#080B10"          # خلفية غامقة جداً
CARD = "rgba(23, 28, 40, 0.7)" # بطاقة زجاجية
BRD = "rgba(255, 255, 255, 0.08)"
TXT = "#FFFFFF"
GOLD = "#D4AF37"        # ذهبي ملكي
SUCCESS = "#00F2A6"     # أخضر نيون
DANGER = "#FF4B4B"      # أحمر صريح
ACCENT = "#3B82F6"      # أزرق تقني

# 3. إدارة الجلسة
if "main_tab" not in st.session_state: st.session_state.main_tab = "الرئيسية"
if "radar_df" not in st.session_state: st.session_state.radar_df = None

# 4. CSS المتقدم (التصميم الاحترافي)
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;500;800&display=swap');

/* تنسيق الخلفية العامة */
.stApp {{
    background: radial-gradient(circle at top right, #1a1f2c, {BG});
    font-family: 'Tajawal', sans-serif!important;
}}

/* تصميم الهيدر العلوي */
.nav-container {{
    background: {CARD};
    backdrop-filter: blur(10px);
    border-bottom: 1px solid {BRD};
    padding: 10px 40px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: sticky;
    top: 0;
    z-index: 1000;
    margin-bottom: 30px;
}}

/* تصميم البطاقة الاحترافية */
.glass-card {{
    background: {CARD};
    backdrop-filter: blur(15px);
    border: 1px solid {BRD};
    border-radius: 20px;
    padding: 20px;
    margin-bottom: 20px;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}}
.glass-card:hover {{
    border-color: {GOLD};
    transform: translateY(-5px);
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
}}

/* مؤشرات الحالة */
.status-pill {{
    padding: 4px 12px;
    border-radius: 30px;
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1px;
}}
.pill-long {{ background: rgba(0, 242, 166, 0.1); color: {SUCCESS}; border: 1px solid {SUCCESS}; }}
.pill-short {{ background: rgba(255, 75, 75, 0.1); color: {DANGER}; border: 1px solid {DANGER}; }}

/* تحسين الجداول والأزرار */
.stButton>button {{
    background: linear-gradient(135deg, {GOLD}, #B8860B)!important;
    color: black!important;
    font-weight: 800!important;
    border: none!important;
    border-radius: 12px!important;
    padding: 10px 25px!important;
    transition: 0.3s!important;
}}
.stButton>button:hover {{
    transform: scale(1.05)!important;
    box-shadow: 0 0 20px rgba(212, 175, 55, 0.4)!important;
}}

/* إخفاء عناصر ستريم ليت الافتراضية */
#MainMenu, footer, header {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)

# 5. الهيدر الاحترافي (Custom Navbar)
st.markdown(f"""
<div class="nav-container">
    <div style="display:flex; align-items:center; gap:15px;">
        <div style="background:{GOLD}; width:42px; height:42px; border-radius:12px; display:flex; align-items:center; justify-content:center; color:black; font-weight:900; font-size:22px;">ح</div>
        <div>
            <div style="font-weight:800; font-size:18px; letter-spacing:1px;">AL7EBI <span style="color:{GOLD};">PLATFORM</span></div>
            <div style="font-size:10px; opacity:0.5; margin-top:-5px;">PRECISION TRADING ENGINE</div>
        </div>
    </div>
    <div style="text-align:left;">
        <div style="color:{GOLD}; font-weight:500; font-size:14px;">{datetime.now().strftime("%A, %d %B")}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 6. شريط التبويبات (Custom Tabs)
t_cols = st.columns([1,1,1,1,4]) # توزيع الأزرار لليمين
menu = ["الرئيسية", "الأوبشن", "الخطة", "المصفوفة"]
for i, m in enumerate(menu):
    with t_cols[i]:
        if st.button(m, use_container_width=True, type="primary" if st.session_state.main_tab == m else "secondary"):
            st.session_state.main_tab = m
            st.rerun()

# 7. وظيفة المسح (Engine)
def run_scan():
    watchlist = [("AAPL","QQQ"), ("TSLA","QQQ"), ("NVDA","QQQ"), ("MSFT","QQQ"), ("AMD","QQQ"), ("META","QQQ")]
    total = len(watchlist); res = []
    pb = st.progress(0)
    with ThreadPoolExecutor(max_workers=5) as pool:
        futs = {pool.submit(E.run_engine, p[0], p[1]): p for p in watchlist}
        for i, f in enumerate(as_completed(futs)):
            raw = f.result()
            row = E.extract_row(raw[0], futs[f][0], futs[f][1])
            res.append(row)
            pb.progress((i + 1) / total)
    pb.empty()
    st.session_state.radar_df = pd.DataFrame(res)

# 8. محتوى التبويبات بتصميم جديد
st.markdown('<div style="padding:0 20px;">', unsafe_allow_html=True)

if st.session_state.main_tab == "الرئيسية":
    c1, c2 = st.columns([5,1])
    with c2:
        if st.button("📡 تحديث الرادار", use_container_width=True): run_scan()
    
    df = st.session_state.radar_df
    if df is not None:
        # عرض البطاقات في شبكة (Grid)
        cols = st.columns(3)
        for i, (idx, r) in enumerate(df.iterrows()):
            with cols[i % 3]:
                bias = r.get("Bias", "Long")
                grd = r.get("Grade", "B")
                pill_class = "pill-long" if bias == "Long" else "pill-short"
                
                st.markdown(f"""
                <div class="glass-card">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:15px;">
                        <div>
                            <div style="font-size:22px; font-weight:800; color:{GOLD};">{r.get('Ticker')}</div>
                            <div style="font-size:12px; opacity:0.6;">{grd} Setup</div>
                        </div>
                        <span class="status-pill {pill_class}">{bias}</span>
                    </div>
                    <div style="background:rgba(0,0,0,0.2); padding:12px; border-radius:12px; margin-bottom:15px;">
                        <div style="display:flex; justify-content:space-between; font-size:13px;">
                            <span style="opacity:0.6;">دخول</span>
                            <b style="color:{ACCENT};">{r.get('Entry')}</b>
                        </div>
                        <div style="display:flex; justify-content:space-between; font-size:13px; margin-top:5px;">
                            <span style="opacity:0.6;">هدف أول</span>
                            <b style="color:{SUCCESS};">{r.get('TP1')}</b>
                        </div>
                    </div>
                    <div style="font-size:10px; text-align:center; opacity:0.4;">
                        Habbi Engine v2.0 • Smart Money Concepts
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("النظام بانتظار أمر المسح لبدء تحليل السيولة الذكية.")

elif st.session_state.main_tab == "الأوبشن":
    st.markdown(f"<h2 style='color:{GOLD};'>🎯 صائد العقود</h2>", unsafe_allow_html=True)
    df = st.session_state.radar_df
    if df is not None:
        for _, r in df[df["Grade"].isin(["A+","A"])].iterrows():
            is_call = r.get("Bias") == "Long"
            st.markdown(f"""
            <div class="glass-card" style="border-left: 5px solid {SUCCESS if is_call else DANGER};">
                <div style="display:flex; justify-content:space-between;">
                    <div>
                        <span style="font-size:20px; font-weight:800;">{r.get('Ticker')}</span>
                        <span style="margin-right:15px; color:{SUCCESS if is_call else DANGER};">● {'CALL' if is_call else 'PUT'}</span>
                    </div>
                    <div style="text-align:left;">
                        <div style="font-size:12px; opacity:0.6;">نقطة التمركز</div>
                        <div style="font-size:18px; font-weight:800; color:{GOLD};">{r.get('Entry')}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# بقية التبويبات تتبع نفس النمط الزجاجي...
st.markdown('</div>', unsafe_allow_html=True)
