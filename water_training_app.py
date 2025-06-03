import streamlit as st
import pandas as pd

st.set_page_config(page_title="水中運動訓練進度表", layout="wide")

st.title("🏊‍♀️ 水中運動訓練進度追蹤")

# 讀取訓練進度表
@st.cache_data
def load_data():
    return pd.read_csv("training_schedule.csv")

df = load_data()

# 選擇週次與星期
col1, col2 = st.columns(2)
with col1:
    selected_week = st.selectbox("📅 請選擇週次", df["週次"].unique())
with col2:
    selected_day = st.radio("🗓️ 請選擇星期", ["週一", "週二"])

# 篩選對應資料
filtered = df[(df["週次"] == selected_week) & (df["星期"] == selected_day)]

st.markdown(f"### ✅ {selected_week}・{selected_day} 訓練內容")

# 顯示訓練內容與打勾選項
for i, row in filtered.iterrows():
    with st.expander(f"{row['訓練項目']}　（{row['時間']}）"):
        st.markdown(f"📝 **操作說明：** {row['操作說明']}")
        st.checkbox("✔️ 已完成", key=f"{i}_{row['訓練項目']}")
