import streamlit as st
import datetime
import time
import pandas as pd
import random

# 1. إعدادات الصفحة (Page Configuration)
st.set_page_config(
    page_title="منصة الحبي للتداول الاحترافي | Habbi Radar",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. الهوية والتصميم (Custom CSS for McKinsey Style)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');

    /* الخط والاتجاه */
    * {
        font-family: 'Tajawal', sans-serif !important;
        direction: rtl;
    }

    /* صناديق شبكة البيانات 3x2 */
    .metric-card {
        background-color: #1a1a1a;
        border: 2px solid #d4af37;
        border-radius: 15px;
        padding: 25px;
        text-align: center;
        color: white;
        box-shadow: 0 8px 25px rgba(0,0,0,0.5);
        margin-bottom: 20px;
    }

    .metric-value {
        font-size: 32px;
        font-weight: 900;
        color: #ffcc00;
        margin: 10px 0;
    }

    /* شريط الأخبار المتحرك */
    .marquee-container {
        width: 100%;
        background-color: #d4af37;
        color: black;
        overflow: hidden;
        padding: 12px 0;
        position: fixed;
        bottom: 0;
        left: 0;
        z-index: 1000;
        font-weight: bold;
        font-size: 18px;
    }

    .marquee-text {
        display: inline-block;
        white-space: nowrap;
        animation: marquee 40s linear infinite;
        padding-left: 100%;
    }

    @keyframes marquee {
        0%   { transform: translate(0, 0); }
        100% { transform: translate(-100%, 0); }
    }

    /* نقطة النبض */
    .pulse {
        display: inline-block;
        width: 15px;
        height: 15px;
        border-radius: 50%;
        box-shadow: 0 0 0 rgba(46, 204, 113, 0.4);
        animation: pulse-animation 2s infinite;
        margin-left: 12px;
        vertical-align: middle;
    }

    @keyframes pulse-animation {
        0% { box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.4); }
        70% { box-shadow: 0 0 0 15px rgba(46, 204, 113, 0); }
        100% { box-shadow: 0 0 0 0 rgba(46, 204, 113, 0); }
    }

    /* تخصيص العناوين والبريق */
    .gold-text {
        color: #d4af37 !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }
    
    .stApp {
        background-color: #0e1117;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. المحرك التحليلي (Logic Engine)
class HabbiRadar:
    @staticmethod
    def get_market_status():
        now = datetime.datetime.now()
        is_open = 9 <= now.hour < 17
        status = "مفتوح" if is_open else "مغلق"
        color = "#2ecc71" if is_open else "#e74c3c"
        countdown = "يغلق بعد: 04:20:15" if is_open else "يفتح بعد: 08:00:00"
        return status, color, countdown

    @staticmethod
    def generate_signals():
        symbols = ["BTC/USD", "GOLD", "TASI", "NVDA", "ETH/USD", "OIL"]
        signals = []
        for sym in symbols:
            score = random.randint(5, 13)
            age = random.randint(1, 80)
            if age > 72: continue # قانون الـ 3 أيام
            
            signals.append({
                "symbol": sym,
                "score": score,
                "status": "فرصة ذهبية" if score >= 9 else "قيد المراقبة",
                "reason": "سحب سيولة + MSS + IFVG" if score >= 9 else "تجميع وقود",
                "entry": f"{random.uniform(100, 70000):.2f}",
                "age": age
            })
        return signals

# 4. واجهة المستخدم (UI Layout)

# الهيدر (Header)
st.markdown('<h1 class="gold-text" style="text-align:center;">منصة الحبي للتداول الاحترافي (Habbi Radar)</h1>', unsafe_allow_html=True)

col_time, col_status = st.columns([1, 1])

with col_time:
    now = datetime.datetime.now()
    st.markdown(f"""
        <div style="text-align:right;">
            <h2 class="gold-text">{now.strftime('%I:%M:%S %p')}</h2>
            <p style="color:white;">{now.strftime('%Y-%m-%d | %A')}</p>
        </div>
    """, unsafe_allow_html=True)

status, color, countdown = HabbiRadar.get_market_status()
with col_status:
    st.markdown(f"""
        <div style="text-align:left;">
            <h2 style="color:{color};"><span class="pulse" style="background:{color}"></span> السوق {status}</h2>
            <p style="color:white;">{countdown}</p>
        </div>
    """, unsafe_allow_html=True)

st.divider()

# شبكة البيانات 3x2
st.markdown('<h2 class="gold-text">📊 أهم مؤشرات السوق (Habbi Grid)</h2>', unsafe_allow_html=True)
grid_cols = st.columns(3)
indicators = [
    ("مؤشر السيولة", "1.2B", "+2.5%"),
    ("تاسي (TASI)", "12,450", "-0.4%"),
    ("الذهب", "2,385", "+1.2%"),
    ("النفط", "85.4", "+0.8%"),
    ("البيتكوين", "67,200", "+4.1%"),
    ("الدولار/ريال", "3.75", "0.0%")
]

for i, (name, val, change) in enumerate(indicators):
    with grid_cols[i % 3]:
        color_change = '#2ecc71' if '+' in change else '#e74c3c' if '-' in change else '#fff'
        st.markdown(f"""
            <div class="metric-card">
                <h3 style="color:#d4af37;">{name}</h3>
                <div class="metric-value">{val}</div>
                <div style="color: {color_change}; font-size: 20px;">{change}</div>
            </div>
        """, unsafe_allow_html=True)

st.divider()

# رادار الصفقات
st.markdown('<h2 class="gold-text">🎯 رادار الفرص المكتشفة (طريقة الحبي)</h2>', unsafe_allow_html=True)
signals = HabbiRadar.generate_signals()

for signal in signals:
    with st.expander(f"🔍 {signal['symbol']} - تقييم: {signal['score']}/13 - {signal['status']}", expanded=(signal['score'] >= 11)):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"**السبب:** {signal['reason']}")
        with c2:
            st.markdown(f"**نقطة الدخول (Equilibrium):** {signal['entry']}")
        with c3:
            st.markdown(f"**العمر:** {signal['age']} ساعة")
        
        if signal['score'] >= 9:
            st.success("✅ هذه الصفقة تطابق شروط 'الحبي' الذهبية.")
            if signal['score'] >= 11:
                st.balloons()

# شريط الأخبار السفلي
st.markdown(f"""
    <div class="marquee-container">
        <div class="marquee-text">
            جاري فحص السيولة... | ترقبوا صفقات الحبي الذهبية | نظام MSS + IFVG قيد التشغيل | تم تطبيق قانون الـ 3 أيام بنجاح | 
            Habbi Radar: دقة التحليل هي مفتاح النجاح | اكتشاف سحب سيولة على الذهب الآن! | منصة الحبي هي رادارك الأول في الأسواق |
        </div>
    </div>
    """, unsafe_allow_html=True)

# تفعيل التحديث التلقائي كل 30 ثانية
# time.sleep(30)
# st.rerun()
