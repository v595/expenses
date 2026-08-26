from app.models import activity_log as activity_log_model

MAX_PATH_LENGTH = 200


def log_pageview(user_id, path):
    if not isinstance(path, str) or not path.strip():
        raise ValueError("Path is required")
    path = path.strip()[:MAX_PATH_LENGTH]
    activity_log_model.log(user_id, "Viewed page", path)
