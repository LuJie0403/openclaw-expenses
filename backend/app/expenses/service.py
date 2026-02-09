
from typing import List, Dict
from ..core.database import get_db_connection

def get_summary(user_id: str) -> Dict:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT
                COALESCE(SUM(trans_amount), 0) AS total_amount,
                COALESCE(COUNT(id), 0) AS total_count,
                COALESCE(AVG(trans_amount), 0) AS avg_amount,
                MIN(trans_datetime) AS earliest_date,
                MAX(trans_datetime) AS latest_date
            FROM personal_expenses_final
            WHERE created_by = %s
            """
            cursor.execute(sql, (user_id,))
            result = cursor.fetchone()
            if result and result['earliest_date']:
                result['earliest_date'] = result['earliest_date'].strftime("%Y-%m-%d")
            if result and result['latest_date']:
                result['latest_date'] = result['latest_date'].strftime("%Y-%m-%d")
            return result
    finally:
        conn.close()

def get_monthly(user_id: str) -> List[Dict]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT
                trans_year AS year,
                trans_month AS month,
                COUNT(id) AS transaction_count,
                SUM(trans_amount) AS monthly_total,
                AVG(trans_amount) AS avg_transaction
            FROM personal_expenses_final
            WHERE created_by = %s
            GROUP BY trans_year, trans_month
            ORDER BY trans_year DESC, trans_month DESC
            """
            cursor.execute(sql, (user_id,))
            return cursor.fetchall()
    finally:
        conn.close()

def get_categories(user_id: str) -> List[Dict]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT
                pet.trans_type_name,
                pet.trans_sub_type_name,
                COUNT(pef.id) AS count,
                SUM(pef.trans_amount) AS total_amount,
                AVG(pef.trans_amount) AS avg_amount
            FROM personal_expenses_final AS pef
            JOIN personal_expenses_type AS pet
                ON pef.trans_code = pet.trans_code AND pef.trans_sub_code = pet.trans_sub_code
            WHERE pef.created_by = %s
            GROUP BY pet.trans_type_name, pet.trans_sub_type_name
            ORDER BY total_amount DESC
            """
            cursor.execute(sql, (user_id,))
            return cursor.fetchall()
    finally:
        conn.close()

def get_payment_methods(user_id: str) -> List[Dict]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT
                pay_account,
                COUNT(id) AS usage_count,
                SUM(trans_amount) AS total_spent,
                AVG(trans_amount) AS avg_per_transaction
            FROM personal_expenses_final
            WHERE created_by = %s
            GROUP BY pay_account
            ORDER BY total_spent DESC
            """
            cursor.execute(sql, (user_id,))
            return cursor.fetchall()
    finally:
        conn.close()

def get_timeline(user_id: str) -> List[Dict]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT
                trans_date AS date,
                SUM(trans_amount) AS daily_total,
                COUNT(id) AS transaction_count
            FROM personal_expenses_final
            WHERE created_by = %s
            GROUP BY trans_date
            ORDER BY trans_date ASC
            """
            cursor.execute(sql, (user_id,))
            return cursor.fetchall()
    finally:
        conn.close()
