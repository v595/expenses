"""Default subject/body for outbound emails."""


def password_reset_email(name, reset_url):
    subject = "Reset your Hisaab password"
    body = (
        f"Hi {name},\n\n"
        "We got a request to reset your Hisaab password. Click the link below "
        "to choose a new one — it's valid for 30 minutes:\n\n"
        f"{reset_url}\n\n"
        "If you didn't ask for this, you can safely ignore this email; your "
        "password won't change.\n\n"
        "— Hisaab"
    )
    return subject, body
