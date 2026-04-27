import streamlit as st
import pandas as pd
import random
from datetime import datetime
import math

st.set_page_config(page_title="منصة الحبي للتداول", layout="wide")

st.markdown("""
<style>
html, body, [class*="css"]  {
    direction: rtl;
    text-align: right;
    font-family: 'Noto Kufi Arabic', sans-serif;
}
html {
    font-size: 19px;
}
.big-title {
    font-size: 2rem !important;
    font-weight: 800;
}
.small-muted {
    color: #6b7280;
    font-size: 0.9rem;
}
.card {
    border: 1px solid #2b3445;
    border-radius: 16px;
    padding: 16px;
    background: #161b26;
}
.metric-box {
    border: 1px solid #2b3445;
    border-radius: 16px;
    padding: 14px;
    background: #161b26;
}
.status-active { color: #22c55e; font-weight: 700; }
.status-waiting { color: #facc15; font-weight: 700; }
.status-closed { color: #9ca3af; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

default_theme = "dark"
if "theme" not in st.session_state:
    st.session_state.theme = default_theme
if "market" not in st.session_state:
    st.session_state.market = "saudi"
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "grid"
if "font_scale" not in st.session_state:
    st.session_state.font_scale = 1.15
if "alerts" not in st.session_state:
    st.session_state.alerts = []
if "sound_enabled" not in st.session_state:
    st.session_state.sound_enabled = True

saudi_trades = [
    {"symbol": "2222", "name": "أرامكو", "date": "2025-01-15", "status": "active", "strength": 3, "entry": 28.50, "stopLoss": 27.80, "target1": 29.50, "target2": 30.20, "target3": 31.00, "current": 29.10},
    {"symbol": "1120", "name": "الراجحي", "date": "2025-01-14", "status": "active", "strength": 3, "entry": 95.00, "stopLoss": 93.50, "target1": 97.00, "target2": 99.00, "target3": 102.00, "current": 96.20},
    {"symbol": "2010", "name": "سابك", "date": "2025-01-13", "status": "waiting", "strength": 2, "entry": 78.00, "stopLoss": 76.50, "target1": 80.00, "target2": 82.00, "target3": 85.00, "current": 77.40},
    {"symbol": "7010", "name": "STC", "date": "2025-01-12", "status": "active", "strength": 2, "entry": 42.00, "stopLoss": 41.00, "target1": 43.50, "target2": 45.00, "target3": 47.00, "current": 43.10},
    {"symbol": "4200", "name": "الدواء", "date": "2025-01-10", "status": "waiting", "strength": 1, "entry": 55.00, "stopLoss": 53.80, "target1": 57.00, "target2": 59.00, "target3": 62.00, "current": 54.20},
    {"symbol": "1180", "name": "الأهلي", "date": "2025-01-09", "status": "closed", "strength": 2, "entry": 38.00, "stopLoss": 37.00, "target1": 39.50, "target2": 41.00, "target3": 43.00, "current": 39.50},
]

us_trades = [
    {"symbol": "AAPL", "name": "Apple", "date": "2025-01-15", "status": "active", "strength": 3, "entry": 192.00, "stopLoss": 188.00, "target1": 198.00, "target2": 205.00, "target3": 212.00, "current": 196.50},
    {"symbol": "MSFT", "name": "Microsoft", "date": "2025-01-14", "status": "active", "strength": 3, "entry": 415.00, "stopLoss": 408.00, "target1": 425.00, "target2": 435.00, "target3": 450.00, "current": 422.00},
    {"symbol": "TSLA", "name": "Tesla", "date": "2025-01-13", "status": "waiting", "strength": 2, "entry": 250.00, "stopLoss": 242.00, "target1": 260.00, "target2": 275.00, "target3": 290.00, "current": 247.00},
    {"symbol": "NVDA", "name": "Nvidia", "date": "2025-01-12", "status": "active", "strength": 3, "entry": 880.00, "stopLoss": 860.00, "target1": 920.00, "target2": 960.00, "target3": 1000.00, "current": 910.00},
    {"symbol": "AMZN", "name": "Amazon", "date": "2025-01-10", "status": "closed", "strength": 2, "entry": 178.00, "stopLoss": 174.00, "target1": 185.00, "target2": 192.00, "target3": 200.00, "current": 185.00},
]

def get_trades():
    return saudi_trades if st.session_state.market == "saudi" else us_trades

def get_progress(t):
    if t["status"] == "waiting":
        return 0
    rng = t["target1"] - t["entry"]
    if rng == 0:
        return 0
    return max(0, min(100, ((t["current"] - t["entry"]) / rng) * 100))

def get_pnl(t):
    diff = t["current"] - t["entry"]
    pct = (diff / t["entry"]) * 100
    return diff, pct

def stars(n):
    return "⭐" * n + "☆" * (3 - n)

def status_label(s):
    if s == "active":
        return "نشط"
    if s == "waiting":
        return "منتظر"
    return "مغلق"

def status_class(s):
    return {
        "active": "status-active",
        "waiting": "status-waiting",
        "closed": "status-closed",
    }[s]

def simulate_price_update():
    trades = get_trades()
    for t in trades:
        if t["status"] == "closed":
            continue
        vol = t["current"] * 0.003
        change = (random.random() - 0.45) * vol
        t["current"] = round(t["current"] + change, 2)

def add_alert(msg):
    tm = datetime.now().strftime("%H:%M:%S")
    st.session_state.alerts.insert(0, {"msg": msg, "time": tm})
    st.session_state.alerts = st.session_state.alerts[:20]

top1, top2, top3 = st.columns([3, 2, 2])
with top1:
    st.markdown('<div class="big-title">منصة الحبي للتداول</div>', unsafe_allow_html=True)
    st.caption("تداول ذكي • تحليل متقدم")
with top2:
    st.metric("الوقت الحالي", datetime.now().strftime("%H:%M:%S"))
with top3:
    if st.button("تحديث الآن"):
        simulate_price_update()

st.sidebar.header("الإعدادات")
st.session_state.market = st.sidebar.radio("السوق", ["saudi", "us"], format_func=lambda x: "السوق السعودي" if x == "saudi" else "السوق الأمريكي")
st.session_state.view_mode = st.sidebar.radio("طريقة العرض", ["grid", "table"], format_func=lambda x: "البطاقات" if x == "grid" else "الجدول")
search = st.sidebar.text_input("بحث")
strength_filter = st.sidebar.selectbox("القوة", ["all", 3, 2, 1], format_func=lambda x: "جميع القوة" if x == "all" else f"قوة {x}")
sort_by = st.sidebar.selectbox("الترتيب", ["strength", "progress", "name"], format_func=lambda x: {"strength": "بالقوة", "progress": "بالتقدم", "name": "أبجدي"}[x])
font_option = st.sidebar.selectbox("حجم الخط", ["small", "medium", "large"], format_func=lambda x: {"small": "صغير", "medium": "متوسط", "large": "كبير"}[x])
if font_option == "small":
    st.session_state.font_scale = 0.95
elif font_option == "medium":
    st.session_state.font_scale = 1.15
else:
    st.session_state.font_scale = 1.35

trades = [t.copy() for t in get_trades()]

if search:
    q = search.lower()
    trades = [t for t in trades if q in t["symbol"].lower() or q in t["name"].lower()]
if strength_filter != "all":
    trades = [t for t in trades if t["strength"] == strength_filter]

if sort_by == "strength":
    trades.sort(key=lambda x: x["strength"], reverse=True)
elif sort_by == "progress":
    trades.sort(key=lambda x: get_progress(x), reverse=True)
else:
    trades.sort(key=lambda x: x["name"])

active_count = len([t for t in trades if t["status"] == "active"])
waiting_count = len([t for t in trades if t["status"] == "waiting"])
closed_count = len([t for t in trades if t["status"] == "closed"])

c1, c2, c3, c4 = st.columns(4)
c1.markdown(f'<div class="metric-box"><div class="small-muted">إجمالي الصفقات</div><div style="font-size:2rem;font-weight:800;">{len(trades)}</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="metric-box"><div class="small-muted">صفقات نشطة</div><div style="font-size:2rem;font-weight:800;color:#22c55e;">{active_count}</div></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="metric-box"><div class="small-muted">صفقات منتظرة</div><div style="font-size:2rem;font-weight:800;color:#facc15;">{waiting_count}</div></div>', unsafe_allow_html=True)
c4.markdown(f'<div class="metric-box"><div class="small-muted">صفقات مغلقة</div><div style="font-size:2rem;font-weight:800;color:#9ca3af;">{closed_count}</div></div>', unsafe_allow_html=True)

st.write("")

if st.session_state.view_mode == "table":
    rows = []
    for t in trades:
        diff, pct = get_pnl(t)
        rows.append({
            "الرمز": t["symbol"],
            "الاسم": t["name"],
            "التاريخ": t["date"],
            "الحالة": status_label(t["status"]),
            "القوة": stars(t["strength"]),
            "نقطة الدخول": f'{t["entry"]:.2f}',
            "السعر الحالي": f'{t["current"]:.2f}',
            "الربح/الخسارة %": f'{pct:.2f}%',
            "وقف الخسارة": f'{t["stopLoss"]:.2f}',
            "الهدف 1": f'{t["target1"]:.2f}',
            "الهدف 2": f'{t["target2"]:.2f}',
            "الهدف 3": f'{t["target3"]:.2f}',
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    cols = st.columns(3)
    for i, t in enumerate(trades):
        with cols[i % 3]:
            diff, pct = get_pnl(t)
            prog = get_progress(t)
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(f'### {t["symbol"]} - {t["name"]}')
            st.caption(f'📅 {t["date"]} | {stars(t["strength"])}')
            st.markdown(f'**الحالة:** <span class="{status_class(t["status"])}">{status_label(t["status"])}</span>', unsafe_allow_html=True)
            if t["status"] == "active":
                st.progress(int(prog))
                st.write(f"التقدم نحو الهدف 1: {prog:.0f}%")
                if diff >= 0:
                    st.success(f"السعر الحالي: {t['current']:.2f} | الربح: +{pct:.2f}%")
                else:
                    st.error(f"السعر الحالي: {t['current']:.2f} | الخسارة: {pct:.2f}%")
            st.write(f"نقطة الدخول: {t['entry']:.2f}")
            st.write(f"وقف الخسارة: {t['stopLoss']:.2f}")
            st.write(f"الهدف 1: {t['target1']:.2f}")
            st.write(f"الهدف 2: {t['target2']:.2f}")
            st.write(f"الهدف 3: {t['target3']:.2f}")
            st.markdown('</div>', unsafe_allow_html=True)

st.write("---")
st.subheader("التنبيهات")
if st.session_state.alerts:
    for a in st.session_state.alerts[:5]:
        st.info(f'{a["msg"]} — {a["time"]}')
else:
    st.caption("لا توجد تنبيهات حالياً")

st.caption("جميع الحقوق محفوظة © 2025 منصة الحبي للتداول. هذه المنصة لأغراض تعليمية فقط.")
