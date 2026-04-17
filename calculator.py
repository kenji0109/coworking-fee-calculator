"""
料金計算ロジック - Workplace Hub Tokyo 料金シミュレーター
"""

import pandas as pd


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """data/ 配下のCSV3つを読み込んでDataFrameで返す"""
    rooms = pd.read_csv("data/rooms.csv", encoding="utf-8-sig")
    options = pd.read_csv("data/options.csv", encoding="utf-8-sig")
    discount_rules = pd.read_csv("data/discount_rules.csv", encoding="utf-8-sig")
    return rooms, options, discount_rules


def calculate_room_fee(
    room: dict | pd.Series,
    hours: float,
    is_holiday: bool,
    use_daily_pack: bool,
) -> dict:
    """
    部屋の利用料金を計算する。

    Returns:
        {
            "base_fee": 基本料金,
            "discount": 割引額,
            "final": 最終料金,
            "applied_discount": 適用割引名（str）,
        }
    """
    if use_daily_pack:
        price = int(room["price_daily_pack"])
        return {
            "base_fee": price,
            "discount": 0,
            "final": price,
            "applied_discount": "日額パック",
        }

    # 時間課金
    unit_price = int(room["price_holiday_hourly"] if is_holiday else room["price_weekday_hourly"])
    base_fee = unit_price * hours

    # 利用時間に応じた割引
    if hours >= 6:
        discount_rate = 0.20
        applied_discount = "6時間以上割引 (20%)"
    elif hours >= 3:
        discount_rate = 0.10
        applied_discount = "3時間以上割引 (10%)"
    else:
        discount_rate = 0.0
        applied_discount = "なし"

    discount = base_fee * discount_rate
    final = base_fee - discount

    return {
        "base_fee": int(base_fee),
        "discount": int(discount),
        "final": int(final),
        "applied_discount": applied_discount,
    }


def calculate_option_fee(
    option: dict | pd.Series,
    quantity: int,
    days: int,
    people: int,
) -> int:
    """
    オプション料金を計算する。

    unit="per_day"    : price * quantity * days
    unit="per_person" : price * people * days
    """
    price = int(option["price"])
    unit = option["unit"]

    if unit == "per_person":
        return price * people * days
    else:  # per_day
        return price * quantity * days


def apply_membership_discount(subtotal: int, membership_type: str) -> dict:
    """
    会員種別による割引を適用する。

    membership_type:
        "non_member" - 割引なし
        "monthly"    - 20% オフ
        "corporate"  - 30% オフ

    Returns:
        {"discount": 割引額, "final": 最終金額}
    """
    rates = {
        "non_member": 0.0,
        "monthly": 0.20,
        "corporate": 0.30,
    }
    rate = rates.get(membership_type, 0.0)
    discount = int(subtotal * rate)
    return {
        "discount": discount,
        "final": subtotal - discount,
    }


def calculate_total(
    room_selections: list[dict],
    option_selections: list[dict],
    membership_type: str,
    is_holiday: bool,
) -> dict:
    """
    全ての計算を統合して見積もりを返す。

    room_selections の各要素:
        {
            "room": pd.Series,      # rooms.csv の1行
            "hours": float,
            "use_daily_pack": bool,
        }

    option_selections の各要素:
        {
            "option": pd.Series,    # options.csv の1行
            "quantity": int,
            "days": int,
            "people": int,
        }

    Returns:
        {
            "rooms":               [各部屋の明細リスト],
            "options":             [各オプションの明細リスト],
            "subtotal":            小計,
            "membership_discount": 会員割引額,
            "total":               最終合計,
        }
    """
    rooms_detail = []
    room_total = 0

    for sel in room_selections:
        fee = calculate_room_fee(
            sel["room"],
            sel["hours"],
            is_holiday,
            sel["use_daily_pack"],
        )
        rooms_detail.append(
            {
                "部屋名": sel["room"]["room_name"],
                "利用形態": "日額パック" if sel["use_daily_pack"] else f"{sel['hours']}時間",
                "基本料金": fee["base_fee"],
                "時間割引": -fee["discount"],
                "適用割引": fee["applied_discount"],
                "小計": fee["final"],
            }
        )
        room_total += fee["final"]

    options_detail = []
    option_total = 0

    for sel in option_selections:
        amount = calculate_option_fee(
            sel["option"],
            sel["quantity"],
            sel["days"],
            sel["people"],
        )
        options_detail.append(
            {
                "オプション名": sel["option"]["option_name"],
                "単価": int(sel["option"]["price"]),
                "数量": sel["quantity"],
                "日数": sel["days"],
                "人数": sel["people"],
                "小計": amount,
            }
        )
        option_total += amount

    subtotal = room_total + option_total
    membership = apply_membership_discount(subtotal, membership_type)

    return {
        "rooms": rooms_detail,
        "options": options_detail,
        "subtotal": subtotal,
        "membership_discount": membership["discount"],
        "total": membership["final"],
    }
