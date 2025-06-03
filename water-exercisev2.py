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
        gcp_secrets = dict(st.secrets["gcp_service_account"])  # 從 secrets.toml 讀入
        creds = ServiceAccountCredentials.from_json_keyfile_dict(gcp_secrets, scope)
        client = gspread.authorize(creds)
        sheet = client.open(sheet_name).sheet1
        return sheet, True, ""
    except Exception as e:
        return None, False, str(e)

# ----------------------
# 寫入紀錄到 Google Sheet（寫入完整欄位）
# ----------------------
def write_to_sheet(sheet, row_data, finish_time):
    try:
        record = [
            row_data["日期"],
            row_data["運動項目"],
            row_data["週次"],
            row_data["星期"],
            row_data["時間"],
            finish_time,
            "已完成",
            row_data["詳細說明"],
            ""
        ]
        sheet.append_row(record)
        return True
    except Exception as e:
        return False

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

    # 使用者提供行程資料或從本機讀取預設檔案
    use_default = st.checkbox("使用預設運動行程（training_schedule.csv）", value=True)
    if use_default:
        df = pd.read_csv("training_schedule.csv")
    else:
        uploaded = st.file_uploader("請上傳 CSV 行程檔", type=["csv"])
        if uploaded:
            df = pd.read_csv(uploaded)
        else:
            st.stop()

    # 選擇起始日期
    start_date = st.date_input("📅 請輸入起始運動日 (週一)", datetime.date.today())

    # 產生行程資料表
    full_schedule = []
    for i in range(4):
        for j, day_label in enumerate(["週一", "週二"]):
            day_date = start_date + datetime.timedelta(days=i*7 + j)
            day_plan = df[df["星期"] == day_label].copy()
            day_plan["日期"] = day_date.strftime("%Y-%m-%d")
            day_plan["週次"] = f"第{i+1}週"
            full_schedule.append(day_plan)
    schedule_df = pd.concat(full_schedule)

    # 匯出 Google Calendar CSV
    def create_calendar_csv(schedule):
        gcal = schedule.copy()
        gcal["Subject"] = gcal["運動項目"]
        gcal["Start Date"] = gcal["日期"]
        gcal["Start Time"] = "08:00 AM"
        gcal["End Date"] = gcal["日期"]
        gcal["End Time"] = "08:45 AM"
        gcal["Description"] = gcal["詳細說明"]
        gcal["Location"] = "水池"
        gcal["All Day Event"] = "False"
        gcal["Private"] = "True"
        return gcal[["Subject", "Start Date", "Start Time", "End Date", "End Time", "Description", "Location", "All Day Event", "Private"]]

    csv_buffer = StringIO()
    calendar_csv = create_calendar_csv(schedule_df)
    calendar_csv.to_csv(csv_buffer, index=False)
    st.download_button("📅 下載 Google 行事曆 CSV", data=csv_buffer.getvalue(), file_name="calendar.csv", mime="text/csv")

    # 顯示行程與勾選記錄
    st.header("詳細運動行程")
    sheet, sheet_ready, sheet_error = init_google_sheet("水中運動行程表")
    for i, row in schedule_df.iterrows():
        with st.expander(f"{row['日期']} - {row['運動項目']} 「{row['時間']}」"):
            st.markdown(f"**週次**：{row['週次']}\n\n**說明**：{row['詳細說明']}")
            if st.checkbox("✅ 已完成", key=f"check_{i}") and sheet_ready:
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                success = write_to_sheet(sheet, row, now)
                if success:
                    st.success("已記錄到 Google Sheet")
                else:
                    st.warning("無法寫入 Google Sheet")

# ----------------------
# Tab 2 - 狀態檢查
# ----------------------
with tab2:
    st.title("🔍 連線狀態檢查")
    st.subheader("Google Sheets 連線")
    if sheet_ready:
        st.success("已成功連接 Google Sheet")
    else:
        st.error("連線失敗")
        st.code(sheet_error)

    st.subheader("secrets 讀取")
    try:
        st.json(st.secrets["gcp_service_account"])
    except:
        st.error("無法讀取 secrets")
