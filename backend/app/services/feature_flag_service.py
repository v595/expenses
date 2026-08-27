from app.models import activity_log as activity_log_model
from app.models import feature_flag as feature_flag_model


def list_flags():
    return feature_flag_model.list_flags()


def is_enabled(key):
    """Called by any future feature (AI Assistant, Net Worth, etc.) before
    doing real work, so a disabled flag is enforced server-side rather than
    just hidden in the UI."""
    return feature_flag_model.is_enabled(key)


def set_enabled(key, enabled, actor_id):
    if not isinstance(enabled, bool):
        raise ValueError("enabled must be true or false")
    flag = feature_flag_model.set_enabled(key, enabled)
    if flag is None:
        raise ValueError("Unknown feature flag")
    activity_log_model.log(
        actor_id,
        f"{'Enabled' if enabled else 'Disabled'} feature flag",
        key,
        entity_type="feature_flag",
        entity_id=None,
    )
    return flag
