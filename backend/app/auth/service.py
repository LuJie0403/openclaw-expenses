from ..core.config import settings
from ..core.database import get_db_connection
from ..core.security import verify_password


def get_user_by_username(username: str):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            user_table = settings.AUTH_USER_TABLE
            # Table name is validated in config via parse_sql_identifier.
            sql = (
                "SELECT id, username, email, hashed_password, full_name, is_active, created_at "
                f"FROM {user_table} WHERE username = %s"
            )
            cursor.execute(sql, (username,))
            user_data = cursor.fetchone()
            if user_data:
                return {
                    "id": user_data["id"],
                    "username": user_data["username"],
                    "email": user_data["email"],
                    "hashed_password": user_data["hashed_password"],
                    "full_name": user_data["full_name"],
                    "is_active": user_data["is_active"],
                    "created_at": user_data["created_at"],
                }
            return None
    finally:
        conn.close()


def authenticate_user(username: str, password: str):
    user = get_user_by_username(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user
