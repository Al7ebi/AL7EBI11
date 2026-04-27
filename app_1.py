import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="منصة الحبي للتداول",
    layout="wide",
)

# إعدادات الستايل مع خط كبير
st.markdown("""
    <style>
    html, body, [class*="css"]  {
        font-family: 'Noto Kufi Arabic', sans-serif;
        direction: rtl;
        text-align: right;
        font-size: 20px !important;
    }
    </style>
""", unsafe_allow_html=True)

# عنوان المنصة
st.title("منصة الحبي للتداول 📊")
st.write("تداول ذكي • تحليل متقدم")

# بيانات تجريبية
data = [
    {"الرمز": "2222", "الاسم": "أرامكو", "الحالة": "نشط", "نقطة الدخول": 28.50, "السعر الحالي": 29.10},
    {"الرمز": "1120", "الاسم": "الراجحي", "الحالة": "نشط", "نقطة الدخول": 95.00, "السعر الحالي": 96.20},
    {"الرمز": "2010", "الاسم": "سابك", "الحالة": "منتظر", "نقطة الدخول": 78.00, "السعر الحالي": 77.40},
]

df = pd.DataFrame(data)

# جدول الصفقات
st.subheader("الصفقات الحالية")
st.dataframe(df, use_container_width=True)

# ملخص الأرقام
col1, col2, col3 = st.columns(3)
col1.metric("الصفقات النشطة", df[df["الحالة"] == "نشط"].shape[0])
col2.metric("الصفقات المنتظرة", df[df["الحالة"] == "منتظر"].shape[0])
col3.metric("إجمالي الصفقات", len(df))

# تنبيه بسيط
st.info("هذا النظام لأغراض تعليمية فقط. البيانات المعروضة تجريبية.")

# تذييل
st.markdown("---")
st.markdown("جميع الحقوق محفوظة © 2025 منصة الحبي للتداول – لأغراض تعليمية فقط.")
