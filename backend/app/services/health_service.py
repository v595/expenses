from app.models.user import count_users


def get_health_status():
    return {
        "status": "ok",
        "database": "connected",
        "user_count": count_users(),
    }
