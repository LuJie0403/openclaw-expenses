

def get_stardust_data() -> Dict:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Query for categories (planets)
            sql_categories = """
                SELECT
                    pet.trans_type_name,
                    SUM(pef.trans_amount) AS total_amount
                FROM personal_expenses_final AS pef
                JOIN personal_expenses_type AS pet ON pef.trans_code = pet.trans_code
                WHERE pef.deleted_at = 0
                GROUP BY pet.trans_type_name
            """
            cursor.execute(sql_categories)
            categories = cursor.fetchall()

            # Query for individual transactions (stardust)
            sql_transactions = """
                SELECT
                    pef.id,
                    pef.trans_event,
                    pef.trans_amount,
                    pet.trans_type_name
                FROM personal_expenses_final AS pef
                JOIN personal_expenses_type AS pet ON pef.trans_code = pet.trans_code
                WHERE pef.deleted_at = 0
            """
            cursor.execute(sql_transactions)
            transactions = cursor.fetchall()

            # Format data for ECharts
            nodes = []
            links = []

            for cat in categories:
                nodes.append({
                    "id": cat['trans_type_name'],
                    "name": cat['trans_type_name'],
                    "symbolSize": max(10, min(80, (cat['total_amount'] / 500))),
                    "value": cat['total_amount'],
                    "category": cat['trans_type_name'],
                    "itemStyle": {"opacity": 0.9},
                    "label": {"show": True, "fontSize": 16, "fontWeight": 'bold'}
                })

            for tx in transactions:
                nodes.append({
                    "id": f"tx-{tx['id']}",
                    "name": tx['trans_event'] or '消费',
                    "symbolSize": max(3, min(30, (tx['trans_amount'] / 50))),
                    "value": tx['trans_amount'],
                    "category": tx['trans_type_name'],
                    "itemStyle": {"opacity": 0.7}
                })
                links.append({
                    "source": f"tx-{tx['id']}",
                    "target": tx['trans_type_name']
                })

            return {"nodes": nodes, "links": links, "categories": categories}
    finally:
        conn.close()
