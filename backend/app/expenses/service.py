
from typing import Any, Dict, List, Tuple

from ..core.database import get_db_connection


def _build_user_filter(username: str, user_id: str, column: str) -> Tuple[str, Tuple[str, ...]]:
    if username == "admin":
        return "", ()
    return f" AND {column} = %s", (str(user_id),)


def get_summary(user_id: str, username: str) -> Dict[str, Any]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            user_filter, params = _build_user_filter(username, user_id, "user_id")
            sql = f"""
            SELECT
                COALESCE(SUM(trans_amount), 0) AS total_amount,
                COALESCE(COUNT(id), 0) AS total_count,
                COALESCE(AVG(trans_amount), 0) AS avg_amount,
                MIN(trans_datetime) AS earliest_date,
                MAX(trans_datetime) AS latest_date
            FROM personal_expenses_final
            WHERE deleted_at = 0
            {user_filter}
            """
            cursor.execute(sql, params)
            result = cursor.fetchone() or {}

            earliest = result.get("earliest_date")
            latest = result.get("latest_date")
            if earliest:
                result["earliest_date"] = earliest.strftime("%Y-%m-%d")
            if latest:
                result["latest_date"] = latest.strftime("%Y-%m-%d")

            return result
    finally:
        conn.close()


def get_monthly(user_id: str, username: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            user_filter, params = _build_user_filter(username, user_id, "user_id")
            sql = f"""
            SELECT
                trans_year AS year,
                trans_month AS month,
                COUNT(id) AS transaction_count,
                SUM(trans_amount) AS monthly_total,
                AVG(trans_amount) AS avg_transaction
            FROM personal_expenses_final
            WHERE deleted_at = 0
            {user_filter}
            GROUP BY trans_year, trans_month
            ORDER BY trans_year DESC, trans_month DESC
            """
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conn.close()


def get_categories(user_id: str, username: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            user_filter, params = _build_user_filter(username, user_id, "pef.user_id")
            sql = f"""
            SELECT
                pet.trans_type_name,
                pet.trans_sub_type_name,
                COUNT(pef.id) AS count,
                SUM(pef.trans_amount) AS total_amount,
                AVG(pef.trans_amount) AS avg_amount
            FROM personal_expenses_final AS pef
            JOIN personal_expenses_type AS pet
                ON pef.trans_code = pet.trans_code AND pef.trans_sub_code = pet.trans_sub_code
            WHERE pef.deleted_at = 0
            {user_filter}
            GROUP BY pet.trans_type_name, pet.trans_sub_type_name
            ORDER BY total_amount DESC
            """
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conn.close()


def get_payment_methods(user_id: str, username: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            user_filter, params = _build_user_filter(username, user_id, "user_id")
            sql = f"""
            SELECT
                pay_account,
                COUNT(id) AS usage_count,
                SUM(trans_amount) AS total_spent,
                AVG(trans_amount) AS avg_per_transaction
            FROM personal_expenses_final
            WHERE deleted_at = 0
            {user_filter}
            GROUP BY pay_account
            ORDER BY total_spent DESC
            """
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conn.close()


def get_timeline(user_id: str, username: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            user_filter, params = _build_user_filter(username, user_id, "user_id")
            sql = f"""
            SELECT
                trans_date AS date,
                SUM(trans_amount) AS daily_total,
                COUNT(id) AS transaction_count
            FROM personal_expenses_final
            WHERE deleted_at = 0
            {user_filter}
            GROUP BY trans_date
            ORDER BY trans_date ASC
            """
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conn.close()


def get_stardust(user_id: str, username: str) -> Dict[str, Any]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            user_filter, params = _build_user_filter(username, user_id, "pef.user_id")
            sql = f"""
            SELECT
                pet.trans_type_name,
                pet.trans_sub_type_name,
                SUM(pef.trans_amount) AS total_amount
            FROM personal_expenses_final AS pef
            JOIN personal_expenses_type AS pet
                ON pef.trans_code = pet.trans_code AND pef.trans_sub_code = pet.trans_sub_code
            WHERE pef.deleted_at = 0
            {user_filter}
            GROUP BY pet.trans_type_name, pet.trans_sub_type_name
            """
            cursor.execute(sql, params)
            rows = cursor.fetchall()
    finally:
        conn.close()

    nodes: List[Dict[str, Any]] = []
    links: List[Dict[str, str]] = []
    categories: List[Dict[str, str]] = []

    root_name = "Total Expenses"
    total_sum = sum(float(row.get("total_amount") or 0) for row in rows)
    safe_total = total_sum if total_sum > 0 else 1.0

    nodes.append(
        {
            "id": "root",
            "name": root_name,
            "symbolSize": 50,
            "value": total_sum,
            "category": 0,
            "label": {"show": True},
        }
    )
    categories.append({"name": root_name})

    category_node_index: Dict[str, int] = {}
    next_category_id = 1
    for row in rows:
        cat_name = row.get("trans_type_name") or "未分类"
        if cat_name in category_node_index:
            continue

        cat_id = f"cat_{cat_name}"
        nodes.append(
            {
                "id": cat_id,
                "name": cat_name,
                "symbolSize": 30,
                "value": 0.0,
                "category": next_category_id,
                "label": {"show": True},
            }
        )
        links.append({"source": "root", "target": cat_id})
        categories.append({"name": cat_name})
        category_node_index[cat_name] = len(nodes) - 1
        next_category_id += 1

    for row in rows:
        cat_name = row.get("trans_type_name") or "未分类"
        sub_cat_name = row.get("trans_sub_type_name") or "其他"
        amount = float(row.get("total_amount") or 0)

        cat_node_idx = category_node_index[cat_name]
        nodes[cat_node_idx]["value"] += amount

        sub_cat_id = f"sub_{cat_name}_{sub_cat_name}"
        nodes.append(
            {
                "id": sub_cat_id,
                "name": sub_cat_name,
                "symbolSize": 10 + (amount / safe_total) * 40,
                "value": amount,
                "category": nodes[cat_node_idx]["category"],
                "label": {"show": amount > (safe_total * 0.01)},
            }
        )
        links.append({"source": f"cat_{cat_name}", "target": sub_cat_id})

    for node in nodes:
        if node["id"].startswith("cat_"):
            node["symbolSize"] = 20 + (float(node["value"]) / safe_total) * 60

    return {"nodes": nodes, "links": links, "categories": categories}
