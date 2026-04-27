import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import engine as E

# ===== الإعدادات =====
st.set_page_config(page_title="AL7EBI PRO", page_icon="🔶", layout="wide", initial_sidebar_state="collapsed")

# ألوان احترافية
BG = "#0B0F19"
CARD = "#111827"
CARD2 = "#1F2937"
GOLD = "#D4AF37"
GOLD2 = "#F59E0B"
GREEN = "#10B981"
RED = "#EF4444"
TXT = "#E5E7EB"
TXT2 = "#9CA3AF"

# ===== CSS احترافي =====
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@500;700;800&family=IBM+Plex+Mono:wght@500&display=swap');

html, body, [class*="css"] {{
    background: {BG}!important;
    color: {TXT}!important;
    font-family: 'Tajawal', sans-serif!important;
    direction: rtl!important;
}}
.block-container {{padding-top: 1rem!important; max-width: 1400px!important;}}

/* هيدر */
.header {{
    background: linear-gradient(135deg, {CARD} 0%, #0F172A 100%);
    border: 1px solid #1E293B;
    border-radius: 16px;
    padding: 18px 24px;
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}}
.logo {{
    display: flex; align-items: center; gap: 12px;
}}
.logo-icon {{
    width: 44px; height: 44px;
    background: linear-gradient(135deg, {GOLD}, {GOLD2});
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 20px; color: #000;
    box-shadow: 0 0 20px rgba(212,175,55,0.3);
}}

/* بطاقات */
.trade-card {{
    background: {CARD};
    border: 1px solid #1E293B;
    border-radius: 14px;
    padding: 18px;
    margin-bottom: 14px;
    transition: all 0.25s ease;
    position: relative;
    overflow: hidden;
}}
.trade-card::before {{
    content: ''; position: absolute; right: 0; top: 0; bottom: 0; width: 4px;
    background: #374151; transition: width 0.25s;
}}
.trade-card.long::before {{ background: {GREEN}; }}
.trade-card.short::before {{ background: {RED}; }}
.trade-card:hover {{
    transform: translateY(-2px);
    border-color: #334155;
    box-shadow: 0 8px 30px rgba(0,0,0,0.4);
}}
.trade-card:hover::before {{ width: 6px; }}

.card-top {{ display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px; }}
.ticker {{ font-size: 22px; font-weight: 800; letter-spacing: 0.5px; }}
.grade {{
    background: rgba(212,175,55,0.15); color: {GOLD};
    padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 700;
    border: 1px solid rgba(212,175,55,0.3);
}}
.badge {{
    padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 700;
}}
.badge-long {{ background: rgba(16,185,129,0.15); color: {GREEN}; border: 1px solid rgba(16,185,129,0.3); }}
.badge-short {{ background: rgba(239,68,68,0.15); color: {RED}; border: 1px solid rgba(239,68,68,0.3); }}

.levels {{ display: grid; grid-template-columns: repeat(3,1fr); gap: 12px; margin-top: 14px; }}
.level {{ background: {CARD2}; padding: 10px; border-radius: 8px; text-align: center; }}
.level-label {{ font-size: 11px; color: {TXT2}; margin-bottom: 4px; }}
.level-value {{ font-family: 'IBM Plex Mono', monospace; font-weight: 600; font-size: 15px; }}

/* أزرار */
.stButton>button {{
    background: {CARD}!important;
    color: {TXT}!important;
    border: 1px solid #334155!important;
    border-radius: 10px!important;
    padding: 10px 20px!important;
    font-family: 'Tajawal'!important;
    font-weight: 600!important;
    transition: all 0.2s!important;
}}
.stButton>button:hover {{ border-color: {GOLD}!important; background: #1E293B!important; }}
.stButton>button[kind="primary"] {{
    background: linear-gradient(135deg, {GOLD}, {GOLD2})!important;
    color: #000!important; border: none!important; font-weight: 800!important;
}}
</style>
""", unsafe_allow_html=True)

# ===== Session =====
if "radar_df" not in st.session_state: st.session_state.radar_df = None
if "radar_ts" not in st.session_state: st.session_state.radar_ts = None

# ===== دوال المحرك (لم تتغير) =====
@st.cache_data(ttl=300, show_spinner=False)
def _row(ticker, smt):
    try:
        res = E.run_engine(ticker, smt)
        return E.extract_row(res[0], ticker, smt)
    except:
        return E.extract_row(None, ticker, smt)

# ===== هيدر =====
st.markdown(f"""
<div class="header">
    <div class="logo">
        <div class="logo-icon">ح</div>
        <div>
            <div style="font-size:18px;font-weight:800;">AL7EBI ICT PRO</div>
            <div style="font-size:12px;color:{TXT2};">Golden Setup • Smart Money Concepts</div>
        </div>
    <div style="text-align:left;">
        <div style="font-size:13px;color:{TXT2};">آخر تحديث</div>
        <div style="font-family:'IBM Plex Mono';color:{GOLD};font-weight:600;">{datetime.now().strftime('%H:%M:%S')}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ===== التبويبات =====
tab1, tab2, tab3, tab4 = st.tabs(["📊 الرادار", "🎯 الأوبشن", "📋 الخطة", "📈 المصفوفة"])

# قوائم
US_WL = [(t,"QQQ") for t in ["MSFT","GOOGL","TSLA","AAPL","NVDA","META","AMZN","ORCL","ADBE","CRM"]]
SA_WL = [("2222","2222"),("1120","2222"),("2010","2222"),("7010","2222")]

# ===== تبويب 1: الرادار =====
with tab1:
    c1, c2, c3 = st.columns([1,1,3])
    with c1:
        market = st.selectbox("السوق", ["🇺🇸 أمريكي","🇸🇦 سعودي"], label_visibility="collapsed")
    with c2:
        if st.button("📡 مسح الآن", type="primary", use_container_width=True):
            wl = US_WL if "أمريكي" in market else SA_WL
            prog = st.progress(0)
            results = []
            with ThreadPoolExecutor(max_workers=5) as ex:
                futs = {ex.submit(_row, t, s): t for t,s in wl}
                for i,f in enumerate(as_completed(futs)):
                    results.append(f.result())
                    prog.progress((i+1)/len(wl))
            prog.empty()
            st.session_state.radar_df = pd.DataFrame(results)
            st.session_state.radar_ts = datetime.now(timezone.utc)

    df = st.session_state.radar_df
    if df is not None and not df.empty:
        # إحصائيات علوية
        m1,m2,m3,m4 = st.columns(4)
        m1.metric("إجمالي", len(df))
        m2.metric("A+", len(df[df['Grade']=='A+']))
        m3.metric("شراء", len(df[df['Bias']=='Long']))
        m4.metric("بيع", len(df[df['Bias']=='Short']))

        st.markdown("---")

        for _, r in df.iterrows():
            ticker = r.get('Ticker','?')
            grade = r.get('Grade','?')
            bias = r.get('Bias','Long')
            entry = r.get('Entry','—')
            sl = r.get('SL','—')
            tp1 = r.get('TP1','—')

            cls = "long" if bias == "Long" else "short"
            badge_cls = "badge-long" if bias == "Long" else "badge-short"
            badge_txt = "شراء • CALL" if bias == "Long" else "بيع • PUT"

            st.markdown(f"""
            <div class="trade-card {cls}">
                <div class="card-top">
                    <div style="display:flex;align-items:center;gap:10px;">
                        <div class="ticker">{ticker}</div>
                        <div class="grade">{grade}</div>
                    </div>
                    <div class="{badge_cls} badge">{badge_txt}</div>
                </div>
                <div class="levels">
                    <div class="level">
                        <div class="level-label">الدخول</div>
                        <div class="level-value">{entry}</div>
                    </div>
                    <div class="level">
                        <div class="level-label">وقف</div>
                        <div class="level-value" style="color:{RED};">{sl}</div>
                    </div>
                    <div class="level">
                        <div class="level-label">هدف 1</div>
                        <div class="level-value" style="color:{GREEN};">{tp1}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("👆 اختر السوق واضغط 'مسح الآن' لبدء التحليل")

# ===== تبويب 2: الأوبشن =====
with tab2:
    st.markdown("### توصيات الأوبشن المباشرة")
    df = st.session_state.radar_df
    if df is None:
        st.warning("قم بالمسح من تبويب الرادار أولاً")
    else:
        for _, r in df[df['Grade'].isin(['A+','A'])].iterrows():
            is_call = r.get('Bias') == 'Long'
            st.markdown(f"""
            <div style="background:{CARD};border-left:4px solid {'#10B981' if is_call else '#EF4444'};padding:14px;margin:8px 0;border-radius:10px;">
                <b>{r.get('Ticker')}</b> — <span style="color:{'#10B981' if is_call else '#EF4444'};font-weight:700;">{'CALL' if is_call else 'PUT'}</span>
                <span style="float:left;font-family:'IBM Plex Mono';">دخول {r.get('Entry')}</span>
            </div>
            """, unsafe_allow_html=True)

# ===== تبويب 3: الخطة =====
with tab3:
    st.markdown("### خطة التداول")
    df = st.session_state.radar_df
    if df is not None:
        filt = st.segmented_control("الحالة", ["الكل","نشط","منتظر"], default="الكل")
        d = df.copy()
        if filt == "نشط": d = d[d['Grade'].isin(['A+','A'])]
        elif filt == "منتظر": d = d[d['Grade'] == 'B']
        st.dataframe(d[['Ticker','Grade','Bias','Entry','SL','TP1','TP2 (Ext)']],
                    use_container_width=True, hide_index=True, height=400)
    else:
        st.info("لا توجد بيانات")

# ===== تبويب 4: المصفوفة =====
with tab4:
    st.markdown("### مصفوفة القوة النسبية")
    df = st.session_state.radar_df
    if df is not None:
        cols = st.columns(3)
        for i, (_, r) in enumerate(df.head(9).iterrows()):
            with cols[i % 3]:
                score = 95 if r.get('Grade') == 'A+' else 85 if r.get('Grade') == 'A' else 70
                st.markdown(f"""
                <div style="background:{CARD};border:1px solid #1E293B;border-radius:12px;padding:16px;text-align:center;margin-bottom:12px;">
                    <div style="font-size:20px;font-weight:800;margin-bottom:8px;">{r.get('Ticker')}</div>
                    <div style="font-size:28px;font-weight:800;color:{GOLD};margin:8px 0;">{score}</div>
                    <div style="height:4px;background:#1E293B;border-radius:2px;overflow:hidden;">
                        <div style="width:{score}%;height:100%;background:linear-gradient(90deg,{GOLD},{GOLD2});"></div>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("قم بالمسح أولاً")
