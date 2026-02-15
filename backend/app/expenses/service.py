from typing import Dict, List, Optional
from ..core.database import get_db_connection

# (Keep get_summary, get_monthly, get_payment_methods etc. as they are)
def get_summary(user: Dict) -> Dict:
    # ... code from previous correct version
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT SUM(trans_amount) as total_amount, COUNT(*) as total_count, MIN(trans_date) as earliest_date, MAX(trans_date) as latest_date FROM personal_expenses_final WHERE deleted_at = 0")
            result = cursor.fetchone()
            total_amount = result['total_amount'] or 0
            total_count = result['total_count'] or 0
            avg_amount = total_amount / total_count if total_count > 0 else 0
            return {"total_amount": total_amount, "total_count": total_count, "avg_amount": avg_amount, "earliest_date": str(result['earliest_date']), "latest_date": str(result['latest_date'])}
    finally:
        conn.close()

def get_monthly(user: Dict) -> List[Dict]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT trans_year as year, SUBSTRING_INDEX(trans_month, '-', -1) as month, COUNT(*) as transaction_count, SUM(trans_amount) as monthly_total FROM personal_expenses_final WHERE deleted_at = 0 GROUP BY trans_year, trans_month ORDER BY trans_month DESC LIMIT 12"
            cursor.execute(sql)
            results = cursor.fetchall()
            output = []
            for row in results:
                count = row['transaction_count']
                total = row['monthly_total']
                output.append({"year": str(row['year']), "month": str(row['month']), "transaction_count": count, "monthly_total": total, "avg_transaction": total / count if count > 0 else 0})
            return output
    finally:
        conn.close()

def get_categories(user: Dict) -> List[Dict]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Corrected SQL to group by both main and sub category
            sql = """
                SELECT 
                    pet.trans_type_name,
                    pet.trans_sub_type_name,
                    COUNT(pef.id) as count,
                    SUM(pef.trans_amount) as total_amount
                FROM personal_expenses_final pef
                JOIN personal_expenses_type pet ON pef.trans_code = pet.trans_code AND pef.trans_sub_code = pet.trans_sub_code
                WHERE pef.deleted_at = 0
                GROUP BY pet.trans_type_name, pet.trans_sub_type_name
                ORDER BY total_amount DESC
            """
            cursor.execute(sql)
            results = cursor.fetchall()
            
            # Calculate total for percentage calculation
            total_expense_for_cats = sum(row['total_amount'] for row in results)

            output = []
            for row in results:
                count = row['count']
                total = row['total_amount']
                output.append({
                    "trans_type_name": row['trans_type_name'],
                    "trans_sub_type_name": row['trans_sub_type_name'],
                    "count": count,
                    "total_amount": total,
                    "avg_amount": total / count if count > 0 else 0,
                    "percentage": (total / total_expense_for_cats) * 100 if total_expense_for_cats > 0 else 0
                })
            return output
    finally:
        conn.close()

def get_payment_methods(user: Dict) -> List[Dict]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT 
                    pay_account as pay_account,
                    COUNT(*) as usage_count,
                    SUM(trans_amount) as total_spent
                FROM personal_expenses_final
                WHERE deleted_at = 0
                GROUP BY pay_account
                ORDER BY total_spent DESC
            """
            cursor.execute(sql)
            results = cursor.fetchall()
            output = []
            for row in results:
                count = row['usage_count']
                total = row['total_spent']
                output.append({"pay_account": row['pay_account'] or "Unknown", "usage_count": count, "total_spent": total, "avg_per_transaction": total / count if count > 0 else 0})
            return output
    finally:
        conn.close()

def get_timeline(user: Dict) -> List[Dict]:
    # ... code from previous correct version
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT trans_date as date, SUM(trans_amount) as daily_total, COUNT(*) as transaction_count FROM personal_expenses_final WHERE deleted_at = 0 GROUP BY trans_date ORDER BY trans_date DESC LIMIT 50"
            cursor.execute(sql)
            return cursor.fetchall()
    finally:
        conn.close()

def get_stardust_data(user: Dict) -> Dict:
    # ... code from previous correct version
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql_categories = "SELECT pet.trans_type_name, SUM(pef.trans_amount) AS total_amount FROM personal_expenses_final AS pef JOIN personal_expenses_type AS pet ON pef.trans_code = pet.trans_code WHERE pef.deleted_at = 0 GROUP BY pet.trans_type_name"
            cursor.execute(sql_categories)
            categories = cursor.fetchall()
            sql_transactions = "SELECT pef.id, pef.trans_event, pef.trans_amount, pet.trans_type_name FROM personal_expenses_final AS pef JOIN personal_expenses_type AS pet ON pef.trans_code = pet.trans_code WHERE pef.deleted_at = 0"
            cursor.execute(sql_transactions)
            transactions = cursor.fetchall()
            nodes, links = [], []
            for cat in categories:
                nodes.append({"id": cat['trans_type_name'], "name": cat['trans_type_name'], "symbolSize": max(10, min(80, (cat['total_amount'] / 500))), "value": cat['total_amount'], "category": cat['trans_type_name'], "itemStyle": {"opacity": 0.9}, "label": {"show": True, "fontSize": 16, "fontWeight": 'bold'}})
            for tx in transactions:
                nodes.append({"id": f"tx-{tx['id']}", "name": tx['trans_event'] or '消费', "symbolSize": max(3, min(30, (tx['trans_amount'] / 50))), "value": tx['trans_amount'], "category": tx['trans_type_name'], "itemStyle": {"opacity": 0.7}})
                links.append({"source": f"tx-{tx['id']}", "target": tx['trans_type_name']})
            stardust_categories = [{"trans_type_name": cat['trans_type_name']} for cat in categories]
            return {"nodes": nodes, "links": links, "categories": stardust_categories}
    finally:
        conn.close()
