import pytest

from app.services import messaging
from app.services.messaging import msg91, templates, twilio, wa_link
from app.services.messaging.base import MessagingError, normalize_phone


@pytest.fixture(autouse=True)
def clear_provider_env(monkeypatch):
    """The stub drivers read their credentials from the environment, so make
    sure a developer's real (or leftover) values can't affect these tests."""
    for key in twilio.REQUIRED_ENV_VARS + msg91.REQUIRED_ENV_VARS + ("MESSAGING_DRIVER",):
        monkeypatch.delenv(key, raising=False)


def test_wa_link_is_the_zero_config_default():
    assert messaging.get_driver() is wa_link
    assert wa_link.is_configured() is True


def test_messaging_driver_env_var_selects_the_driver(monkeypatch):
    monkeypatch.setenv("MESSAGING_DRIVER", "twilio")
    assert messaging.get_driver() is twilio

    monkeypatch.setenv("MESSAGING_DRIVER", "MSG91")
    assert messaging.get_driver() is msg91

    monkeypatch.setenv("MESSAGING_DRIVER", "carrier-pigeon")
    with pytest.raises(MessagingError) as excinfo:
        messaging.get_driver()
    assert "Unknown messaging driver" in excinfo.value.message


def test_phone_normalization():
    assert normalize_phone("+91 98765 43210") == "+919876543210"
    assert normalize_phone("(044) 2233-4455") == "04422334455"
    assert normalize_phone("  9876543210  ") == "9876543210"
    assert normalize_phone("no digits here") is None
    assert normalize_phone(None) is None


def test_wa_link_strips_spaces_plus_and_punctuation_from_the_number():
    link = wa_link.build_link("+91 98765-43210", "Hi")
    assert link.startswith("https://wa.me/919876543210?text=")


def test_wa_link_url_encodes_the_message():
    link = wa_link.build_link("919876543210", "Hi Ravi, ₹1,500.00 is pending. Pay? Thanks & bye/ok")

    _, _, query = link.partition("?text=")
    # Spaces, the rupee sign and every reserved character are percent-encoded,
    # so nothing in the body can terminate the query string.
    assert " " not in query
    assert "%20" in query
    assert "%E2%82%B9" in query  # ₹
    assert "?" not in query
    assert "&" not in query
    assert "/" not in query
    assert "%2C" in query  # ,


def test_wa_link_send_reports_pending_and_needs_the_user_to_press_send():
    result = wa_link.send("+919876543210", "Hi")
    assert result["driver"] == "wa_link"
    # Nothing has actually been sent — the caller must confirm separately.
    assert result["status"] == "pending"
    assert result["requires_user_action"] is True
    assert result["link"].startswith("https://wa.me/919876543210?text=")


def test_wa_link_requires_a_phone_number():
    with pytest.raises(MessagingError):
        wa_link.build_link("", "Hi")


def test_twilio_stub_raises_a_not_configured_error():
    assert twilio.is_configured() is False
    with pytest.raises(MessagingError) as excinfo:
        twilio.send("+919876543210", "Hi")

    message = excinfo.value.message
    assert "Twilio is not configured" in message
    for env_var in twilio.REQUIRED_ENV_VARS:
        assert env_var in message


def test_msg91_stub_raises_a_not_configured_error():
    assert msg91.is_configured() is False
    with pytest.raises(MessagingError) as excinfo:
        msg91.send("+919876543210", "Hi")

    message = excinfo.value.message
    assert "MSG91 is not configured" in message
    for env_var in msg91.REQUIRED_ENV_VARS:
        assert env_var in message


def test_stub_drivers_still_refuse_once_credentials_are_present(monkeypatch):
    """Credentials alone aren't enough — the outbound call is still a TODO, so
    the driver says so rather than silently pretending it sent something."""
    for env_var in twilio.REQUIRED_ENV_VARS:
        monkeypatch.setenv(env_var, "placeholder")

    assert twilio.is_configured() is True
    with pytest.raises(MessagingError) as excinfo:
        twilio.send("+919876543210", "Hi")
    assert "not implemented yet" in excinfo.value.message


def test_default_reminder_template_and_override():
    default = templates.reminder_message("Ravi", 1500, "Shop")
    assert default == (
        "Hi Ravi, this is a reminder that ₹1,500.00 is pending against your "
        "account with Shop. Please arrange the payment. Thank you."
    )

    custom = templates.reminder_message("Ravi", 1500, "Shop", "Please pay {amount} today")
    assert custom == "Please pay 1,500.00 today"

    # A caller message that isn't a template is passed through untouched.
    assert templates.reminder_message("Ravi", 1, "Shop", "50% off {") == "50% off {"
