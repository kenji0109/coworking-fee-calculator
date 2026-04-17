"""
Workplace Hub Tokyo 料金シミュレーター
架空のコワーキングスペースを題材にした学習・ポートフォリオ用 Streamlit アプリ
"""

import datetime

import jpholiday
import pandas as pd
import streamlit as st

from calculator import (
    calculate_total,
    load_data,
)

st.set_page_config(
    page_title="Workplace Hub Tokyo 料金シミュレーター",
    layout="wide",
)


@st.cache_data
def get_data():
    return load_data()


rooms_df, options_df, discount_rules_df = get_data()

# ---------------------------------------------------------------------------
# タイトル
# ---------------------------------------------------------------------------
st.title("🏢 Workplace Hub Tokyo 料金シミュレーター")
st.caption("架空のコワーキングスペースの料金計算アプリ（個人学習用）")
st.divider()

# ---------------------------------------------------------------------------
# サイドバー
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("利用条件の設定")

    st.subheader("📅 利用日")
    use_date = st.date_input(
        "利用日を選択",
        value=datetime.date.today(),
        label_visibility="collapsed",
    )

    # 土日 or 祝日 → 休日料金
    is_weekend = use_date.weekday() >= 5
    is_holiday_day = jpholiday.is_holiday(use_date)
    is_holiday = is_weekend or is_holiday_day

    if is_holiday:
        holiday_reason = "祝日" if is_holiday_day else "土日"
        st.info(f"🗓️ 選択日は{holiday_reason}のため、**休日料金**が適用されます。")
    else:
        st.success("🗓️ 選択日は平日のため、**平日料金**が適用されます。")

    st.divider()

    st.subheader("👤 会員種別")
    membership_label = st.selectbox(
        "会員種別を選択",
        options=["非会員", "月額会員 (20%オフ)", "法人契約 (30%オフ)"],
        label_visibility="collapsed",
    )
    membership_map = {
        "非会員": "non_member",
        "月額会員 (20%オフ)": "monthly",
        "法人契約 (30%オフ)": "corporate",
    }
    membership_type = membership_map[membership_label]

# ---------------------------------------------------------------------------
# STEP 1: 部屋の選択
# ---------------------------------------------------------------------------
st.subheader("STEP 1　部屋の選択")

selected_room_names = st.multiselect(
    "利用する部屋を選択してください（複数選択可）",
    options=rooms_df["room_name"].tolist(),
    placeholder="部屋を選択...",
)

# ---------------------------------------------------------------------------
# STEP 2: 各部屋の利用設定
# ---------------------------------------------------------------------------
room_selections: list[dict] = []

if selected_room_names:
    st.divider()
    st.subheader("STEP 2　各部屋の利用設定")

    for room_name in selected_room_names:
        room = rooms_df[rooms_df["room_name"] == room_name].iloc[0]

        with st.expander(f"🚪 {room_name}　（{room['floor']} / 定員 {room['capacity']}名）", expanded=True):
            billing_mode = st.radio(
                "利用形態",
                options=["時間課金", "日額パック"],
                horizontal=True,
                key=f"mode_{room_name}",
            )
            use_daily_pack = billing_mode == "日額パック"

            if use_daily_pack:
                hours = 0.0
                fee_preview = int(room["price_daily_pack"])
                st.write(f"日額パック料金: **¥{fee_preview:,}**")
            else:
                hours = st.number_input(
                    "利用時間（時間）",
                    min_value=0.5,
                    max_value=12.0,
                    value=2.0,
                    step=0.5,
                    key=f"hours_{room_name}",
                )
                unit_price = int(room["price_holiday_hourly"] if is_holiday else room["price_weekday_hourly"])
                base = unit_price * hours
                if hours >= 6:
                    discount_rate, label = 0.20, "6時間以上割引 (20%)"
                elif hours >= 3:
                    discount_rate, label = 0.10, "3時間以上割引 (10%)"
                else:
                    discount_rate, label = 0.0, ""

                discount = int(base * discount_rate)
                fee_preview = int(base) - discount

                col1, col2 = st.columns(2)
                col1.write(f"基本料金: ¥{int(base):,}")
                if discount:
                    col2.write(f"割引（{label}）: -¥{discount:,}")
                st.write(f"この部屋の小計: **¥{fee_preview:,}**")

            room_selections.append(
                {
                    "room": room,
                    "hours": hours,
                    "use_daily_pack": use_daily_pack,
                }
            )

# ---------------------------------------------------------------------------
# STEP 3: オプションの選択
# ---------------------------------------------------------------------------
st.divider()
st.subheader("STEP 3　オプションの選択")

option_selections: list[dict] = []

days = st.number_input("利用日数", min_value=1, max_value=30, value=1, step=1)

categories = options_df["category"].unique().tolist()
for category in categories:
    st.markdown(f"**{category}**")
    cat_options = options_df[options_df["category"] == category]

    cols = st.columns(len(cat_options))
    for col, (_, opt_row) in zip(cols, cat_options.iterrows()):
        with col:
            selected = st.checkbox(opt_row["option_name"], key=f"opt_{opt_row['option_id']}")
            if selected:
                if opt_row["unit"] == "per_person":
                    people = st.number_input(
                        "人数",
                        min_value=1,
                        max_value=500,
                        value=10,
                        step=1,
                        key=f"people_{opt_row['option_id']}",
                    )
                    quantity = 1
                else:
                    people = 1
                    quantity = st.number_input(
                        "数量",
                        min_value=1,
                        max_value=10,
                        value=1,
                        step=1,
                        key=f"qty_{opt_row['option_id']}",
                    )

                option_selections.append(
                    {
                        "option": opt_row,
                        "quantity": quantity,
                        "days": days,
                        "people": people,
                    }
                )

# ---------------------------------------------------------------------------
# STEP 4: 見積もり結果
# ---------------------------------------------------------------------------
st.divider()
st.subheader("STEP 4　見積もり結果")

if not room_selections:
    st.info("STEP 1 で部屋を選択すると、ここに見積もりが表示されます。")
else:
    result = calculate_total(room_selections, option_selections, membership_type, is_holiday)

    # 部屋明細
    if result["rooms"]:
        st.markdown("##### 🚪 部屋料金")
        rooms_table = pd.DataFrame(result["rooms"])
        # 数値列を通貨表示
        for col in ["基本料金", "時間割引", "小計"]:
            rooms_table[col] = rooms_table[col].apply(lambda x: f"¥{x:,}")
        st.dataframe(rooms_table, use_container_width=True, hide_index=True)

    # オプション明細
    if result["options"]:
        st.markdown("##### 🔧 オプション料金")
        opt_table = pd.DataFrame(result["options"])
        opt_table["単価"] = opt_table["単価"].apply(lambda x: f"¥{x:,}")
        opt_table["小計"] = opt_table["小計"].apply(lambda x: f"¥{x:,}")
        st.dataframe(opt_table, use_container_width=True, hide_index=True)

    st.divider()

    # 金額サマリー
    col_sum1, col_sum2, col_sum3 = st.columns(3)
    col_sum1.metric("小計", f"¥{result['subtotal']:,}")

    if result["membership_discount"] > 0:
        col_sum2.metric(
            f"会員割引（{membership_label}）",
            f"-¥{result['membership_discount']:,}",
            delta=f"-¥{result['membership_discount']:,}",
            delta_color="normal",
        )
    else:
        col_sum2.metric("会員割引", "¥0")

    col_sum3.metric("**合計金額**", f"¥{result['total']:,}")

# ---------------------------------------------------------------------------
# フッター
# ---------------------------------------------------------------------------
st.divider()
st.caption(
    "💡 このアプリは架空の施設を題材にした学習・ポートフォリオ用プロジェクトです。"
    "実在する施設とは関係ありません。"
)
