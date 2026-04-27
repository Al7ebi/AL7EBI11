import streamlit as st
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import engine as E

# 1. الإعدادات التقنية الصارمة
st.set_page_config(page_title="AL7EBI ELITE", page_icon="🔶", layout="wide", initial_sidebar_state="collapsed")

# 2. لوحة ألوان "فايبرنت دارك" (Vibrant Dark)
BG = "#0B0E14"          # خلفية داكنة جداً
CARD_BG = "#151921"      # لون البطاقات
ACCENT = "#D4AF37"      # ذهبي منصة الحبي
SUCCESS = "#00C853"      # أخضر حيوي
DANGER = "#FF3D00"       # أحمر حيوي
BORDER = "rgba(255, 255, 255, 0.05)"

# 3. CSS "المستوى الرابع" (تنسيق احترافي شامل)
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;500;700;900&display=swap');

/* تنسيق الجسم العام */
.stApp {{ background-color: {BG}; font-family: 'Tajawal', sans-serif!important; color: white!important; }}

/* هيدر المنصة الاحترافي */
.top-nav {{
    background: {CARD_BG};
    padding: 15px 30px;
    border-bottom: 1px solid {BORDER};
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-radius: 0 0 20px 20px;
    margin-bottom: 25px;
}}

/* صناديق الإحصائيات العلوي */
.metric-box {{
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 15px;
    text-align: center;
}}
.metric-val {{ font-size: 20px; font-weight: 900; color: {ACCENT}; }}
.metric-lbl {{ font-size: 10px; opacity: 0.5; text-transform: uppercase; }}

/* تأثير النبض للسوق */
.pulse-green {{
    width: 8px; height: 8px; background: {SUCCESS}; border-radius: 50%;
    box-shadow: 0 0 0 0 rgba(0, 200, 83, 1);
    animation: pulse-green 2s infinite;
}}
@keyframes pulse-green {{
    0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 200, 83, 0.7); }}
    70% {{ transform: scale(1); box-shadow: 0 0 0 10px rgba(0, 200, 83, 0); }}
    100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 200, 83, 0); }}
}}

/* تصميم بطاقة الصفقة "المحترف" */
.trade-card-pro {{
    background: linear-gradient(145deg, {CARD_BG}, #1c222d);
    border: 1px solid {BORDER};
    border-radius: 16px;
    padding: 20px;
    position: relative;
    overflow: hidden;
    transition: 0.4s;
}}
.trade-card-pro:hover {{ border-color: {ACCENT}; transform: translateY(-5px); box-shadow: 0 12px 20px rgba(0,0,0,0.4); }}
.side-indicator {{ position: absolute; top: 0; right: 0; width: 4px; height: 100%; }}

/* الأزرار الاحترافية */
.stButton>button {{
    background: {ACCENT}!important; color: black!important; font-weight: 700!important;
    border-radius: 10px!important; border: none!important; padding: 12px 24px!important;
}}

/* إخفاء الزوائد */
#MainMenu, footer, header {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)

# 4. بناء الهيدر العلوي (Navbar)
st.markdown(f"""
<div class="top-nav">
    <div style="display:flex; align-items:center; gap:15px;">
        <div style="background:{ACCENT}; width:40px; height:40px; border-radius:10px; display:flex; align-items:center; justify-content:center; color:black; font-weight:900; font-size:20px;">ح</div>
        <div>
            <div style="font-weight:900; font-size:18px; letter-spacing:1px;">AL7EBI <span style="color:{ACCENT};">ELITE</span></div>
            <div style="display:flex; align-items:center; gap:8px;">
                <div class="pulse-green"></div>
                <span style="font-size:10px; opacity:0.6;">LIVE MARKET ENGINE</span>
            </div>
        </div>
    </div>
    <div style="text-align:left;">
        <div style="font-size:12px; opacity:0.5;">{datetime.now().strftime("%H:%M:%S UTC")}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 5. إدارة الحالة (State) والبيانات
if "main_tab" not in st.session_state: st.session_state.main_tab = "الرئيسية"
if "radar_df" not in st.session_state: st.session_state.radar_df = None

def run_elite_scan():
    watchlist = [("AAPL","QQQ"), ("TSLA","QQQ"), ("NVDA","QQQ"), ("MSFT","QQQ"), ("AMD","QQQ"), ("META","QQQ"), ("GOOGL","QQQ")]
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

# 6. شريط التنقل (Navigation)
menu_cols = st.columns([1,1,1,1,5])
tabs = ["الرئيسية", "الأوبشن", "الخطة", "المصفوفة"]
for i, tab in enumerate(tabs):
    with menu_cols[i]:
        if st.button(tab, use_container_width=True, type="primary" if st.session_state.main_tab == tab else "secondary"):
            st.session_state.main_tab = tab
            st.rerun()

# 7. التبويبات والمحتوى الاحترافي
st.markdown('<div style="padding:0 10px;">', unsafe_allow_html=True)

if st.session_state.main_tab == "الرئيسية":
    # قسم الإحصائيات (Metrics)
    m1, m2, m3, m4 = st.columns(4)
    df = st.session_state.radar_df
    
    with m1: st.markdown(f'<div class="metric-box"><div class="metric-lbl">إجمالي الأسهم</div><div class="metric-val">{len(df) if df is not None else 0}</div></div>', unsafe_allow_html=True)
    with m2: st.markdown(f'<div class="metric-box"><div class="metric-lbl">إشارات الشراء</div><div class="metric-val" style="color:{SUCCESS}">{len(df[df["Bias"]=="Long"]) if df is not None else 0}</div></div>', unsafe_allow_html=True)
    with m3: st.markdown(f'<div class="metric-box"><div class="metric-lbl">إشارات البيع</div><div class="metric-val" style="color:{DANGER}">{len(df[df["Bias"]=="Short"]) if df is not None else 0}</div></div>', unsafe_allow_html=True)
    with m4: 
        if st.button("📡 تحديث الرادار", use_container_width=True): run_elite_scan()

    st.markdown("<br>", unsafe_allow_html=True)

    if df is not None:
        grid = st.columns(3)
        for i, (_, r) in enumerate(df.iterrows()):
            bias = r.get("Bias", "Long")
            color = SUCCESS if bias == "Long" else DANGER
            with grid[i % 3]:
                st.markdown(f"""
                <div class="trade-card-pro">
                    <div class="side-indicator" style="background:{color};"></div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div style="font-size:10px; opacity:0.5;">TICKER</div>
                            <div style="font-size:24px; font-weight:900;">{r.get('Ticker')}</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:10px; opacity:0.5;">GRADE</div>
                            <div style="font-size:18px; font-weight:700; color:{ACCENT};">{r.get('Grade')}</div>
                        </div>
                    </div>
                    <hr style="border:0; border-top:1px solid {BORDER}; margin:15px 0;">
                    <div style="display:flex; justify-content:space-between;">
                        <div>
                            <div style="font-size:9px; opacity:0.5;">ENTRY</div>
                            <div style="font-size:16px; font-weight:700;">{r.get('Entry')}</div>
                        </div>
                        <div>
                            <div style="font-size:9px; opacity:0.5;">TARGET</div>
                            <div style="font-size:16px; font-weight:700; color:{SUCCESS};">{r.get('TP1')}</div>
                        </div>
                        <div>
                            <div style="font-size:9px; opacity:0.5;">STOP</div>
                            <div style="font-size:16px; font-weight:700; color:{DANGER};">{r.get('SL')}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("قم ببدء مسح الرادار لتحليل تدفقات السيولة.")

# الأقسام الأخرى تتبع نفس الفخامة...
st.markdown('</div>', unsafe_allow_html=True)
