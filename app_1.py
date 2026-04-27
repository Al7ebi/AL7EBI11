import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import engine as E

# 1. إعدادات الصفحة والسمات (Themes)
st.set_page_config(page_title="منصة الحبي الذكية", page_icon="🔶", layout="wide", initial_sidebar_state="collapsed")

# الألوان الثابتة (الذهبي والداكن)
BG="#0A0E14"; CARD="#121821"; BRD="#1E293B"; TXT="#E2E8F5"; BL="#D4AF37"; GR="#10B981"; RD="#EF4444"; AM="#F59E0B"

# 2. إدارة حالة الجلسة (Session State) لضمان عدم فقدان البيانات
_DEFAULTS = {
    "main_tab": "الرئيسية",
    "radar_df": None,
    "radar_ts": None,
    "market_tab": "US"
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state: st.session_state[k] = v

# 3. تحسين المظهر (CSS) لدمج التبويبات والبطاقات
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;800&display=swap');
html, body, [class*="css"] {{background:{BG}!important; font-family:'Tajawal',sans-serif!important; color:{TXT}!important; direction:rtl!important;}}
.stButton>button {{border-radius:8px!important; font-family:'Tajawal'!important; transition:0.3s;}}
.trade-card {{background:{CARD}; border:1px solid {BRD}; border-radius:14px; padding:16px; margin-bottom:12px; transition:0.3s;}}
.trade-card:hover {{transform:translateY(-3px); border-color:{BL};}}
.long {{border-right:5px solid {GR};}}
.short {{border-right:5px solid {RD};}}
.wait {{border-right:5px solid {AM};}}
.closed {{border-right:5px solid #444; opacity:0.6;}}
.tab-header {{background:{CARD}; padding:15px; border-bottom:2px solid {BL}; display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;}}
</style>
""", unsafe_allow_html=True)

# 4. وظائف المحرك (Engine Helpers)
def _row(t, s):
    try:
        r = E.run_engine(t, s)
        return E.extract_row(r[0], t, s)
    except:
        return E.extract_row(None, t, s)

def do_scan(watchlist):
    total = len(watchlist); res = []
    pb = st.progress(0, text="جارٍ فحص وتحليل السوق...")
    with ThreadPoolExecutor(max_workers=5) as pool:
        futs = {pool.submit(_row, p[0], p[1]): p for p in watchlist}
        for i, f in enumerate(as_completed(futs)):
            r = f.result()
            res.append(r)
            pb.progress((i + 1) / total)
    pb.empty()
    df = pd.DataFrame(res).sort_values(by=["_grade_rank"], ascending=True).reset_index(drop=True)
    st.session_state.radar_df = df
    st.session_state.radar_ts = datetime.now()
    st.success(f"✅ تم تحديث بيانات {len(df)} سهم بنجاح")

# 5. الهيدر العلوي
st.markdown(f"""
<div class="tab-header">
    <div style="display:flex; gap:15px; align-items:center;">
        <div style="width:45px; height:45px; background:{BL}; border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:20px; font-weight:900; color:#000;">ح</div>
        <div>
            <div style="font-size:18px; font-weight:800;">منصة الحبي للتداول الذكي</div>
            <div style="font-size:12px; color:{BL};">Habbi Golden Setup | النسخة الاحترافية</div>
        </div>
    </div>
    <div style="text-align:left;">
        <div style="font-size:16px; font-weight:700; color:{BL};">{datetime.now().strftime("%I:%M %p")}</div>
        <div style="font-size:10px; opacity:0.6;">توقيت النظام</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 6. شريط التبويبات (Navigation)
t_cols = st.columns(4)
menu = ["الرئيسية", "الأوبشن", "الخطة", "المصفوفة"]
for i, m in enumerate(menu):
    with t_cols[i]:
        if st.button(m, use_container_width=True, type="primary" if st.session_state.main_tab == m else "secondary"):
            st.session_state.main_tab = m
            st.rerun()

# تجهيز القوائم
SA_WATCHLIST = [("2222","2222"), ("1120","2222"), ("2010","2222")]
US_WATCHLIST = [(t,"QQQ") for t in ["MSFT","GOOGL","TSLA","AAPL","NVDA","META"]]
watchlist = US_WATCHLIST # يمكنك إضافة زر تبديل بين السوقين هنا

# 7. محتوى التبويبات
st.markdown('<div style="padding:0 20px;">', unsafe_allow_html=True)

if st.session_state.main_tab == "الرئيسية":
    col_a, col_b = st.columns([5, 1])
    with col_b:
        if st.button("📡 بدء المسح", type="primary", use_container_width=True):
            do_scan(watchlist)
    
    df = st.session_state.radar_df
    if df is not None:
        for _, r in df.iterrows():
            grd = r.get("Grade", "?")
            bias = r.get("Bias", "Long")
            # تحديد الكلاس بناءً على القوة والاتجاه
            if grd in ["A+", "A"]: cls = "long" if bias == "Long" else "short"
            elif grd == "B": cls = "wait"
            else: cls = "closed"
            
            st.markdown(f"""
            <div class="trade-card {cls}">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="font-size:18px;"><b>{r.get('Ticker')}</b> <span style="font-size:12px; opacity:0.7;">({grd})</span></div>
                    <div style="color:{GR if bias=='Long' else RD}; font-weight:bold;">{'شراء 🟢' if bias=='Long' else 'بيع 🔴'}</div>
                    <div style="font-size:14px; background:{BG}; padding:5px 15px; border-radius:20px; border:1px solid {BRD};">
                        الدخول: <b>{r.get('Entry','—')}</b> ⮕ الهدف: <b>{r.get('TP1','—')}</b>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("الرادار جاهز.. اضغط على 'بدء المسح' لتحليل الأسهم.")

elif st.session_state.main_tab == "الأوبشن":
    st.subheader("🎯 توصيات الأوبشن الذكية")
    df = st.session_state.radar_df
    if df is not None:
        # تصفية الأسهم القوية فقط للأوبشن
        opt_df = df[df["Grade"].isin(["A+", "A", "B"])]
        if opt_df.empty: st.warning("لا توجد فرص أوبشن حالياً.")
        for _, r in opt_df.iterrows():
            is_call = r.get("Bias") == "Long"
            color = GR if is_call else RD
            st.markdown(f"""
            <div style="background:{CARD}; border-right:5px solid {color}; padding:15px; border-radius:10px; margin-bottom:10px; display:flex; justify-content:space-between;">
                <div><b>{r.get('Ticker')}</b> - عقد <b>{'CALL' if is_call else 'PUT'}</b></div>
                <div>الهدف الفني: {r.get('TP1')}</div>
                <div style="color:{color};">قوة الإشارة: {r.get('Grade')}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("يرجى إجراء مسح الرادار من تبويب الرئيسية أولاً.")

elif st.session_state.main_tab == "الخطة":
    st.subheader("📋 خطة التداول اليومية")
    df = st.session_state.radar_df
    if df is not None:
        filt = st.radio("حالة الصفقة", ["الكل", "نشط (A/A+)", "منتظر (B)"], horizontal=True)
        temp_df = df.copy()
        if "نشط" in filt: temp_df = df[df["Grade"].isin(["A+", "A"])]
        elif "منتظر" in filt: temp_df = df[df["Grade"] == "B"]
        
        st.table(temp_df[["Ticker", "Grade", "Bias", "Entry", "SL", "TP1"]])
    else:
        st.error("لا توجد بيانات خطة معروضة.")

elif st.session_state.main_tab == "المصفوفة":
    st.subheader("📊 مصفوفة القوة النسبية")
    df = st.session_state.radar_df
    if df is not None:
        matrix_data = []
        for _, r in df.head(15).iterrows():
            matrix_data.append({
                "الأصل": r.get("Ticker"),
                "التقييم": "⭐⭐⭐" if r.get("Grade") in ["A+", "A"] else "⭐⭐",
                "الاتجاه": "صاعد 📈" if r.get("Bias") == "Long" else "هابط 📉",
                "السعر المستهدف": r.get("TP1"),
                "المخاطرة": "منخفضة" if r.get("Grade") == "A+" else "متوسطة"
            })
        st.dataframe(pd.DataFrame(matrix_data), use_container_width=True)
    else:
        st.warning("المصفوفة فارغة، بانتظار بيانات المسح.")

st.markdown('</div>', unsafe_allow_html=True)
