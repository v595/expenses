from app.models import activity_log as activity_log_model
from app.models import system_setting as system_setting_model
from app.services.settings_service import ALLOWED_CURRENCIES

KNOWN_SETTINGS = ("app_name", "default_currency", "maintenance_mode")


def get_all():
    values = system_setting_model.get_all()
    return {key: values.get(key) for key in KNOWN_SETTINGS}


def update_settings(data, actor_id):
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object")

    updated = {}

    if "app_name" in data:
        app_name = data["app_name"]
        if not isinstance(app_name, str) or not app_name.strip():
            raise ValueError("Application name cannot be empty")
        updated["app_name"] = app_name.strip()

    if "default_currency" in data:
        currency = data["default_currency"]
        if currency not in ALLOWED_CURRENCIES:
            raise ValueError(f"Default currency must be one of {', '.join(ALLOWED_CURRENCIES)}")
        updated["default_currency"] = currency

    if "maintenance_mode" in data:
        maintenance_mode = data["maintenance_mode"]
        if not isinstance(maintenance_mode, bool):
            raise ValueError("maintenance_mode must be true or false")
        updated["maintenance_mode"] = "true" if maintenance_mode else "false"

    for key, value in updated.items():
        system_setting_model.set_value(key, value)

    if updated:
        activity_log_model.log(
            actor_id, "Updated system settings", ", ".join(updated.keys()), entity_type="system_setting"
        )

    return get_all()
