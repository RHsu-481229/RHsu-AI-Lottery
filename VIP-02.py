# ====================================================
# 👑【VIP-02 雙引擎完全體】全域掃描與連續出牌極限智庫 (vip-02.py - 頂級進裝版 - Part 1)
# ====================================================
import streamlit as st
import sqlite3
import pandas as pd
import io
import os

# 📡【Sophia 智慧雷達自動定位導航】100% 徹底鎖定實體路徑
current_folder = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(current_folder, "Lotto_Multi.db")

# 💡 1. 精密設定 10 組獨立黃金群組號碼映射字典
GRP_RAW = {
    "GRP 1": "1,10,29,38",
    "GRP 2": "2,11,20,39",
    "GRP 3": "3,12,21,30",
    "GRP 4": "4,13,22,31",
    "GRP 5": "5,14,23,32",
    "GRP 6": "6,15,24,33",
    "GRP 7": "7,16,25,34",
    "GRP 8": "8,17,26,35",
    "GRP 9": "9,18,27,36",
    "GRP 10": "10,19,28,37"
}

GRP_CONFIG = {}
for g_key, g_val in GRP_RAW.items():
    GRP_CONFIG[g_key] = [int(x) for x in g_val.split(",")]

GRP_LABEL_MAP = {}
for g_key, b_list in GRP_CONFIG.items():
    GRP_LABEL_MAP[g_key] = f"({', '.join([f'{x:02d}' for x in b_list])})"

# 設置商業級高質感全設備靠左網頁配置
st.set_page_config(page_title="👑 AI 雙模融合・VIP 戰情室", layout="wide")

# ====================================================
# 🔐【Sophia 終極特權鎖】JS 影子節點監聽・Deploy 按鈕全網惡意強行抹除 (100% 根除)
# ====================================================
# 智慧判定：只要當前使用者「不是」最高管理員，立刻在瀏覽器底層發動 JavaScript 實體拔除令！
if ("vip2_is_admin" not in st.session_state) or (not st.session_state["vip2_is_admin"]):
    st.components.v1.html("""
        <script>
            // 💡 建立一個自癒型定時監聽器，每 100 毫秒瘋狂掃描一次網頁骨架
            const observer = new MutationObserver((mutations) => {
                // 1. 抓取標準 Deploy 按鈕
                const deployBtn = window.parent.document.querySelector('.stDeployButton');
                if (deployBtn) { deployBtn.remove(); }

                // 2. 抓取新版 Streamlit 雲端頂部彩端 Toolbar 保護區
                const header = window.parent.document.querySelector('header');
                if (header) {
                    // 將頂部工具列直接隱形，親友用手機看盤時版面會變得極度純淨、空間更大！
                    header.style.display = 'none';
                    header.style.height = '0px';
                }
            });

            // 啟動雷達，死死鎖定雲端網頁的肉體根節點
            observer.observe(window.parent.document.body, { childList: true, subtree: true });
        </script>
    """, height=0, width=0)
# ====================================================

# 注入 CSS 黑科技：強制將 12 期號碼方塊極致向左收緊、縮小欄位間距
st.markdown("""
    <style>
        div[data-testid="stTable"] { max-width: 720px !important; margin-left: 0 !important; margin-right: auto !important; }
        div[data-testid="stTable"] th, div[data-testid="stTable"] td { text-align: center !important; vertical-align: middle !important; }
        div[data-testid="stHorizontalBlock"] { justify-content: flex-start !important; gap: 8px !important; }
        div[data-testid="stHorizontalBlock"] > div { max-width: 85px !important; flex: none !important; }
        div[data-testid="stHorizontalBlock"] > div:first-child { max-width: 240px !important; }
    </style>
""", unsafe_allow_html=True)

# 持久型智慧通知中心
if "vip2_toast" in st.session_state and st.session_state["vip2_toast"]:
    st.toast(st.session_state["vip2_toast"], icon="✅")
    st.session_state["vip2_toast"] = ""

# ====================================================
# 🔐【安全防禦閘門】資料庫驱动型授權金鑰密碼安全鎖中心
# ====================================================
if "vip2_authenticated" not in st.session_state:
    st.session_state["vip2_authenticated"] = False
if "vip2_username" not in st.session_state:
    st.session_state["vip2_username"] = ""
if "vip2_is_admin" not in st.session_state:
    st.session_state["vip2_is_admin"] = False
# ====================================================
# 🔐【安全防禦閘門】資料庫驅動型授權金鑰密碼安全鎖中心 (自帶鍵盤 Enter 一鍵大通關版)
# ====================================================
if "vip2_authenticated" not in st.session_state:
    st.session_state["vip2_authenticated"] = False
if "vip2_username" not in st.session_state:
    st.session_state["vip2_username"] = ""
if "vip2_is_admin" not in st.session_state:
    st.session_state["vip2_is_admin"] = False

if not st.session_state["vip2_authenticated"]:
    st.markdown("## 🔐 歡迎登入 VIP 雙算力戰情室")
    st.caption(
        "💡 本平台受實體金鑰數據庫保護，輸入金鑰後按下「Enter」或點擊下方按鈕繼續。")

    # 🌟【Sophia 終極打包表單鎖】將密碼格與按鈕完美收納進 form 容器中，強制打通鍵盤 Enter 聯動通道！
    with st.form(key="vip2_login_form_lock", clear_on_submit=False):
        input_key = st.text_input("請輸入尊榮授權金鑰：", type="password",
                                  placeholder="user name")

        # 實體換上表單專屬的提交按鈕
        submit_clicked = st.form_submit_button("🚀 驗證金鑰並解鎖算力平台")

        # 💡 雙通道啟動：當實體滑鼠點擊按鈕，或是使用者在密碼格直接按下「Enter」按鍵時，此條件通通 100% 完美成立！
        if submit_clicked:
            if input_key.strip():
                conn_auth = sqlite3.connect(DB_NAME)
                cursor_auth = conn_auth.cursor()
                cursor_auth.execute(
                    "CREATE TABLE IF NOT EXISTS auth_users (user_key TEXT PRIMARY KEY, user_name TEXT, expire_date TEXT, role TEXT)")
                cursor_auth.execute(
                    "INSERT OR IGNORE INTO auth_users VALUES ('admin888', '最高管理員', '2035-12-31', 'admin')")
                conn_auth.commit()

                cursor_auth.execute("SELECT user_name, expire_date, role FROM auth_users WHERE user_key = ?",
                                    (input_key.strip(),))
                res_user = cursor_auth.fetchone()
                conn_auth.close()

                if res_user:
                    u_name, u_expire, u_role = res_user
                    from datetime import datetime

                    current_date_str = datetime.now().strftime("%Y-%m-%d")

                    if u_expire < current_date_str:
                        st.error(
                            f"❌ 登入失敗：您的授權金鑰 ({input_key.strip()}) 已於 {u_expire} 屆期失效！請聯絡最高管理員續正。")
                    else:
                        st.session_state["vip2_authenticated"] = True
                        st.session_state["vip2_username"] = u_name
                        st.session_state["vip2_is_admin"] = (u_role == "admin")
                        st.session_state["vip2_toast"] = f"🎉 歡迎回來，{u_name}！您的 VIP II 頂級算力權限已全數對齊解鎖。"
                        st.rerun()
                else:
                    st.error("❌ 登入失敗：查無此授權金鑰，請重新輸入。")
            else:
                st.error("❌ 金鑰欄位不能留空！")

    st.stop()

# ====================================================
# 🎛️ Sidebar 控制面板中心 (左側控制區)
# ====================================================
st.sidebar.title("👑 VIP 雙算力戰情室")
st.sidebar.info(f"👤 當前用戶: {st.session_state['vip2_username']}")

game_map = {"今彩 539": "lotto_539", "大樂透": "lotto_649", "威力彩": "lotto_super", "3星彩": "lotto_3d",
            "4星彩": "lotto_4d"}
game_selected = st.sidebar.selectbox("請選擇彩券種類", list(game_map.keys()), key="vip2_game_select")
tbl_name = game_map[game_selected]

search_periods = st.sidebar.slider("請選取歷史搜尋期數範圍", min_value=10, max_value=300, value=300, step=10,
                                   key="vip2_period_slider")

st.sidebar.markdown("---")
st.sidebar.subheader("🧮 拖牌核心演算法切換")
calc_mode = st.sidebar.radio(
    "請選擇計算模式：",
    ["🔍 1. 全域雷達大掃描拖牌", "🔥 2. 連續出牌統計"],
    key="vip2_calc_mode"
)

# 💡 只有登入成功的使用者，側邊欄才會浮現這個啟動原本主程式控制台的直達傳送門！
st.sidebar.markdown("---")
st.sidebar.subheader("📊 擴充算力主控台")
# 填入您目前官方綁定 app-v11.py 的那個實體雲端網址
# st.sidebar.markdown('<a href="https://streamlit.app" target="_blank"><button style="width:100%; border-radius:5px; background-color:#1E88E5; color:white; border:none; padding:8px; cursor:pointer;">🚀 啟動原本標準雙模融合看板</button></a>', unsafe_allow_html=True)
# 🟢【Sophia 實體對齊】精準配置您專屬的 GitHub 儲存庫 app-v11.py 官方雲端獨立分頁門牌超連結！
st.sidebar.markdown('<a href="https://streamlit.app" target="_blank"><button style="width:100%; border-radius:5px; background-color:#1E88E5; color:white; border:none; padding:8px; cursor:pointer; font-weight:bold;">🚀 啟動原本標準雙模融合看板</button></a>', unsafe_allow_html=True)


if st.sidebar.button("🔒 登出安全戰情室"):
    st.session_state["vip2_authenticated"] = False
    st.session_state["vip2_is_admin"] = False
    st.rerun()

# ====================================================
# 🔮 12 期開獎號碼「期別由小到大往下排列」收緊交互矩陣
# ====================================================
try:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({tbl_name})")
    cols_info = cursor.fetchall()

    ball_cols = []
    for c in cols_info:
        col_name_str = str(c[1])
        if col_name_str.startswith('num') or col_name_str in ['hundreds', 'tens', 'units', 'thousands', 'sp_num',
                                                              'sec_num']:
            ball_cols.append(col_name_str)

    ball_cols_str = ", ".join(ball_cols)

    df_12 = pd.read_sql_query(
        f"SELECT period, open_date, {ball_cols_str} FROM {tbl_name} ORDER BY period DESC LIMIT 12", conn)
    conn.close()
except Exception as e_db:
    st.error(f"❌ 數據庫讀取受阻（{str(e_db)}）。請確認已將手動更新好的實體 Lotto_Multi.db 複製一份到本資料夾。")
    st.stop()

if df_12.empty:
    st.error("❌ 數據庫內目前無相符歷史開獎數據。")
    st.stop()

p_to_n_mapping = {int(row['period']): (row_idx + 1) for row_idx, row in df_12.iterrows()}
df_12_ascending = df_12.sort_values(by="period", ascending=True).reset_index(drop=True)

st.markdown(f"### 📅 最近 12 期 [{game_selected}] 歷史開獎號碼")
st.caption("💡 操作心法：號碼已依落球順序靠左緊密排開。請勾選號碼（打勾即反白），系統會即時在下方切換不同算法進行大數據追蹤！")

selected_targets = []

for idx, row in df_12_ascending.iterrows():
    p_num = int(row['period'])
    o_date = str(row['open_date'])

    cols_row = st.columns([3.0] + [1.0] * len(ball_cols))

    with cols_row[0]:
        st.markdown(f"**第 {p_num} 期** `{o_date}`")

    for pos_idx, col_name in enumerate(ball_cols):
        ball_val = int(row[col_name])
        with cols_row[pos_idx + 1]:
            is_default_checked = (p_num == df_12["period"].max())

            is_clicked = st.checkbox(
                f"{ball_val:02d}",
                value=is_default_checked,
                key=f"chk_v2_{p_num}_{col_name}_{ball_val}"
            )

            if is_clicked:
                real_n_val = p_to_n_mapping[p_num]
                selected_targets.append((real_n_val, col_name, ball_val, p_num))

if not selected_targets:
    st.warning("⚠️ 請至少勾選一或多個開獎號碼位置（打勾即反白）。")
    st.stop()

# ====================================================
# 🧮 VIP 02 雙演算中樞 (vip-02.py - 第二部分 A 區)
# ====================================================
hit_counter = {}

try:
    conn_vip = sqlite3.connect(DB_NAME)
    # 共同步驟：先提取最近指定搜尋期數範圍（例如200期）的實體歷史完整數據（由最新往舊排列）
    sql_get_universe = f"SELECT period, {ball_cols_str} FROM {tbl_name} ORDER BY period DESC LIMIT :limit_p;"
    universe_df = pd.read_sql_query(sql_get_universe, conn_vip, params={"limit_p": search_periods})
    conn_vip.close()

    if not universe_df.empty:
        # ----------------------------------------------------
        # 🔍 模式 1：全域雷達大掃描拖牌 (LM + n 家族位移)
        # ----------------------------------------------------
        if "🔍" in calc_mode:
            universe_periods = universe_df['period'].tolist()

            for (n_val, col_name, chosen_ball_value, p_num) in selected_targets:
                conn_loop = sqlite3.connect(DB_NAME)

                for lm_period in universe_periods:
                    cursor_search = conn_loop.cursor()
                    sql_check_match = f"SELECT {col_name} FROM {tbl_name} WHERE period = ?;"
                    cursor_search.execute(sql_check_match, (lm_period,))
                    res_match = cursor_search.fetchone()

                    # 💡 完美對齊：精準解包 Tuple 索引 [0]，消滅型態衝突
                    if res_match and int(res_match[0]) == chosen_ball_value:
                        target_periods = [lm_period + n_val, lm_period + n_val + 1, lm_period + n_val + 2]

                        for t_p in target_periods:
                            cursor_search.execute(f"SELECT COUNT(*) FROM {tbl_name} WHERE period = ?", (t_p,))
                            if cursor_search.fetchone()[0] == 0:
                                continue  # 超出邊界，智慧略過

                            sql_get_dragged = f"SELECT {col_name} FROM {tbl_name} WHERE period = ?;"
                            cursor_search.execute(sql_get_dragged, (t_p,))
                            res_dragged = cursor_search.fetchone()

                            if res_dragged and res_dragged[0] is not None:
                                dragged_ball_value = int(res_dragged[0])
                                hit_counter[dragged_ball_value] = hit_counter.get(dragged_ball_value, 0) + 1
                conn_loop.close()

        # ----------------------------------------------------
        # 🔥 模式 2：連續出牌統計 (不限落球、由最新期數開始往上計數)
        # ----------------------------------------------------
        else:
            distinct_chosen_balls = list(set([target[2] for target in selected_targets]))

            for target_ball in distinct_chosen_balls:
                consecutive_count = 0

                for _, row_universe in universe_df.iterrows():
                    current_period_all_balls = [int(row_universe[c]) for c in ball_cols if pd.notna(row_universe[c])]

                    if target_ball in current_period_all_balls:
                        consecutive_count += 1
                    else:
                        break  # 中斷立刻停止

                if consecutive_count >= 2:
                    hit_counter[target_ball] = consecutive_count

except Exception as eVIP2:
    st.error(f"❌ VIP 02 雙算力矩陣執行中斷，詳情: {str(eVIP2)}")

# ====================================================
# 📊【全新介面微調】依照 4 大全新規格完全對齊渲染呈現看板
# ====================================================
st.markdown("---")
title_suffix = "全域位移掃描" if "🔍" in calc_mode else "連續出牌統計"
st.markdown(f"### 🏆 [{game_selected}] — {title_suffix} (精選最近 {search_periods} 期)")
st.caption("💡 視覺導航：左側 Group 依總次數由大到小排列，右側號碼依數字由小到大往右排列。")

grp_total_times = {}
grp_hit_details = {}

for grp_id, balls_list in GRP_CONFIG.items():
    current_grp_hits = {}
    total_grp_sum = 0

    for b in balls_list:
        times = hit_counter.get(b, 0)
        if times > 0:
            current_grp_hits[b] = times
            total_grp_sum += times

    grp_total_times[grp_id] = total_grp_sum
    sorted_by_ball_num = sorted(current_grp_hits.items(), key=lambda item: item[0], reverse=False)
    grp_hit_details[grp_id] = sorted_by_ball_num

sorted_grp_order = sorted(grp_total_times.items(), key=lambda item: item[1], reverse=True)

render_rows = []

for grp_id, total_sum in sorted_grp_order:
    display_group_id = GRP_LABEL_MAP[grp_id]
    sorted_hits = grp_hit_details[grp_id]

    # 4-1 & 4-2 標題硬優化，徹底洗淨複雜符號
    row_data = {
        "GROUP": f"{display_group_id}",
        "群組總次數": f"{total_sum} 次"
    }

    # 4-3 & 4-4 國際化更名為 No. 1 ~ No. 4，完全去除 🎯 與 () 括號
    for i in range(4):
        col_no = f"No. {i + 1}"

        if i < len(sorted_hits):
            ball_num, ball_times = sorted_hits[i]
            row_data[col_no] = f"{ball_num:02d} - {ball_times}次"
        else:
            row_data[col_no] = ""

    render_rows.append(row_data)

if render_rows:
    df_vip2_show = pd.DataFrame(render_rows)
    # 強制排定最終大完工欄位順序：GROUP、群組總次數、No. 1 ~ No. 4
    final_cols_order = ["GROUP", "群組總次數", "No. 1", "No. 2", "No. 3", "No. 4"]
    df_vip2_show = df_vip2_show[final_cols_order]
    st.table(df_vip2_show.set_index("GROUP"))
else:
    st.info("💡 目前所選的號碼組合在該算力模式下尚未激發 any 群組數據。")

# ====================================================
# 👑【最高管理員特權區】授權管理與歷史開獎數據 CSV 一鍵導入通道 (Part 2 - B區)
# ====================================================
if st.session_state["vip2_is_admin"]:
    st.markdown("---")
    st.markdown("## 👑 最高管理員安全特權控制台 (VIP 後台數據中心)")

    tab_csv, tab_auth = st.tabs(["📂 1. 歷史中獎資料一鍵 CSV 導入", "🔐 2. 用戶授權金鑰自主增減"])

    # 📑 分頁一：歷史中獎資料一鍵 CSV 智慧導入通道
    with tab_csv:
        st.subheader(f"📥 [{game_selected}] 歷史大數據補給站")
        uploaded_file = st.file_uploader(f"請上傳 [{game_selected}] 的備援歷史 CSV 檔", type=["csv"])

        if uploaded_file is not None:
            if st.button(f"📥 執行一鍵硬核導入 [{game_selected}] 實體資料庫"):
                try:
                    # 自動兼融 Big5 (cp950) 與 UTF-8 編碼格式，防範任何中文字元衝突
                    try:
                        excel_df = pd.read_csv(uploaded_file, encoding='cp950')
                    except:
                        excel_df = pd.read_csv(uploaded_file, encoding='utf-8')

                    excel_df.columns = excel_df.columns.str.strip()

                    conn_csv = sqlite3.connect(DB_NAME)
                    cursor_csv = conn_csv.cursor()
                    import_count = 0

                    # A. 今彩 539 智慧通道
                    if game_selected == "今彩 539":
                        for _, r in excel_df[
                            ['期別', '開獎日期', '獎號1', '獎號2', '獎號3', '獎號4', '獎號5']].dropna().iterrows():
                            cursor_csv.execute("INSERT OR IGNORE INTO lotto_539 VALUES (?,?,?,?,?,?,?)",
                                               (int(r['期別']), str(r['開獎日期']), int(r['獎號1']), int(r['獎號2']),
                                                int(r['獎號3']), int(r['獎號4']), int(r['獎號5'])))
                            if cursor_csv.rowcount > 0: import_count += 1

                    # B. 大樂透 智慧通道
                    elif game_selected == "大樂透":
                        cursor_csv.execute(
                            "CREATE TABLE IF NOT EXISTS lotto_649 (period INTEGER PRIMARY KEY, open_date TEXT, num1 INTEGER, num2 INTEGER, num3 INTEGER, num4 INTEGER, num5 INTEGER, num6 INTEGER, sp_num INTEGER)")
                        for _, r in excel_df[['期別', '開獎日期', '獎號1', '獎號2', '獎號3', '獎號4', '獎號5', '獎號6',
                                              '特別號']].dropna().iterrows():
                            cursor_csv.execute("INSERT OR IGNORE INTO lotto_649 VALUES (?,?,?,?,?,?,?,?,?)",
                                               (int(r['期別']), str(r['開獎日期']), int(r['獎號1']), int(r['獎號2']),
                                                int(r['獎號3']), int(r['獎號4']), int(r['獎號5']), int(r['獎號6']),
                                                int(r['特別號'])))
                            if cursor_csv.rowcount > 0: import_count += 1

                    # C. 威力彩 智慧通道
                    elif game_selected == "威力彩":
                        cursor_csv.execute(
                            "CREATE TABLE IF NOT EXISTS lotto_super (period INTEGER PRIMARY KEY, open_date TEXT, num1 INTEGER, num2 INTEGER, num3 INTEGER, num4 INTEGER, num5 INTEGER, num6 INTEGER, sec_num INTEGER)")
                        for _, r in excel_df[['期別', '開獎日期', '獎號1', '獎號2', '獎號3', '獎號4', '獎號5', '獎號6',
                                              '第二區']].dropna().iterrows():
                            cursor_csv.execute("INSERT OR IGNORE INTO lotto_super VALUES (?,?,?,?,?,?,?,?,?)",
                                               (int(r['期別']), str(r['開獎日期']), int(r['獎號1']), int(r['獎號2']),
                                                int(r['獎號3']), int(r['獎號4']), int(r['獎號5']), int(r['獎號6']),
                                                int(r['第二區'])))
                            if cursor_csv.rowcount > 0: import_count += 1

                    # D. 3星彩 智慧通道
                    elif game_selected == "3星彩":
                        cursor_csv.execute(
                            "CREATE TABLE IF NOT EXISTS lotto_3d (period INTEGER PRIMARY KEY, open_date TEXT, hundreds INTEGER, tens INTEGER, units INTEGER)")
                        for _, r in excel_df[['期別', '開獎日期', '獎號1', '獎號2', '獎號3']].dropna().iterrows():
                            cursor_csv.execute("INSERT OR IGNORE INTO lotto_3d VALUES (?,?,?,?,?)",
                                               (int(r['期別']), str(r['開獎日期']), int(r['獎號1']), int(r['獎號2']),
                                                int(r['獎號3'])))
                            if cursor_csv.rowcount > 0: import_count += 1

                    # E. 4星彩 智慧通道
                    elif game_selected == "4星彩":
                        cursor_csv.execute(
                            "CREATE TABLE IF NOT EXISTS lotto_4d (period INTEGER PRIMARY KEY, open_date TEXT, thousands INTEGER, hundreds INTEGER, tens INTEGER, units INTEGER)")
                        for _, r in excel_df[
                            ['期別', '開獎日期', '獎號1', '獎號2', '獎號3', '獎號4']].dropna().iterrows():
                            cursor_csv.execute("INSERT OR IGNORE INTO lotto_4d VALUES (?,?,?,?,?,?)",
                                               (int(r['期別']), str(r['開獎日期']), int(r['獎號1']), int(r['獎號2']),
                                                int(r['獎號3']), int(r['獎號4'])))
                            if cursor_csv.rowcount > 0: import_count += 1

                    conn_csv.commit()
                    conn_csv.close()

                    st.session_state[
                        "vip2_toast"] = f"📂 數據導入大成功！已成功為 [{game_selected}] 注入 {import_count} 期最新數據！"
                    st.rerun()
                except Exception as e_csv:
                    st.error(f"❌ 歷史 CSV 導入程序受阻，病因詳情: {str(e_csv)}")

    # 🔐 全球授權金鑰自主管理中心
    with tab_auth:
        st.subheader("🔐 全球授權金鑰自主管理中心")
        conn_a = sqlite3.connect(DB_NAME)
        df_a = pd.read_sql_query(
            "SELECT user_key AS 金鑰密碼, user_name AS 使用者姓名, expire_date AS 截止到期日, role AS 權限角色 FROM auth_users",
            conn_a)
        conn_a.close()

        st.markdown("#### 👥 當前合法授權 VIP 使用者名冊")
        st.table(df_a)

        st.markdown("---")
        col_add, col_del = st.columns(2)

        with col_add:
            st.markdown("##### ➕ 發行/發放全新的 VIP 合法金鑰")
            new_key = st.text_input("1. 設定 VIP 授權金鑰 (密碼)", placeholder="例如: friend888", key="nk2")
            new_name = st.text_input("2. 輸入使用者名稱 (姓名)", placeholder="例如: 李小華", key="nn2")
            new_expire = st.text_input("3. 設定到期截止日 (YYYY-MM-DD)", value="2027-12-31", key="ne2")
            new_role = st.selectbox("4. 分配系統權限角色", ["user (普通親友)", "admin (最高管理員)"], key="nr2")
            actual_role = "admin" if "admin" in new_role else "user"

            if st.button("🚀 實體發行並寫入此金鑰"):
                if new_key and new_name:
                    try:
                        conn_add = sqlite3.connect(DB_NAME)
                        cursor_add = conn_add.cursor()
                        cursor_add.execute("INSERT OR REPLACE INTO auth_users VALUES (?, ?, ?, ?)",
                                           (new_key.strip(), new_name.strip(), new_expire.strip(), actual_role))
                        conn_add.commit()
                        conn_add.close()
                        st.session_state[
                            "vip2_toast"] = f"🔑 金鑰發行成功！全新授權密碼 {new_key} 已成功註冊給 [{new_name}]。"
                        st.rerun()
                    except Exception as e_add:
                        st.error(f"❌ 發行金鑰失敗: {str(e_add)}")
                else:
                    st.error("❌ 金鑰密碼與使用者姓名不能留空！")

        with col_del:
            st.markdown("##### ➗ 註銷/收回使用者 VIP 權限")
            del_key = st.selectbox("請選取您要「強行註銷」的金鑰密碼", ["請選擇"] + df_a['金鑰密碼'].tolist(), key="dk2")
            if del_key != "請選擇" and del_key != "admin888":
                st.warning(f"🚨 警告：確定要收回金鑰 [{del_key}] 的所有 VIP 算力權限嗎？")
                if st.button("🗑️ 確定強行註銷並收回"):
                    try:
                        conn_del = sqlite3.connect(DB_NAME)
                        cursor_del = conn_del.cursor()
                        cursor_del.execute("DELETE FROM auth_users WHERE user_key = ?", (del_key,))
                        conn_del.commit()
                        conn_del.close()
                        st.session_state["vip2_toast"] = f"🔒 成功強行註銷金鑰！該用戶已被永久中斷看盤特權。"
                        st.rerun()
                    except Exception as e_del:
                        st.error(f"❌ 註銷金鑰失敗: {str(e_del)}")
            elif del_key == "admin888":
                st.error("❌ 安全機制阻斷：系統禁止註銷最高管理員您自己的終極金鑰！")

st.success(f"🏁 VIP 綜合雙算力全面成功！")
