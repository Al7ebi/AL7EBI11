import streamlit as st
import pandas as pd
from datetime import datetime
import random

st.set_page_config(page_title="منصة الحبي للتداول", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
html, body, [class*="css"] {
    direction: rtl;
    text-align: right;
    font-family: 'Noto Kufi Arabic', sans-serif;
}
html {
    font-size: 19px;
}
.stApp {
    background: #0d1117;
    color: #e5e7eb;
}
.iconbtn {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    background: #1e2536;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #9ca3af;
    font-size: 20px;
}
.brand {
    font-size: 1.7rem;
    font-weight: 800;
    color: #fff;
    line-height: 1.2;
}
.subtitle {
    color: #6b7280;
    font-size: 0.95rem;
    margin-top: .1rem;
}
.tabsline {
    display: flex;
    gap: 2rem;
    align-items: center;
    justify-content: flex-end;
    padding: 0.9rem 1rem 0 1rem;
    border-bottom: 1px solid #223044;
}
.tab {
    color: #6b7280;
    font-weight: 700;
    font-size: 1rem;
    padding-bottom: .8rem;
}
.tab.active {
    color: #3b82f6;
    border-bottom: 3px solid #3b82f6;
}
.statusbar {
    margin-top: .8rem;
    padding: .85rem 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #161b26;
    border: 1px solid #263043;
    border-radius: 18px;
}
.dot {
    width: 14px;
    height: 14px;
    border-radius: 999px;
    background: #ef4444;
    display: inline-block;
    margin-left: .5rem;
}
.redtxt {
    color: #f87171;
    font-weight: 800;
}
.stTextInput > div > div > input,
.stSelectbox > div > div > div {
    background: #1e2536 !important;
    color: #e5e7eb !important;
    border: 1px solid #334155 !important;
    border-radius: 14px !important;
    padding: .9rem 1rem !important;
}
.metriccard {
    background: #161b26;
    border: 1px solid #263043;
    border-radius: 18px;
    padding: 1.2rem;
    min-height: 120px;
}
.metriclabel {
    color: #6b7280;
    font-size: 1rem;
}
.metricvalue {
    font-size: 2.2rem;
    font-weight: 800;
    margin-top: .2rem;
}
.gapbox {
    height: 250px;
}
.empty-box {
    min-height: 260px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: #6b7280;
    background: #161b26;
    border: 1px solid #263043;
    border-radius: 18px;
}
.footerbar {
    margin-top: 1rem;
    padding: .8rem 1rem;
    color: #6b7280;
    font-size: .9rem;
    text-align: center;
    background: #161b26;
    border: 1px solid #263043;
    border-radius: 18px;
}
</style>
""", unsafe_allow_html=True)

for k, v in [
    ("market", "saudi"),
    ("sort_by", "strength"),
    ("filter_strength", "all"),
    ("view_mode", "grid"),
    ("update_seconds", 300),
]:
    st.session_state.setdefault(k, v)

saudi = [
    {"symbol": "2222", "name": "أرامكو", "status": "active", "strength": 3, "entry": 28.5, "current": 29.1, "stop": 27.8, "t1": 29.5, "t2": 30.2, "t3": 31.0, "date": "2025-01-15"},
    {"symbol": "1120", "name": "الراجحي", "status": "active", "strength": 3, "entry": 95.0, "current": 96.2, "stop": 93.5, "t1": 97.0, "t2": 99.0, "t3": 102.0, "date": "2025-01-14"},
    {"symbol": "2010", "name": "سابك", "status": "waiting", "strength": 2, "entry": 78.0, "current": 77.4, "stop": 76.5, "t1": 80.0, "t2": 82.0, "t3": 85.0, "date": "2025-01-13"},
    {"symbol": "7010", "name": "STC", "status": "active", "strength": 2, "entry": 42.0, "current": 43.1, "stop": 41.0, "t1": 43.5, "t2": 45.0, "t3": 47.0, "date": "2025-01-12"},
    {"symbol": "4200", "name": "الدواء", "status": "waiting", "strength": 1, "entry": 55.0, "current": 54.2, "stop": 53.8, "t1": 57.0, "t2": 59.0, "t3": 62.0, "date": "2025-01-10"},
    {"symbol": "1180", "name": "الأهلي", "status": "closed", "strength": 2, "entry": 38.0, "current": 39.5, "stop": 37.0, "t1": 39.5, "t2": 41.0, "t3": 43.0, "date": "2025-01-09"},
]

us = [
    {"symbol": "AAPL", "name": "Apple", "status": "active", "strength": 3, "entry": 192.0, "current": 196.5, "stop": 188.0, "t1": 198.0, "t2": 205.0, "t3": 212.0, "date": "2025-01-15"},
    {"symbol": "MSFT", "name": "Microsoft", "status": "active", "strength": 3, "entry": 415.0, "current": 422.0, "stop": 408.0, "t1": 425.0, "t2": 435.0, "t3": 450.0, "date": "2025-01-14"},
    {"symbol": "TSLA", "name": "Tesla", "status": "waiting", "strength": 2, "entry": 250.0, "current": 247.0, "stop": 242.0, "t1": 260.0, "t2": 275.0, "t3": 290.0, "date": "2025-01-13"},
    {"symbol": "NVDA", "name": "Nvidia", "status": "active", "strength": 3, "entry": 880.0, "current": 910.0, "stop": 860.0, "t1": 920.0, "t2": 960.0, "t3": 1000.0, "date": "2025-01-12"},
    {"symbol": "AMZN", "name": "Amazon", "status": "closed", "strength": 2, "entry": 178.0, "current": 185.0, "stop": 174.0, "t1": 185.0, "t2": 192.0, "t3": 200.0, "date": "2025-01-10"},
]

def trades():
    return saudi if st.session_state.market == "saudi" else us

def progress(t):
    if t["status"] == "waiting":
        return 0
    rng = t["t1"] - t["entry"]
    if rng == 0:
        return 0
    return max(0, min(100, ((t["current"] - t["entry"]) / rng) * 100))

def pnl(t):
    d = t["current"] - t["entry"]
    return d, (d / t["entry"]) * 100

def stars(n):
    return "⭐" * n + '<span style="color:#374151">' + "☆" * (3 - n) + "</span>"

def apply_filters(df):
    q = st.session_state.get("search", "").lower().strip()
    if q:
        df = df[df["symbol"].str.lower().str.contains(q) | df["name"].str.lower().str.contains(q)]
    fs = st.session_state.filter_strength
    if fs != "all":
        df = df[df["strength"] == int(fs)]
    s = st.session_state.sort_by
    if s == "strength":
        df = df.sort_values(["strength", "date"], ascending=[False, False])
    elif s == "progress":
        df = df.assign(prog=df.apply(lambda r: progress(r.to_dict()), axis=1))
        df = df.sort_values(["prog", "date"], ascending=[False, False]).drop(columns=["prog"])
    else:
        df = df.sort_values("name")
    return df

if st.session_state.update_seconds <= 0:
    st.session_state.update_seconds = 300
    for t in trades():
        if t["status"] != "closed":
            t["current"] = round(t["current"] + (random.random() - 0.45) * t["current"] * 0.003, 2)
else:
    st.session_state.update_seconds -= 1

c0, c1 = st.columns([1, 10], vertical_alignment="center")
with c0:
    st.markdown('<div class="iconbtn">🔔</div>', unsafe_allow_html=True)
with c1:
    a, b, c = st.columns([4, 5, 1])
    with a:
        st.markdown('<div class="brand">منصة الحبي للتداول</div><div class="subtitle">تداول ذكي • تحليل متقدم</div>', unsafe_allow_html=True)
    with b:
        st.markdown(f'<div style="text-align:left;font-size:1.05rem;color:#9ca3af;padding-top:.6rem;">{datetime.now().strftime("%H:%M:%S")}</div>', unsafe_allow_html=True)
    with c:
        st.markdown('<div class="iconbtn" style="background:#2b82f6;color:white;font-size:1.2rem;font-weight:800;">ح</div>', unsafe_allow_html=True)

st.markdown('<div class="tabsline"><div class="tab">السوق الأمريكي us</div><div class="tab active">السوق السعودي sa</div></div>', unsafe_allow_html=True)
st.markdown(f'<div class="statusbar"><div><span class="dot"></span><span class="redtxt">السوق مغلق - يفتح بعد 6س 40د</span> <span style="color:#6b7280;margin-right:1rem;">{datetime.now().strftime("%H:%M:%S")}</span></div><div style="color:#6b7280;">آخر تحديث: --:-- | التحديث كل 5 دقائق</div></div>', unsafe_allow_html=True)

st.write("")
q1, q2, q3, q4 = st.columns([3, 2.2, 2.2, 4.6])
with q4:
    st.text_input("", placeholder="ابحث بالرمز أو الاسم...", key="search", label_visibility="collapsed")
with q3:
    st.session_state.sort_by = st.selectbox("", ["strength", "progress", "name"], format_func=lambda x: {"strength": "ترتيب بالقوة", "progress": "ترتيب بالتقدم", "name": "ترتيب أبجدي"}[x], label_visibility="collapsed")
with q2:
    st.session_state.filter_strength = st.selectbox("", ["all", 3, 2, 1], format_func=lambda x: "جميع القوة" if x == "all" else f"قوة {x}", label_visibility="collapsed")
with q1:
    st.session_state.view_mode = st.selectbox("", ["grid", "table"], format_func=lambda x: "عرض البطاقات" if x == "grid" else "عرض الجدول", label_visibility="collapsed")

st.write("")
raw = pd.DataFrame(trades())
filtered = apply_filters(raw.copy())

m1, m2, m3, m4 = st.columns(4)
for c, label, val, color in [
    (m4, "إجمالي الصفقات", len(filtered), "#ffffff"),
    (m3, "صفقات نشطة", int((filtered["status"] == "active").sum()) if len(filtered) else 0, "#4ade80"),
    (m2, "صفقات منتظرة", int((filtered["status"] == "waiting").sum()) if len(filtered) else 0, "#facc15"),
    (m1, "صفقات مغلقة", int((filtered["status"] == "closed").sum()) if len(filtered) else 0, "#9ca3af"),
]:
    c.markdown(f'<div class="metriccard"><div class="metriclabel">{label}</div><div class="metricvalue" style="color:{color}">{val}</div></div>', unsafe_allow_html=True)

st.write("")
if len(filtered) == 0:
    st.markdown('<div class="empty-box"><div style="font-size:4rem;line-height:1;">🗃️</div><div style="margin-top:1rem;font-size:1.15rem;">لا توجد صفقات مطابقة للبحث</div></div>', unsafe_allow_html=True)
else:
    if st.session_state.view_mode == "table":
        rows = []
        for _, r in filtered.iterrows():
            _, p = pnl(r.to_dict())
            rows.append([
                r["symbol"], r["name"], r["date"],
                "نشط" if r["status"] == "active" else "منتظر" if r["status"] == "waiting" else "مغلق",
                "⭐" * int(r["strength"]), f'{r["entry"]:.2f}', f'{r["current"]:.2f}',
                f'{p:+.2f}%', f'{r["stop"]:.2f}', f'{r["t1"]:.2f}', f'{r["t2"]:.2f}', f'{r["t3"]:.2f}'
            ])
        st.dataframe(pd.DataFrame(rows, columns=["الرمز", "الاسم", "التاريخ", "الحالة", "القوة", "الدخول", "الحالي", "ربح/خسارة", "وقف", "هدف1", "هدف2", "هدف3"]), use_container_width=True, hide_index=True)
    else:
        cols = st.columns(3)
        for i, (_, r) in enumerate(filtered.iterrows()):
            t = r.to_dict()
            _, p = pnl(t)
            with cols[i % 3]:
                st.markdown(f"""
<div style="background:#161b26;border:1px solid #263043;border-radius:18px;padding:1rem;min-height:220px;">
<div style="display:flex;justify-content:space-between;align-items:center;">
<div><div style="font-size:1.15rem;font-weight:800;color:#fff;">{t['symbol']}</div><div style="color:#94a3b8;">{t['name']}</div></div>
<div style="text-align:left;color:#94a3b8;">{t['date']}<br>{stars(int(t['strength']))}</div>
</div>
<div style="margin-top:.8rem;font-weight:700;color:{'#4ade80' if t['status']=='active' else '#facc15' if t['status']=='waiting' else '#9ca3af'};">
{'نشط' if t['status']=='active' else 'منتظر' if t['status']=='waiting' else 'مغلق'}
</div>
<div style="margin-top:.7rem;color:#9ca3af;">نقطة الدخول: <b style="color:#fff">{t['entry']:.2f}</b></div>
<div style="color:#9ca3af;">السعر الحالي: <b style="color:#fff">{t['current']:.2f}</b></div>
<div style="margin-top:.5rem;color:{'#4ade80' if p>=0 else '#f87171'};font-weight:800;">الربح/الخسارة: {p:+.2f}%</div>
<div style="margin-top:.7rem;height:8px;background:#0d1117;border-radius:999px;overflow:hidden;"><div style="height:8px;width:{progress(t)}%;background:linear-gradient(90deg,#22c55e,#3b82f6);border-radius:999px;"></div></div>
</div>
""", unsafe_allow_html=True)

st.write("")
st.markdown('<div class="gapbox"></div>', unsafe_allow_html=True)
st.markdown('<div class="footerbar">جميع الحقوق محفوظة © 2025 منصة الحبي للتداول. هذه المنصة لأغراض تعليمية فقط ولا تتحمل أي التزامات مالية.</div>', unsafe_allow_html=True)
