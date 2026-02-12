# backend/app/expenses/service.py
from typing import Dict, List
from app.core.database import get_db_connection

def get_summary(user: Dict) -> Dict:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT COALESCE(SUM(trans_amount), 0) AS total_amount, COALESCE(COUNT(id), 0) AS total_count, COALESCE(AVG(trans_amount), 0) AS avg_amount, MIN(trans_datetime) AS earliest_date, MAX(trans_datetime) AS latest_date FROM personal_expenses_final WHERE deleted_at = 0"
            if user['username'] != 'admin':
                sql += " AND user_id = %s"
                cursor.execute(sql, (user['id'],))
            else:
                cursor.execute(sql)
            result = cursor.fetchone()
            if result:
                if result.get('earliest_date'): result['earliest_date'] = result['earliest_date'].strftime("%Y-%m-%d")
                if result.get('latest_date'): result['latest_date'] = result['latest_date'].strftime("%Y-%m-%d")
            return result
    finally:
        conn.close()

def get_monthly(user: Dict) -> List[Dict]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT trans_year AS year, trans_month AS month, COUNT(id) AS transaction_count, SUM(trans_amount) AS monthly_total, AVG(trans_amount) AS avg_transaction FROM personal_expenses_final WHERE deleted_at = 0"
            params = ()
            if user['username'] != 'admin':
                sql += " AND user_id = %s"
                params = (user['id'],)
            sql += " GROUP BY trans_year, trans_month ORDER BY trans_year DESC, trans_month DESC"
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conn.close()

def get_categories(user: Dict) -> List[Dict]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT pet.trans_type_name, pet.trans_sub_type_name, COUNT(pef.id) AS count, SUM(pef.trans_amount) AS total_amount, AVG(pef.trans_amount) AS avg_amount FROM personal_expenses_final AS pef JOIN personal_expenses_type AS pet ON pef.trans_code = pet.trans_code AND pef.trans_sub_code = pet.trans_sub_code WHERE pef.deleted_at = 0"
            params = ()
            if user['username'] != 'admin':
                sql += " AND pef.user_id = %s"
                params = (user['id'],)
            sql += " GROUP BY pet.trans_type_name, pet.trans_sub_type_name ORDER BY total_amount DESC"
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conn.close()

def get_payment_methods(user: Dict) -> List[Dict]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT pay_account, COUNT(id) AS usage_count, SUM(trans_amount) AS total_spent, AVG(trans_amount) AS avg_per_transaction FROM personal_expenses_final WHERE deleted_at = 0"
            params = ()
            if user['username'] != 'admin':
                sql += " AND user_id = %s"
                params = (user['id'],)
            sql += " GROUP BY pay_account ORDER BY total_spent DESC"
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conn.close()

def get_timeline(user: Dict) -> List[Dict]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT trans_date AS date, SUM(trans_amount) AS daily_total, COUNT(id) AS transaction_count FROM personal_expenses_final WHERE deleted_at = 0"
            params = ()
            if user['username'] != 'admin':
                sql += " AND user_id = %s"
                params = (user['id'],)
            sql += " GROUP BY trans_date ORDER BY trans_date ASC"
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conn.close()

def get_stardust_data(user: Dict) -> Dict:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT pet.trans_type_name, pet.trans_sub_type_name, SUM(pef.trans_amount) AS total_amount FROM personal_expenses_final AS pef JOIN personal_expenses_type AS pet ON pef.trans_code = pet.trans_code AND pef.trans_sub_code = pet.trans_sub_code WHERE pef.deleted_at = 0"
            params = ()
            if user['username'] != 'admin':
                sql += " AND pef.user_id = %s"
                params = (user['id'],)
            sql += " GROUP BY pet.trans_type_name, pet.trans_sub_type_name"
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            nodes, links, categories = [], [], []
            root_name = "Total Expenses"
            total_sum = sum(row['total_amount'] for row in rows)
            nodes.append({"id": "root", "name": root_name, "symbolSize": 50, "value": total_sum, "category": 0, "label": {"show": True}})
            categories.append({"name": root_name})

            cat_map = {}
            cat_set = set()
            cat_index = 1
            for row in rows:
                cat_name = row['trans_type_name']
                if cat_name not in cat_set:
                    cat_id = f"cat_{cat_name}"
                    nodes.append({"id": cat_id, "name": cat_name, "symbolSize": 30, "value": 0, "category": cat_index, "label": {"show": True}})
                    links.append({"source": "root", "target": cat_id})
                    categories.append({"name": cat_name})
                    cat_map[cat_name] = len(nodes) - 1
                    cat_set.add(cat_name)
                    cat_index += 1
            
            for row in rows:
                cat_name = row['trans_type_name']
                sub_cat_name = row['trans_sub_type_name']
                amount = float(row['total_amount'])
                cat_node_idx = cat_map[cat_name]
                nodes[cat_node_idx]["value"] += amount
                sub_cat_id = f"sub_{cat_name}_{sub_cat_name}"
                nodes.append({"id": sub_cat_id, "name": sub_cat_name, "symbolSize": 10 + (amount / total_sum) * 40, "value": amount, "category": nodes[cat_node_idx]["category"], "label": {"show": amount > (total_sum * 0.01)}})
                links.append({"source": f"cat_{cat_name}", "target": sub_cat_id})

            for node in nodes:
                if node["id"].startswith("cat_"):
                    node["symbolSize"] = 20 + (node["value"] / total_sum) * 60
            
            return {"nodes": nodes, "links": links, "categories": categories}
    finally:
        conn.close()
