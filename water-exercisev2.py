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
# 寫入紀錄到 Google Sheet
# ----------------------
def write_to_sheet(sheet, data):
    try:
        sheet.append_row(data)
        return True
    except Exception as e:
        return False

# ----------------------
# 產出行事曆 CSV（每週一、二，各一筆，固定時間）
# ----------------------
def create_calendar_csv(start_date):
    rows = []
    for i in range(4):  # 四週
        for j in range(2):  # 週一與週二
            day = start_date + datetime.timedelta(days=i*7 + j)
            row = {
                "Subject": "水中運動訓練",
                "Start Date": day.strftime("%Y/%m/%d"),
                "Start Time": "06:30 PM",
                "End Date": day.strftime("%Y/%m/%d"),
                "End Time": "07:30 PM",
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

    # 產生完整行程表資料（週一與週二）
    full_schedule = []
    for i in range(4):
        for j, day_label in enumerate(["週一", "週二"]):
            day_date = start_date + datetime.timedelta(days=i*7 + j)
            day_plan = df[df["星期"] == day_label].copy()
            day_plan["日期"] = day_date.strftime("%Y-%m-%d")
            day_plan["週次"] = f"第{i+1}週"
            day_plan["星期"] = day_label
            full_schedule.append(day_plan)
    schedule_df = pd.concat(full_schedule)

    # 匯出 Google Calendar CSV（新版邏輯）
    csv_buffer = StringIO()
    calendar_csv = create_calendar_csv(start_date)
    calendar_csv.to_csv(csv_buffer, index=False)
    st.download_button("📅 下載 Google 行事曆 CSV", data=csv_buffer.getvalue(), file_name="calendar.csv", mime="text/csv")

    # 顯示行程與勾選記錄
    st.header("詳細訓練行程")
    sheet, sheet_ready, sheet_error = init_google_sheet("水中運動行程表")
    for i, row in schedule_df.iterrows():
        with st.expander(f"{row['日期']} - {row['訓練項目']} 「{row['時間']}」"):
            st.markdown(f"**週次**：{row['週次']}\n\n**操作說明**：{row['操作說明']}")
            unique_key = f"check_{row['日期']}_{row['訓練項目']}_{row['時間']}_{i}".replace(" ", "").replace(":", "")
            if st.checkbox("✅ 已完成", key=unique_key) and sheet_ready:
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                success = write_to_sheet(sheet, [
                    row["日期"], row["訓練項目"], row["週次"], row["星期"], row["時間"],
                    now, "已完成", row["操作說明"], ""
                ])
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
