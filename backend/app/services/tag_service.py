from app.models import tag as tag_model

MAX_TAG_LENGTH = 30
MAX_TAGS_PER_TRANSACTION = 10


def get_tags(user_id):
    return tag_model.get_tags_by_user(user_id)


def resolve_tag_names(user_id, names):
    """Turns a list of freeform tag name strings into tag row ids, creating
    any tag that doesn't exist yet for this user."""
    if names is None:
        return []
    if not isinstance(names, list):
        raise ValueError("Tags must be a list of strings")
    if len(names) > MAX_TAGS_PER_TRANSACTION:
        raise ValueError(f"A transaction can have at most {MAX_TAGS_PER_TRANSACTION} tags")

    ids = []
    seen = set()
    for raw in names:
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError("Each tag must be non-empty text")
        name = raw.strip().lower()
        if len(name) > MAX_TAG_LENGTH:
            raise ValueError(f"Tags must be {MAX_TAG_LENGTH} characters or fewer")
        if name in seen:
            continue
        seen.add(name)
        tag = tag_model.get_or_create_tag(user_id, name)
        ids.append(tag["id"])
    return ids


def delete_tag(tag_id, user_id):
    tag_model.delete_tag(tag_id, user_id)
