import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px
import plotly.graph_objects as go
import json
import os

# ページ設定
st.set_page_config(
    page_title="💰 家計簿アプリ",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# データファイル
DATA_FILE = "data.json"

# カテゴリ設定
EXPENSE_CATEGORIES = {
    "固定費": ["住居費", "光熱費", "通信費", "保険料", "ローン返済"],
    "変動費": ["食費", "日用品", "交通費", "医療費", "教育費", "娯楽費", "交際費", "その他"]
}
INCOME_CATEGORIES = ["給与（本人）", "給与（配偶者）", "賞与", "副業", "投資配当", "児童手当", "その他"]
PAYMENT_METHODS = ["現金", "クレジットカード", "口座引落", "電子マネー"]

# データ読み込み・保存
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return (
                pd.DataFrame(data.get("income", [])),
                pd.DataFrame(data.get("expense", [])),
                pd.DataFrame(data.get("budget", [])),
                pd.DataFrame(data.get("accounts", []))
            )
    return create_empty_data()

def create_empty_data():
    income = pd.DataFrame(columns=["日付", "項目", "金額", "メモ"])
    expense = pd.DataFrame(columns=["日付", "大分類", "中分類", "金額", "支払方法", "メモ"])
    budget = pd.DataFrame({
        "項目": ["食費", "日用品", "交通費", "娯楽費", "その他"],
        "月額予算": [50000, 10000, 15000, 20000, 10000]
    })
    accounts = pd.DataFrame({
        "口座名": ["メイン銀行", "貯蓄用"],
        "残高": [500000, 1000000]
    })
    return income, expense, budget, accounts

def save_data():
    data = {
        "income": st.session_state.income.to_dict(orient="records") if not st.session_state.income.empty else [],
        "expense": st.session_state.expense.to_dict(orient="records") if not st.session_state.expense.empty else [],
        "budget": st.session_state.budget.to_dict(orient="records") if not st.session_state.budget.empty else [],
        "accounts": st.session_state.accounts.to_dict(orient="records") if not st.session_state.accounts.empty else []
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

# 初期化
if "income" not in st.session_state:
    i, e, b, a = load_data()
    st.session_state.income = i
    st.session_state.expense = e
    st.session_state.budget = b
    st.session_state.accounts = a

# サイドバー
st.sidebar.title("💰 家計簿アプリ")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "メニュー",
    ["📊 ダッシュボード", "➕ 収入入力", "➖ 支出入力", "📋 予算設定", "🏦 口座管理", "📈 レポート"]
)

# ==================== ダッシュボード ====================
if page == "📊 ダッシュボード":
    st.title("📊 ダッシュボード")
    
    # 今月のデータをフィルタ
    today = date.today()
    current_month = today.strftime("%Y-%m")
    
    # サマリー計算
    income_total = st.session_state.income["金額"].sum() if not st.session_state.income.empty else 0
    expense_total = st.session_state.expense["金額"].sum() if not st.session_state.expense.empty else 0
    balance = income_total - expense_total
    
    # メトリクス表示
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💵 収入合計", f"¥{income_total:,.0f}")
    col2.metric("💸 支出合計", f"¥{expense_total:,.0f}")
    col3.metric("💰 収支", f"¥{balance:,.0f}", delta=f"¥{balance:,.0f}")
    
    account_total = st.session_state.accounts["残高"].sum() if not st.session_state.accounts.empty else 0
    col4.metric("🏦 総資産", f"¥{account_total:,.0f}")
    
    st.markdown("---")
    
    # グラフ
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 支出内訳")
        if not st.session_state.expense.empty:
            expense_by_cat = st.session_state.expense.groupby("中分類")["金額"].sum().reset_index()
            fig = px.pie(expense_by_cat, values="金額", names="中分類", hole=0.4)
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("支出データがありません")
    
    with col2:
        st.subheader("📈 予算vs実績")
        if not st.session_state.budget.empty and not st.session_state.expense.empty:
            budget_df = st.session_state.budget.copy()
            actual = st.session_state.expense.groupby("中分類")["金額"].sum()
            budget_df["実績"] = budget_df["項目"].map(actual).fillna(0)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(name="予算", x=budget_df["項目"], y=budget_df["月額予算"], marker_color="lightblue"))
            fig.add_trace(go.Bar(name="実績", x=budget_df["項目"], y=budget_df["実績"], marker_color="coral"))
            fig.update_layout(barmode="group", height=350)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("予算・支出データがありません")

# ==================== 収入入力 ====================
elif page == "➕ 収入入力":
    st.title("➕ 収入入力")
    
    with st.form("income_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            input_date = st.date_input("📅 日付", date.today())
            item = st.selectbox("📝 項目", INCOME_CATEGORIES)
        with col2:
            amount = st.number_input("💴 金額", min_value=0, step=1000, format="%d")
            memo = st.text_input("📌 メモ")
        
        submitted = st.form_submit_button("✅ 登録", use_container_width=True)
        
        if submitted and amount > 0:
            new_row = pd.DataFrame({
                "日付": [str(input_date)],
                "項目": [item],
                "金額": [amount],
                "メモ": [memo]
            })
            st.session_state.income = pd.concat([st.session_state.income, new_row], ignore_index=True)
            save_data()
            st.success(f"✅ {item}: ¥{amount:,} を登録しました！")
            st.rerun()
    
    st.markdown("---")
    st.subheader("📋 収入履歴")
    if not st.session_state.income.empty:
        st.dataframe(st.session_state.income.sort_values("日付", ascending=False), use_container_width=True)
    else:
        st.info("収入データがありません")

# ==================== 支出入力 ====================
elif page == "➖ 支出入力":
    st.title("➖ 支出入力")
    
    with st.form("expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            input_date = st.date_input("📅 日付", date.today())
            major_cat = st.selectbox("📁 大分類", list(EXPENSE_CATEGORIES.keys()))
            minor_cat = st.selectbox("📂 中分類", EXPENSE_CATEGORIES[major_cat])
        with col2:
            amount = st.number_input("💴 金額", min_value=0, step=100, format="%d")
            payment = st.selectbox("💳 支払方法", PAYMENT_METHODS)
            memo = st.text_input("📌 メモ")
        
        submitted = st.form_submit_button("✅ 登録", use_container_width=True)
        
        if submitted and amount > 0:
            new_row = pd.DataFrame({
                "日付": [str(input_date)],
                "大分類": [major_cat],
                "中分類": [minor_cat],
                "金額": [amount],
                "支払方法": [payment],
                "メモ": [memo]
            })
            st.session_state.expense = pd.concat([st.session_state.expense, new_row], ignore_index=True)
            save_data()
            st.success(f"✅ {minor_cat}: ¥{amount:,} を登録しました！")
            st.rerun()
    
    st.markdown("---")
    st.subheader("📋 支出履歴")
    if not st.session_state.expense.empty:
        st.dataframe(st.session_state.expense.sort_values("日付", ascending=False), use_container_width=True)
    else:
        st.info("支出データがありません")

# ==================== 予算設定 ====================
elif page == "📋 予算設定":
    st.title("📋 予算設定")
    
    edited_budget = st.data_editor(
        st.session_state.budget,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "項目": st.column_config.TextColumn("項目", width="medium"),
            "月額予算": st.column_config.NumberColumn("月額予算", format="¥%d", min_value=0)
        }
    )
    
    if st.button("💾 保存", use_container_width=True):
        st.session_state.budget = edited_budget
        save_data()
        st.success("✅ 予算を保存しました！")

# ==================== 口座管理 ====================
elif page == "🏦 口座管理":
    st.title("🏦 口座管理")
    
    edited_accounts = st.data_editor(
        st.session_state.accounts,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "口座名": st.column_config.TextColumn("口座名", width="medium"),
            "残高": st.column_config.NumberColumn("残高", format="¥%d", min_value=0)
        }
    )
    
    if st.button("💾 保存", use_container_width=True):
        st.session_state.accounts = edited_accounts
        save_data()
        st.success("✅ 口座情報を保存しました！")
    
    st.markdown("---")
    total = edited_accounts["残高"].sum()
    st.metric("🏦 総資産", f"¥{total:,.0f}")

# ==================== レポート ====================
elif page == "📈 レポート":
    st.title("📈 月次レポート")
    
    if st.session_state.expense.empty and st.session_state.income.empty:
        st.info("データがありません。収入・支出を入力してください。")
    else:
        # 収支サマリー
        income_total = st.session_state.income["金額"].sum() if not st.session_state.income.empty else 0
        expense_total = st.session_state.expense["金額"].sum() if not st.session_state.expense.empty else 0
        
        st.subheader("📊 収支サマリー")
        col1, col2, col3 = st.columns(3)
        col1.metric("収入", f"¥{income_total:,.0f}")
        col2.metric("支出", f"¥{expense_total:,.0f}")
        col3.metric("収支", f"¥{income_total - expense_total:,.0f}")
        
        # カテゴリ別支出
        if not st.session_state.expense.empty:
            st.markdown("---")
            st.subheader("📋 カテゴリ別支出")
            cat_summary = st.session_state.expense.groupby(["大分類", "中分類"])["金額"].sum().reset_index()
            st.dataframe(cat_summary, use_container_width=True)

# フッター
st.sidebar.markdown("---")
st.sidebar.caption("© 2026 家計簿アプリ")
