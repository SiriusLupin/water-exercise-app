import streamlit as st
import pandas as pd
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from io import StringIO

# ----------------------
# Google Sheets API 初始化
# ----------------------
def init_google_sheet(sheet_name):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        gcp_secrets = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(gcp_secrets, scope)
        client = gspread.authorize(creds)
        sheet = client.open(sheet_name).sheet1
        return sheet, True, ""
    except Exception as e:
        return None, False, str(e)

# ----------------------
# 寫入紀錄到 Google Sheet
# ----------------------
def write_to_sheet(sheet, data):
    try:
        sheet.append_row(data)
        return True
    except Exception as e:
        return False

# ----------------------
# 產出行事曆 CSV（每日一筆）
# ----------------------
def create_calendar_csv(date_list):
    rows = []
    for day in date_list:
        row = {
            "Subject": "水中運動訓練",
            "Start Date": day.strftime("%Y/%m/%d"),
            "Start Time": "08:00 PM",
            "End Date": day.strftime("%Y/%m/%d"),
            "End Time": "09:00 PM",
            "Description": "水中阻力訓練與有氧強化",
            "Location": "水池",
            "All Day Event": "False",
            "Private": "True"
        }
        rows.append(row)
    return pd.DataFrame(rows)

# ----------------------
# App 開始
# ----------------------
st.set_page_config(page_title="水中運動行程管理", layout="wide")

# 分頁選單
tab1, tab2 = st.tabs(["主功能", "狀態檢查"])

# ----------------------
# Tab 1 - 主功能
# ----------------------
with tab1:
    st.title("🏊‍♀️ 水中運動行程設計")

    # 使用預設 training_schedule.csv
    df = pd.read_csv("training_schedule.csv")

    # 起始日期 + 可選擇星期
    start_date = st.date_input("📅 起始運動日", datetime.date.today())
    weekday_options = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
    selected_days = st.multiselect("請選擇執行日 (可多選)", weekday_options)
  
    if not selected_days:
    st.warning("⚠️ 請至少選擇一個執行日（星期）")
    st.stop()

    weekday_map = {"週一": 0, "週二": 1, "週三": 2, "週四": 3, "週五": 4, "週六": 5, "週日": 6}

    # 依據選擇的星期與起始日，建立對應的日期清單
    date_plan = []
    for week in range(df["週次"].nunique()):
        for i, day_label in enumerate(selected_days):
            weekday_num = weekday_map[day_label]
            offset = (7 * week) + ((weekday_num - start_date.weekday()) % 7)
            date = start_date + datetime.timedelta(days=offset)
            date_plan.append({"週次": f"第{week+1}週", "次數": i+1, "日期": date, "星期": day_label})

    date_plan_df = pd.DataFrame(date_plan)

    # 驗證：是否 schedule.csv 次數 < 勾選星期數
    max_times = df.groupby("週次")["次數"].nunique().max()
    if len(selected_days) > max_times:
        st.warning("⚠️ schedule.csv 中的訓練次數少於你選擇的每週訓練日數！")

   
    # 建立完整行程表資料
    merged_df = pd.merge(date_plan_df, df, on=["週次", "次數"], how="left")
    schedule_df = merged_df.dropna()

    # 匯出 Google Calendar CSV
    csv_buffer = StringIO()
    calendar_csv = create_calendar_csv(schedule_df["日期"].tolist())
    calendar_csv.to_csv(csv_buffer, index=False)
    st.download_button("📅 下載 Google 行事曆 CSV", data=csv_buffer.getvalue(), file_name="calendar.csv", mime="text/csv")

    # 顯示訓練行程與打勾記錄
    st.header("詳細訓練行程")
    sheet, sheet_ready, sheet_error = init_google_sheet("水中運動行程表")
    for i, row in schedule_df.iterrows():
        with st.expander(f"{row['日期'].strftime('%Y-%m-%d')} - {row['訓練項目']} 「{row['時間']}」"):
            st.markdown(f"**週次**：{row['週次']}\n\n**操作說明**：{row['操作說明']}")
            unique_key = f"check_{row['日期']}_{row['訓練項目']}_{row['時間']}_{i}".replace(" ", "").replace(":", "")
            if st.checkbox("✅ 已完成", key=unique_key) and sheet_ready:
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                success = write_to_sheet(sheet, [
                    row["日期"].strftime("%Y-%m-%d"), row["訓練項目"], row["週次"], row["星期"], row["時間"],
                    now, "已完成", row["操作說明"], ""
                ])
                if success:
                    st.success("✅ 已記錄到 Google Sheet")
                else:
                    st.warning("⚠️ 無法寫入 Google Sheet")

# ----------------------
# Tab 2 - 狀態檢查
# ----------------------
with tab2:
    st.title("🔍 系統狀態檢查")

    st.subheader("🔑 Google Sheets API 初始化")
    if sheet_ready:
        st.success("✅ 成功連線 Google Sheets 並取得工作表")
    else:
        st.error(f"❌ Google Sheets 初始化失敗：{sheet_error}")

    st.subheader("🔎 secrets 設定檢查")
    if "gcp_service_account" not in st.secrets:
        st.error("❌ st.secrets 中找不到 gcp_service_account")
    else:
        st.success("✅ 成功載入 gcp_service_account")
        st.code(st.secrets["gcp_service_account"].get("client_email", "未找到 Email"))
