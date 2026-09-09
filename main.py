import streamlit as st
import sqlite3
import pandas as pd
import requests
import io
import itertools
from concurrent.futures import ThreadPoolExecutor, as_completed

DB_NAME = "Lotto_Multi.db"

# ----------------------------------------------------
# 1. 資料庫結構初始化 (已升級：單行防斷行安全版)
# ----------------------------------------------------
def init_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 💡 1. 建立樂透型彩券資料表 (採用單行安全格式，防編輯器自動換行錯亂)
    cursor.execute("CREATE TABLE IF NOT EXISTS lotto_649 (period INTEGER PRIMARY KEY, open_date TEXT, num1 INTEGER, num2 INTEGER, num3 INTEGER, num4 INTEGER, num5 INTEGER, num6 INTEGER, sp_num INTEGER)")
    cursor.execute("CREATE TABLE IF NOT EXISTS lotto_539 (period INTEGER PRIMARY KEY, open_date TEXT, num1 INTEGER, num2 INTEGER, num3 INTEGER, num4 INTEGER, num5 INTEGER)")
    cursor.execute("CREATE TABLE IF NOT EXISTS lotto_super (period INTEGER PRIMARY KEY, open_date TEXT, num1 INTEGER, num2 INTEGER, num3 INTEGER, num4 INTEGER, num5 INTEGER, num6 INTEGER, sec_num INTEGER)")

    # 💡 2. 建立3/4星彩位置型資料表
    cursor.execute("CREATE TABLE IF NOT EXISTS lotto_3d (period INTEGER PRIMARY KEY, open_date TEXT, hundreds INTEGER, tens INTEGER, units INTEGER)")
    cursor.execute("CREATE TABLE IF NOT EXISTS lotto_4d (period INTEGER PRIMARY KEY, open_date TEXT, thousands INTEGER, hundreds INTEGER, tens INTEGER, units INTEGER)")

    # 💡 3. 🔐【Sophia 授權核心】建立安全用戶管理資料表
    cursor.execute("CREATE TABLE IF NOT EXISTS auth_users (user_key TEXT PRIMARY KEY, user_name TEXT, expire_date TEXT, role TEXT DEFAULT 'user')")

    # 💡 4. 智慧預載機制：如果權限表目前是空的，自動幫您插入初始系統金鑰
    cursor.execute("SELECT COUNT(*) FROM auth_users")
    if cursor.fetchone()[0] == 0:
        initial_users = [
            ("admin888", "終極管理員", "2030-12-31", "admin"),
            ("vipguan", "親友合夥人", "2030-06-30", "user"),
        ]
        cursor.executemany("INSERT INTO auth_users VALUES (?, ?, ?, ?)", initial_users)

    conn.commit()
    conn.close()

# ----------------------------------------------------
# 2. 高效能多執行緒爬蟲
# 2. 具備防封鎖與政府 OpenData 備用機制的爬蟲模組
# 2. 具備關鍵字參數保護與雙備援機制的爬蟲模組
# ----------------------------------------------------
import ssl
from urllib.request import Request, urlopen
# ----------------------------------------------------
# 2. 瀏覽器層級偽裝 - 台彩官方 CSV 高速同步模組
# ----------------------------------------------------
def _download_and_parse_worker(game_type, primary_url, backup_url=None):
    """
    使用核心 urllib 進行高級瀏覽器指紋偽裝，直接繞過台彩防火牆阻擋
    """
    req = Request(primary_url)
    # 注入完整的標準安全指紋，讓台彩主機誤判定為一般民眾在點擊下載
    req.add_header("User-Agent",
                   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    req.add_header("Accept",
                   "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8")
    req.add_header("Referer", "https://www.taiwanlottery.com/lotto/history/result_download/")
    req.add_header("Accept-Language", "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7")

    # 忽略本機 SSL 安全憑證過期或解析阻礙問題
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with urlopen(req, context=ctx, timeout=10) as response:
            raw_data = response.read()
            # 官方第五屆 CSV 全面採用 CP950 (Big5) 編碼
            csv_data = raw_data.decode('cp950', errors='ignore')

            # 台彩 CSV 第一行為標題說明（例如: 第5屆...各期開獎結果...），所以一定要 skiprows=1
            df = pd.read_csv(io.StringIO(csv_data), skiprows=1)
            df.columns = df.columns.str.strip()
            return game_type, True, df
    except Exception as e:
        return game_type, False, f"台彩數據源下載解析中斷: {str(e)}"


def sync_all_lottery_data_parallel():
    init_database()

    # 【全新更正】配置台灣彩券官方第 5 屆（113年起至今）最新標準 CSV 動態實體下載端點
    urls_config = {
        "大樂透": {
            "primary": "https://taiwanlottery.com"
        },
        "今彩 539": {
            "primary": "https://taiwanlottery.com"
        },
        "威力彩": {
            "primary": "https://taiwanlottery.com"
        },
        "3星彩": {
            "primary": "https://taiwanlottery.com"
        },
        "4星彩": {
            "primary": "https://taiwanlottery.com"
        }
    }

    parsed_results, logs = {}, []

    # 採用安全執行緒限制，避免觸發伺服器 DDoS 安全阻斷機制
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                _download_and_parse_worker,
                game_type=gtype,
                primary_url=cfg["primary"]
            )
            for gtype, cfg in urls_config.items()
        ]
        for future in as_completed(futures):
            gtype, success, result = future.result()
            if success:
                parsed_results[gtype] = result
            else:
                logs.append(f"❌ {gtype} 同步失敗: {result}")

    if not parsed_results:
        return False, "所有彩券資料官方管道下載均失敗。\n" + "\n".join(logs)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        for gtype, df in parsed_results.items():
            insert_count = 0

            # 因台彩官方 CSV 的欄位有「最前置空白」，已透過 str.strip() 消除，以下可精準對照寫入
            if gtype == "大樂透":
                df_cleaned = df[
                    ['期別', '開獎日期', '獎號1', '獎號2', '獎號3', '獎號4', '獎號5', '獎號6', '特別號']].dropna()
                for _, r in df_cleaned.iterrows():
                    cursor.execute("INSERT OR IGNORE INTO lotto_649 VALUES (?,?,?,?,?,?,?,?,?)",
                                   (int(r['期別']), str(r['開獎日期']), int(r['獎號1']), int(r['獎號2']),
                                    int(r['獎號3']), int(r['獎號4']), int(r['獎號5']), int(r['獎號6']),
                                    int(r['特別號'])))
                    if cursor.rowcount > 0: insert_count += 1
            elif gtype == "今彩 539":
                df_cleaned = df[['期別', '開獎日期', '獎號1', '獎號2', '獎號3', '獎號4', '獎號5']].dropna()
                for _, r in df_cleaned.iterrows():
                    cursor.execute("INSERT OR IGNORE INTO lotto_539 VALUES (?,?,?,?,?,?,?)",
                                   (int(r['期別']), str(r['開獎日期']), int(r['獎號1']), int(r['獎號2']),
                                    int(r['獎號3']), int(r['獎號4']), int(r['獎號5'])))
                    if cursor.rowcount > 0: insert_count += 1
            elif gtype == "威力彩":
                df_cleaned = df[
                    ['期別', '開獎日期', '獎號1', '獎號2', '獎號3', '獎號4', '獎號5', '獎號6', '第二區']].dropna()
                for _, r in df_cleaned.iterrows():
                    cursor.execute("INSERT OR IGNORE INTO lotto_super VALUES (?,?,?,?,?,?,?,?,?)",
                                   (int(r['期別']), str(r['開獎日期']), int(r['獎號1']), int(r['獎號2']),
                                    int(r['獎號3']), int(r['獎號4']), int(r['獎號5']), int(r['獎號6']),
                                    int(r['第二區'])))
                    if cursor.rowcount > 0: insert_count += 1
            elif gtype == "3星彩":
                df_cleaned = df[['期別', '開獎日期', '獎號1', '獎號2', '獎號3']].dropna()
                for _, r in df_cleaned.iterrows():
                    cursor.execute("INSERT OR IGNORE INTO lotto_3d VALUES (?,?,?,?,?)",
                                   (int(r['期別']), str(r['開獎日期']), int(r['獎號1']), int(r['獎號2']),
                                    int(r['獎號3'])))
                    if cursor.rowcount > 0: insert_count += 1
            elif gtype == "4星彩":
                df_cleaned = df[['期別', '開獎日期', '獎號1', '獎號2', '獎號3', '獎號4']].dropna()
                for _, r in df_cleaned.iterrows():
                    cursor.execute("INSERT OR IGNORE INTO lotto_4d VALUES (?,?,?,?,?,?)",
                                   (int(r['期別']), str(r['開獎日期']), int(r['獎號1']), int(r['獎號2']),
                                    int(r['獎號3']), int(r['獎號4'])))
                    if cursor.rowcount > 0: insert_count += 1
            logs.append(f"🟢 {gtype}: 成功同步更新 {insert_count} 期數據")
        conn.commit()
        return True, "\n".join(logs)
    except Exception as e:
        return False, f"寫入 SQLite 資料庫失敗: {str(e)}"
    finally:
        conn.close()


# ----------------------------------------------------
# 2.5 近期冷門球檢索機制 (從最新歷史往前查完全沒出現過的球)
# ----------------------------------------------------
def get_cold_numbers(game_type, limit_periods):
    if game_type in ["3星彩", "4星彩"] or limit_periods == 0:
        return []

    if game_type == "大樂透":
        table, max_ball = "lotto_649", 49
    elif game_type == "威力彩":
        table, max_super = "lotto_super", 38
    else:
        table, max_ball = "lotto_539", 39

    conn = sqlite3.connect(DB_NAME)
    # 取出最近 X 期的所有開獎號碼 (不含威力彩第二區)
    if game_type == "大樂透":
        sql = f"SELECT num1, num2, num3, num4, num5, num6 FROM {table} ORDER BY period DESC LIMIT {limit_periods};"
    elif game_type == "威力彩":
        sql = f"SELECT num1, num2, num3, num4, num5, num6 FROM {table} ORDER BY period DESC LIMIT {limit_periods};"
    else:
        sql = f"SELECT num1, num2, num3, num4, num5 FROM {table} ORDER BY period DESC LIMIT {limit_periods};"

    df = pd.read_sql_query(sql, conn)
    conn.close()

    if df.empty:
        return []

    # 將最近開過的所有球集合起來
    recent_opened = set(df.values.flatten())
    # 找出完全沒有包含在最近開獎集合裡面的號碼，即為「冷門冰封球」
    all_balls = set(range(1, 39 if game_type == "威力彩" else (40 if game_type == "今彩 539" else 50)))
    cold_balls = list(all_balls - recent_opened)
    return cold_balls

# ----------------------------------------------------
# 3. 雙模並行融合演算法 (核心優化)
# ----------------------------------------------------
def get_dual_mode_stats(game_type, target_num, ball_idx=None, limit_periods=100, position_col=None, is_super_sec=False):
    conn = sqlite3.connect(DB_NAME)
    
    # 處理 3/4星彩與威力彩第二區
    if game_type in ["3星彩", "4星彩"] or is_super_sec:
        if is_super_sec:
            sql = f"WITH T AS (SELECT period+1 AS np FROM lotto_super WHERE sec_num=:t ORDER BY period DESC LIMIT {limit_periods}) SELECT h.sec_num AS b, COUNT(*) as c FROM lotto_super h JOIN T ON h.period=t.np GROUP BY b;"
        else:
            table = "lotto_3d" if game_type == "3星彩" else "lotto_4d"
            sql = f"WITH T AS (SELECT period+1 AS np FROM {table} WHERE {position_col}=:t ORDER BY period DESC LIMIT {limit_periods}) SELECT {position_col} AS b, COUNT(*) as c FROM {table} h JOIN T ON h.period=t.np GROUP BY b;"
        df = pd.read_sql_query(sql, conn, params={"t": target_num})
        conn.close()
        return df if not df.empty else pd.DataFrame(columns=['b', 'c'])

    # 處理樂透型雙模融合 (大樂透 / 539 / 威力彩第一區)
    if game_type == "大樂透": table, max_cols = "lotto_649", 6
    elif game_type == "威力彩": table, max_cols = "lotto_super", 6
    else: table, max_cols = "lotto_539", 5

    # 1. 執行【落球模式】SQL
    target_col = f"num{ball_idx + 1}"
    sql_drop = f"""
        WITH T AS (SELECT period + 1 AS np FROM {table} WHERE {target_col} = :t ORDER BY period DESC LIMIT {limit_periods})
        SELECT h.{target_col} AS b, COUNT(*) as drop_count FROM {table} h JOIN T ON h.period = t.np GROUP BY b;
    """
    df_drop = pd.read_sql_query(sql_drop, conn, params={"t": target_num})

    # 2. 執行【大小模式】SQL
    where_clause = " OR ".join([f"num{i}=:t" for i in range(1, max_cols + 1)])
    union_selects = " UNION ALL ".join([f"SELECT h.num{i} AS b FROM {table} h JOIN T ON h.period = t.np" for i in range(1, max_cols + 1)])
    sql_size = f"""
        WITH T AS (SELECT period + 1 AS np FROM {table} WHERE {where_clause} ORDER BY period DESC LIMIT {limit_periods})
        SELECT b, COUNT(*) as size_count FROM ({union_selects}) GROUP BY b;
    """
    df_size = pd.read_sql_query(sql_size, conn, params={"t": target_num})
    conn.close()

    # 3. 在記憶體中進行 Data 合併與加權計算 (已將未定義的 game_selected 修正為 game_type)
    df_all = pd.DataFrame({'b': range(1, 50 if game_type == "大樂透" else (39 if game_type == "威力彩" else 40))})
    df_all = df_all.merge(df_drop, on='b', how='left').merge(df_size, on='b', how='left').fillna(0)
    return df_all

# ----------------------------------------------------
# 4. Streamlit UI 介面
# ----------------------------------------------------
st.set_page_config(page_title="AI 雙模融合拖牌算力儀表板", layout="wide")
init_database()

st.markdown("""
    <style>
        /* 1. 隱藏 DEPLOY 按鈕 */
        .stAppDeployButton {
            display: none !important;
        }

        /* 2. ✨【Sophia 精準置中】安全控制主畫面文字與輸入欄位標題，絕不攪碎佈局骨架 */
        /* 讓主畫面的大標題文字完美靠中浮現 */
        .main h2, .main h3 {
            text-align: center !important;
            width: 100% !important;
            color: #111111 !important;
            margin-bottom: 25px !important;
        }

        /* 讓輸入外框內部的中文自訂標頭（如：第1落球）在各自格子內絕對置中 */
        .main div[style*="text-align: center"] {
            text-align: center !important;
            width: 100% !important;
            margin: 0 auto !important;
        }

        /* 強制讓輸入框白框內部的數字本身在框內居中對齊 */
        div[data-testid="stNumberInput"] input {
            text-align: center !important;
        }

        /* 3. 🎯【表格網頁樣式硬校正】精準鎖定靜態表格的表頭(th)與單元格(td)強制置中 */
        div[data-testid="stTable"] th,
        div[data-testid="stTable"] td {
            text-align: center !important;
            vertical-align: middle !important;
        }

        /* 確保表格容器在橫向網頁排版中完美靠中，絕不偏左 */
        div[data-testid="stTable"] {
            margin: 0 auto !important;
            width: 100% !important;
        }
     </style> 
       """, unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ 核心主控台")

    # 🔐【Sophia 升級：SQLite 資料庫驅動型合法授權管理系統】
    access_password = st.text_input("🔑 請輸入系統合法授權金鑰", type="password")

    if not access_password:
        st.warning("⚠️ 請輸入金鑰以解鎖核心大數據算力。")
        st.stop()

    # 連接資料庫即時查詢該金鑰的合法性
    conn_auth = sqlite3.connect(DB_NAME)
    cursor_auth = conn_auth.cursor()
    cursor_auth.execute("SELECT user_name, expire_date, role FROM auth_users WHERE user_key = ?", (access_password,))
    auth_result = cursor_auth.fetchone()
    conn_auth.close()

    # 判定金鑰是否存在
    if auth_result is None:
        st.error("❌ 授權金鑰不合法，系統核心算力已全面鎖定。")
        st.stop()

    # 提取資料庫中的動態用戶特徵
    user_name, expire_date_str, user_role = auth_result

    # 進行到期日合法性邏輯檢核
    current_date = pd.to_datetime("today").normalize()
    expire_date = pd.to_datetime(expire_date_str)

    if current_date > expire_date:
        st.error(f"❌ 抱歉！使用者 [{user_name}] 的授權已於 {expire_date_str} 到期，請聯絡發行者更新。")
        st.stop()

    st.success(f"🔓 歡迎回來，{user_name}！")

    # 🌟 核心管理員權限開關：直接由資料庫中的角色欄位（role == 'admin'）來動態決定！
    is_admin = (user_role == "admin")

    st.markdown("---")
    # 原本的選單與滑桿
    game_selected = st.selectbox("選擇彩券類型", ["大樂透", "今彩 539", "威力彩", "3星彩", "4星彩"])
    period_range = st.slider("採計歷史期數", 50, 500, 150, step=50)

    st.markdown("---")
    # 🧊 2. 冷門球過濾機制開關
    st.subheader("❄️ 冷門球（冰封球）過濾")
    enable_filter = st.checkbox("啟動歷史冷門球過濾機制")
    if enable_filter:
        filter_limit = st.slider("過濾掉近期「完全未開出」達幾期的球號", 5, 30, 10, step=1)
        st.caption(f"💡 系統將自動檢索數據庫，剃除最近 {filter_limit} 期內完全沒開過的邊緣球。")
    else:
        filter_limit = 0

#    game_selected = st.selectbox("選擇彩券類型", ["大樂透", "今彩 539", "威力彩", "3星彩", "4星彩"])
#    period_range = st.slider("採計歷史期數", 50, 500, 150, step=50)

    # ----------------------------------------------------
    # 🔐【Sophia 智慧名單同步】自動將新帳號動態寫入實體資料庫 (.db 檔案)
    # ----------------------------------------------------
    try:
        conn_sync = sqlite3.connect(DB_NAME)
        cursor_sync = conn_sync.cursor()
        # 💡 自動增留：每次啟動都會檢查，如果資料庫沒有 vipguan，就主動幫您實體寫入
        cursor_sync.execute("INSERT OR IGNORE INTO auth_users (user_key, user_name, expire_date, role) VALUES ('vipguan', '親友合夥人', '2030-06-30', 'user')")
        conn_sync.commit()
        conn_sync.close()
    except:
        pass

    # ----------------------------------------------------
    # 🎛️ 融合權重配比 (所有使用者均可操作)
    # ----------------------------------------------------
    st.markdown("---")
    st.subheader("🎛️ 融合權重配比")
    w_size = st.slider("大小順序 (數學連動) 權重 %", 0, 100, 50, step=10)
    w_drop = 100 - w_size
    st.caption(f"當前公式：`(大小次數 * {w_size / 100}) + (落球次數 * {w_drop / 100})`")

    # ----------------------------------------------------
    # 🔒【管理員特權區】只有當 is_admin 為 True 時，底下的同步與上傳才會浮現！
    # ----------------------------------------------------
    if is_admin:
        st.markdown("---")
        st.subheader("⚡ 數據同步（最高管理員專屬）")
        if st.button("🚀 啟動全彩券官方網路同步"):
            with st.spinner("非同步多執行緒同步中..."):
                success, msg_log = sync_all_lottery_data_parallel()
                if success: st.success("🎉 同步完成！")
                else: st.error("同步程序部分中斷")
                st.code(msg_log)

        st.markdown("---")
        st.subheader("📂 備援選項：上傳本機歷史資料")
        uploaded_file = st.file_uploader(f"請上傳 [{game_selected}] 的 Excel 或 CSV 檔", type=["xlsx", "xls", "csv"])

        if uploaded_file is not None:
            if st.button(f"📥 導入 {game_selected} 歷史數據"):
                try:
                    excel_df = pd.read_csv(uploaded_file, encoding='cp950') if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
                    excel_df.columns = excel_df.columns.str.strip()
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    import_count = 0

                    if game_selected == "大樂透":
                        for _, r in excel_df[['期別', '開獎日期', '獎號1', '獎號2', '獎號3', '獎號4', '獎號5', '獎號6', '特別號']].dropna().iterrows():
                            cursor.execute("INSERT OR IGNORE INTO lotto_649 VALUES (?,?,?,?,?,?,?,?,?)", (int(r['期別']), str(r['開獎日期']), int(r['獎號1']), int(r['獎號2']), int(r['獎號3']), int(r['獎號4']), int(r['獎號5']), int(r['獎號6']), int(r['特別號'])))
                            if cursor.rowcount > 0: import_count += 1
                    elif game_selected == "今彩 539":
                        for _, r in excel_df[['期別', '開獎日期', '獎號1', '獎號2', '獎號3', '獎號4', '獎號5']].dropna().iterrows():
                            cursor.execute("INSERT OR IGNORE INTO lotto_539 VALUES (?,?,?,?,?,?,?)", (int(r['期別']), str(r['開獎日期']), int(r['獎號1']), int(r['獎號2']), int(r['獎號3']), int(r['獎號4']), int(r['獎號5'])))
                            if cursor.rowcount > 0: import_count += 1
                    elif game_selected == "威力彩":
                        for _, r in excel_df[['期別', '開獎日期', '獎號1', '獎號2', '獎號3', '獎號4', '獎號5', '獎號6', '第二區']].dropna().iterrows():
                            cursor.execute("INSERT OR IGNORE INTO lotto_super VALUES (?,?,?,?,?,?,?,?,?)", (int(r['期別']), str(r['開獎日期']), int(r['獎號1']), int(r['獎號2']), int(r['獎號3']), int(r['獎號4']), int(r['獎號5']), int(r['獎號6']), int(r['第二區'])))
                            if cursor.rowcount > 0: import_count += 1
                    elif game_selected == "4星彩":
                        for _, r in excel_df[['期別', '開獎日期', '獎號1', '獎號2', '獎號3', '獎號4']].dropna().iterrows():
                            cursor.execute("INSERT OR IGNORE INTO lotto_4d VALUES (?,?,?,?,?,?)", (int(r['期別']), str(r['開獎日期']), int(r['獎號1']), int(r['獎號2']), int(r['獎號3']), int(r['獎號4'])))
                            if cursor.rowcount > 0: import_count += 1

                    conn.commit()
                    conn.close()
                    st.success(f"🎉 數據導入成功！共更新了 {import_count} 期未重複之歷史數據。")
                except Exception as e:
                    st.error(f"❌ 解析或寫入資料庫失敗。錯誤訊息: {str(e)}")

    # ----------------------------------------------------
    # 📊 戰情看盤：SQLite 歷史數據庫存即時檢視列
    # ----------------------------------------------------
st.markdown("---")
st.subheader("📊 本機數據庫存看板")
try:
    conn_check = sqlite3.connect(DB_NAME)
    cursor_check = conn_check.cursor()

    # 智慧查詢各表：總期數、最新期數、以及最新一期的開獎日期
    counts = {}
    for game_name, tbl in [("大樂透", "lotto_649"), ("今彩 539", "lotto_539"), ("威力彩", "lotto_super"),
                           ("3星彩", "lotto_3d"), ("4星彩", "lotto_4d")]:
        # 💡 【Sophia 終極修正】改用 ORDER BY period DESC LIMIT 1 的子查詢，完美繞過 SQLite 的 MAX 限制！
        sql_query = f"""
            SELECT 
                (SELECT COUNT(*) FROM {tbl}),
                (SELECT period FROM {tbl} ORDER BY period DESC LIMIT 1),
                (SELECT open_date FROM {tbl} ORDER BY period DESC LIMIT 1)
        """
        cursor_check.execute(sql_query)
        total, max_p, max_date = cursor_check.fetchone()

        # 智慧安全防空值字串配置
        total_p = total if total else 0
        display_period = max_p if max_p else "無資料"
        display_date = max_date if max_date else "無資料"

        counts[game_name] = (total_p, display_period, display_date)

    conn_check.close()

    # ✨【期數 + 日期雙指標看盤：全原生高質感對稱排版】
    c_col1, c_col2, c_col3 = st.columns(3)

    with c_col1:
        st.metric("🔴 大樂透總庫存", f"{counts['大樂透'][0]} 期",
                  f"最新: {counts['大樂透'][1]} 期 | {counts['大樂透'][2]}", delta_color="off")
        st.metric("🟡 3星彩總庫存", f"{counts['3星彩'][0]} 期", f"最新: {counts['3星彩'][1]} 期 | {counts['3星彩'][2]}",
                  delta_color="off")

    with c_col2:
        st.metric("🟢 今彩539庫存", f"{counts['今彩 539'][0]} 期",
                  f"最新: {counts['今彩 539'][1]} 期 | {counts['今彩 539'][2]}", delta_color="off")
        st.metric("🟠 4星彩總庫存", f"{counts['4星彩'][0]} 期", f"最新: {counts['4星彩'][1]} 期 | {counts['4星彩'][2]}",
                  delta_color="off")

    with c_col3:
        st.metric("🔵 威力彩總庫存", f"{counts['威力彩'][0]} 期",
                  f"最新: {counts['威力彩'][1]} 期 | {counts['威力彩'][2]}", delta_color="off")

except Exception as e_check:
    st.caption(f"❌ 數據庫看板讀取失敗。錯誤訊息: {str(e_check)}")

# ----------------------------------------------------
# 📌【核心補修】主畫面動態變數配置與獎號手動輸入區
# ----------------------------------------------------
if game_selected == "大樂透":
    max_ball, ball_labels, pos_cols, default_vals = 49, ["第1落球", "第2落球", "第3落球", "第4落球", "第5落球", "第6落球"], None, [11, 20, 23, 33, 34, 44]
elif game_selected == "今彩 539":
    max_ball, ball_labels, pos_cols, default_vals = 39, ["第1落球", "第2落球", "第3落球", "第4落球", "第5落球"], None, [1, 2, 3, 4, 5]
elif game_selected == "威力彩":
    max_ball, ball_labels, pos_cols, default_vals = 38, ["第一區 落球1", "第一區 落球2", "第一區 落球3", "第一區 落球4", "第一區 落球5", "第一區 落球6"], None, [1, 2, 3, 4, 5, 6]
elif game_selected == "3星彩":
    max_ball, ball_labels, pos_cols, default_vals = 9, ["佰位", "拾位", "個位"], ["hundreds", "tens", "units"], [8, 7, 0]
elif game_selected == "4星彩":
    max_ball, ball_labels, pos_cols, default_vals = 9, ["千位", "佰位", "拾位", "個位"], ["thousands", "hundreds", "tens", "units"], [1, 2, 8, 0]

st.subheader(f"🔮 輸入前一期開出之 [{game_selected}] 獎號 (雙模融合模式)")
cols_input = st.columns(len(ball_labels) + (1 if game_selected == "威力彩" else 0))
input_numbers = []
min_v = 0 if game_selected in ["3星彩", "4星彩"] else 1

for i, label in enumerate(ball_labels):
    with cols_input[i]:
        num = st.number_input(label, min_value=min_v, max_value=max_ball, value=default_vals[i], key=f"b_{i}")
        input_numbers.append(num)

super_sec_input = 2  # 預防非威力彩模式點分析時發生變數未定義錯誤
if game_selected == "威力彩":
    with cols_input[-1]:
        super_sec_input = st.number_input("第二區 特別號", min_value=1, max_value=8, value=2)

# ----------------------------------------------------
# 5. 執行融合計算與視覺化 (全彩券解鎖與 3/4星彩終極置中硬校正)
# ----------------------------------------------------
# 🌟【Sophia 修正】解鎖縮排！將分析按鈕抽回頂層，讓所有彩券類型同步回歸浮現
if st.button("⚡ 啟動雙模大數據融合分析"):
    if game_selected in ["3星彩", "4星彩"]:
        st.markdown(f"### 🎯 [{game_selected}] 位置正彩精確預測")
        cols_res = st.columns(len(pos_cols))
        for i, pos in enumerate(pos_cols):
            with cols_res[i]:
                df_pos = get_dual_mode_stats(game_selected, input_numbers[i], limit_periods=period_range,
                                             position_col=pos)
                if not df_pos.empty:
                    df_pos.columns = ['預測數字', '歷史次數']
                    df_pos = df_pos.sort_values(by='歷史次數', ascending=False)

                    # 指標卡同步優化置中
                    st.metric(f"{ball_labels[i]} 首選", f" {df_pos['預測數字'].iloc[0]} ")

                    # 🌟【終極置中】將 3/4星彩改用 HTML 架構的 st.table，強制表頭文字與數值 100% 完美對齊正中央
                    df_pos_render = df_pos.copy()
                    df_pos_render['預測數字'] = df_pos_render['預測數字'].astype(str)
                    df_pos_render['歷史次數'] = df_pos_render['歷史次數'].astype(str)

                    # 套用精緻的暖橘色戰情漸層熱圖
                    st.table(df_pos_render.style.background_gradient(cmap='Oranges', subset=['歷史次數']))
    else:
        # 大樂透 / 539 / 威力彩第一區（核心融合渲染）
        master_df = pd.DataFrame({'b': range(1, max_ball + 1), '落球總次數': 0.0, '大小總次數': 0.0})
        for i, n in enumerate(input_numbers):
            df_res = get_dual_mode_stats(game_selected, n, ball_idx=i, limit_periods=period_range)
            if not df_res.empty:
                master_df['落球總次數'] += master_df['b'].map(df_res.set_index('b')['drop_count']).fillna(0)
                master_df['大小總次數'] += master_df['b'].map(df_res.set_index('b')['size_count']).fillna(0)

        master_df['AI 綜合融合得分'] = (master_df['大小總次數'] * (w_size / 100.0)) + (
                    master_df['落球總次數'] * (w_drop / 100.0))
        master_df = master_df.sort_values(by='AI 綜合融合得分', ascending=False).reset_index(drop=True)
        master_df.columns = ['球號', '歷史落球累計', '歷史大小累計', 'AI 綜合融合得分']

        # ❄️ 冷門球過濾核心邏輯
        if enable_filter:
            cold_ones = get_cold_numbers(game_selected, filter_limit)
            if cold_ones:
                st.info(
                    f"❄️ 依據數據庫檢索，最近 {filter_limit} 期未開出的冷門球有：{', '.join([f'{x:02d}' for x in cold_ones])} 號")
                master_df = master_df[~master_df['球號'].isin(cold_ones)].reset_index(drop=True)

        render_df = master_df.copy()
        render_df['球號'] = render_df['球號'].apply(lambda x: f"{int(x):02d}")
        render_df['歷史落球累計'] = render_df['歷史落球累計'].apply(lambda x: f"{int(x)}")
        render_df['歷史大小累計'] = render_df['歷史大小累計'].apply(lambda x: f"{int(x)}")
        render_df['AI 綜合融合得分'] = render_df['AI 綜合融合得分'].apply(lambda x: f"{x:.1f}")

        if game_selected == "威力彩":
            col_z1, col_z2 = st.columns([3, 1])
            with col_z1:
                st.markdown("### 🔵 第一區雙模加權融合結果")
                st.metric("雙模制霸黃金首選球", f"{int(master_df['球號'].iloc[0]):02d} 號")
                st.table(render_df.style.background_gradient(cmap='Blues', subset=['AI 綜合融合得分']))
                st.bar_chart(master_df.set_index('球號')['AI 綜合融合得分'], color='#1f77b4')

            with col_z2:
                st.markdown("### 🔴 第二區預測")
                df_sec = get_dual_mode_stats(game_selected, super_sec_input, limit_periods=period_range,
                                             is_super_sec=True)
                if not df_sec.empty:
                    df_sec.columns = ['球號', '次數']
                    df_sec = df_sec.sort_values(by='次數', ascending=False)
                    st.metric("第二區天選球", f"{int(df_sec['球號'].iloc[0]):02d} 號")
                    df_sec_render = df_sec.copy()
                    df_sec_render['球號'] = df_sec_render['球號'].apply(lambda x: f"{int(x):02d}")
                    df_sec_render['次數'] = df_sec_render['次數'].apply(lambda x: f"{int(x)}")
                    st.table(df_sec_render.style.background_gradient(cmap='Reds', subset=['次數']))
        else:
            # 📊 大樂透 / 539 展示
            st.markdown(f"### 📊 [{game_selected}] 雙模綜合加權算力看板")
            top_3 = master_df['球號'].head(3).astype(int).tolist()
            st.metric("🏆 雙模交叉制霸球推薦（已排除冰封冷門球）" if enable_filter else "🏆 雙模交叉制霸球推薦",
                      f"{', '.join([f'{x:02d}' for x in top_3])} 號")
            st.table(render_df.style.background_gradient(cmap='Blues', subset=['AI 綜合融合得分']))
            st.bar_chart(master_df.set_index('球號')['AI 綜合融合得分'], color='#1f77b4')

# ----------------------------------------------------
# 👑【最高管理員特權區】智慧資料庫控制台 (檢視/修改號碼、清空數據、金鑰自主增減)
# ----------------------------------------------------
# 只有登入 admin888 且順利通過前面的 is_admin 判定時，主畫面最下方才會解鎖此終極後台
if 'is_admin' in locals() and is_admin:
    st.markdown("---")
    st.markdown("## 👑 最高管理員安全控制台 (後台數據中心)")

    # 建立三個精緻的實戰戰情標籤頁面
    tab_data, tab_clear, tab_auth = st.tabs(
        ["📝 1. 獎號數據檢檢視與修改", "🗑️ 2. 清空某一機種數據", "🔐 3. 用戶授權金鑰自主增減"])

    # ------------------------------------------------
    # 📝 頁面 1：檢視與修改開獎號碼
    # ------------------------------------------------
    with tab_data:
        st.subheader("📝 歷史開獎號碼智慧管理 (動態 SQL 硬更新)")
        # 💡【Sophia 精準修正】將 3星彩（lotto_3d）正式納入後台數據庫管理地圖中
        game_table_map = {
            "大樂透": "lotto_649",
            "今彩 539": "lotto_539",
            "威力彩": "lotto_super",
            "3星彩": "lotto_3d",  # 👈 補上這行
            "4星彩": "lotto_4d"
        }

        manage_game = st.selectbox("請選擇要管理的彩券類型", list(game_table_map.keys()), key="manage_game_sel")
        target_tbl = game_table_map[manage_game]

        # 讀取目前該機種的所有數據
        conn_m = sqlite3.connect(DB_NAME)
        df_m = pd.read_sql_query(f"SELECT * FROM {target_tbl} ORDER BY period DESC", conn_m)
        conn_m.close()

        if not df_m.empty:
            st.caption(f"💡 目前數據庫內已有 {len(df_m)} 期資料。如需微調特定期數，請在下方輸入期別：")

            # 使用大數據過濾器，讓管理員直接指定期數
            edit_period = st.number_input("請輸入要求改或檢視的「期別」", min_value=int(df_m['period'].min()),
                                          max_value=int(df_m['period'].max()), value=int(df_m['period'].max()))
            df_row = df_m[df_m['period'] == edit_period]

            if not df_row.empty:
                st.warning(f"🔔 正在編輯：[{manage_game}] 第 {edit_period} 期之開獎資料")

                # 動態根據欄位生成橫向修改框
                cols_edit = st.columns(len(df_m.columns) - 1)
                new_values = {}
                col_idx = 0

                for col in df_m.columns:
                    if col == 'period': continue
                    with cols_edit[col_idx]:
                        val_type = df_row[col].iloc[0]
                        if isinstance(val_type, (int, float)):
                            new_values[col] = st.number_input(f"修改 {col}", value=int(val_type),
                                                              key=f"edit_{col}_{edit_period}")
                        else:
                            new_values[col] = st.text_input(f"修改 {col}", value=str(val_type),
                                                            key=f"edit_{col}_{edit_period}")
                        col_idx += 1

                # 執行寫入變更
                if st.button(f"💾 儲存第 {edit_period} 期變更並即時校正"):
                    try:
                        conn_up = sqlite3.connect(DB_NAME)
                        cursor_up = conn_up.cursor()
                        set_clause = ", ".join([f"{k} = ?" for k in new_values.keys()])
                        params = list(new_values.values()) + [edit_period]
                        cursor_up.execute(f"UPDATE {target_tbl} SET {set_clause} WHERE period = ?", params)
                        conn_up.commit()
                        conn_up.close()
                        st.success(f"🎉 成功！第 {edit_period} 期的資料已在實體資料庫內精準導正變更。")
                        st.rerun()
                    except Exception as e_up:
                        st.error(f"❌ 修正失敗: {str(e_up)}")
            else:
                st.error("❌ 找不到此期別，請確認數據庫庫存看板。")

            st.markdown("#### 🔍 目前全數據動態預覽 (最新期數排在最前)")
            st.dataframe(df_m, use_container_width=True, hide_index=True)
        else:
            st.info("💡 目前此機種數據庫內尚無資料。")

    # ------------------------------------------------
    # 🗑️ 頁面 2：一鍵刪除、清空某種數據 (方便重新導入)
    # ------------------------------------------------
    with tab_clear:
        st.subheader("🗑️ 資料庫重整中心 (一鍵清空去髒資料)")
        st.error("⚠️ 警告：此操作將會徹底抹除該彩券在本機的所有歷史期數，以便您重新導入最乾淨的 CSV 資料！")
        clear_game = st.selectbox("請選取您要「完全清空、重新洗牌」的機種", ["請選擇"] + list(game_table_map.keys()),
                                  key="clear_game_sel")

        if clear_game != "請選擇":
            clear_tbl = game_table_map[clear_game]
            st.warning(f"💣 您已選取清空：[{clear_game}] 資料表名稱 ({clear_tbl})")

            # 安全防誤觸雙重確認二次勾選鎖
            double_check = st.checkbox(f"我已確認要徹底清空所有的 [{clear_game}] 數據，此動作無法復原。")
            if double_check:
                if st.button(f"🔥 執行一鍵摧毀並清空 [{clear_game}] 歷史數據庫"):
                    try:
                        conn_del = sqlite3.connect(DB_NAME)
                        cursor_del = conn_del.cursor()
                        cursor_del.execute(f"DELETE FROM {clear_tbl}")
                        conn_del.commit()
                        conn_del.close()
                        st.success(
                            f"🎉【大清理成功】所有的 [{clear_game}] 歷史數據已被洗刷一空！您現在可以回到側邊欄重新上傳最完美的 CSV 檔了。")
                        st.rerun()
                    except Exception as e_del:
                        st.error(f"❌ 摧毀清空失敗: {str(e_del)}")

    # ------------------------------------------------
    # 🔐 頁面 3：權限資料庫自主增減修改管理
    # ------------------------------------------------
    with tab_auth:
        st.subheader("🔐 全球金鑰自主授權中心 (免改程式動態管理)")

        # 讀取目前的所有用戶金鑰著名單
        conn_a = sqlite3.connect(DB_NAME)
        df_a = pd.read_sql_query("SELECT * FROM auth_users", conn_a)
        conn_a.close()

        # 展示目前的用戶列表
        st.markdown("#### 👥 當前合法授權使用者字典列表")
        st.table(df_a)

        st.markdown("---")
        # 橫向切分：新增使用者 與 刪除使用者
        col_add, col_del = st.columns(2)

        with col_add:
            st.markdown("##### ➕ 發行/新增全新的合法金鑰")
            new_key = st.text_input("1. 設定登入授權金鑰 (密碼)", placeholder="例如: friend999")
            new_name = st.text_input("2. 輸入使用者名稱 (姓名)", placeholder="例如: 王小明")
            new_expire = st.text_input("3. 設定到期截止日 (YYYY-MM-DD)", value="2027-12-31")
            new_role = st.selectbox("4. 分配系統權限角色", ["user (普通親友)", "admin (最高管理員)"])
            actual_role = "admin" if "admin" in new_role else "user"

            if st.button("🚀 實體寫入並發行此金鑰"):
                if new_key and new_name:
                    try:
                        conn_add = sqlite3.connect(DB_NAME)
                        cursor_add = conn_add.cursor()
                        cursor_add.execute("INSERT OR REPLACE INTO auth_users VALUES (?, ?, ?, ?)",
                                           (new_key.strip(), new_name.strip(), new_expire.strip(), actual_role))
                        conn_add.commit()
                        conn_add.close()
                        st.success(f"🎉【授權成功】全新金鑰 {new_key} 已成功發行給 [{new_name}]！")
                        st.rerun()
                    except Exception as e_add:
                        st.error(f"❌ 發行金鑰失敗: {str(e_add)}")
                else:
                    st.error("❌ 金鑰密碼與使用者名稱不能留空！")

        with col_del:
            st.markdown("##### ➖ 徹底註銷/刪除使用者授權")
            st.caption("💡 只要在這裡將特定金鑰註銷，該使用者下次登入就會被全網強行中斷鎖定。")
            del_key = st.selectbox("請選取您要「徹底註銷、收回權限」的金鑰密碼", ["請選擇"] + df_a['user_key'].tolist())

            if del_key != "請選擇" and del_key != "admin888":  # 防止管理員不小心把自己刪除
                st.warning(f"🚨 確定要收回該使用者的所有算力權限嗎？")
                if st.button("🗑️ 確定執行強行註銷"):
                    try:
                        conn_del_u = sqlite3.connect(DB_NAME)
                        cursor_del_u = conn_del_u.cursor()
                        cursor_del_u.execute("DELETE FROM auth_users WHERE user_key = ?", (del_key,))
                        conn_del_u.commit()
                        conn_del_u.close()
                        st.success(f"🎉 成功註銷金鑰！該用戶已無法再連上您的核心看盤大數據。")
                        st.rerun()
                    except Exception as e_del_u:
                        st.error(f"❌ 註銷失敗: {str(e_del_u)}")
            elif del_key == "admin888":
                st.error("❌ 系統安全防護保護中：不允許刪除您自己的最高管理員管理金鑰！")
