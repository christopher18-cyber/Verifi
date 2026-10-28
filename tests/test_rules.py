from app.rules.checks import scan_rules


def ids(result):
    return {f["id"] for f in result["flags"]}


def test_fake_bank_alert_triggers_floor():
    r = scan_rules("GTBank Alert: Your account has been suspended. Verify your BVN and OTP "
                   "within 24 hours: http://gtb-secure-verify.xyz/login")
    assert r["hard_floor"]
    assert {"secret_request", "lookalike_link", "urgency", "account_threat"} <= ids(r)


def test_genuine_alert_is_not_flagged():
    r = scan_rules("Debit alert: N5,000.00 left your account on 24-Oct. "
                   "Never share your OTP or PIN with anyone, including bank staff.")
    assert not r["hard_floor"]
    assert r["protective_warning"]
    assert r["score"] == 0


def test_prize_and_fee_with_short_link():
    r = scan_rules("Congratulations! You have won N2,500,000. Pay a N5,000 processing fee "
                   "to claim your prize today: bit.ly/mtn-claim")
    assert {"prize", "advance_fee", "shortener_link"} <= ids(r)


def test_pidgin_otp_request():
    r = scan_rules("Oga, your account don block o. Send your OTP make we fit open am back.")
    assert r["hard_floor"]
    assert "account_threat" in ids(r)


def test_fake_relative_airtime():
    r = scan_rules("Mummy it's me, I lost my phone. Please send 20k airtime urgently.")
    assert {"airtime_request", "urgency"} <= ids(r)


def test_official_link_is_not_flagged():
    r = scan_rules("Your statement is ready: https://www.gtbank.com/statement")
    assert not any(f["id"].endswith("_link") for f in r["flags"])


def test_email_address_is_not_a_link():
    assert scan_rules("Write to support@gtbank.com for help")["links"] == []


def test_loan_app_threat():
    r = scan_rules("Your loan is overdue. Pay now or we will send your photo to everyone "
                   "in your contact list.")
    assert "contact_threat" in ids(r)