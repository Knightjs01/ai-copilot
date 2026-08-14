"""Deliberately "basic" per the user's own choice over the alternative (DNS TXT record / email-
link domain verification): no outbound check of any kind, just a denylist of the free/consumer
email providers a real company wouldn't be signing up from. A company's email_domain and
is_verified_domain are computed once, at signup, from the owner's email — see
CompanyService.create_company. There is deliberately no self-serve re-verification flow yet;
an org that ends up unverified needs a manual/support-driven fix, which is an acceptable gap for
a "basic gate," not a full identity-verification product."""

_FREE_EMAIL_DOMAINS = frozenset(
    {
        "gmail.com",
        "googlemail.com",
        "yahoo.com",
        "yahoo.co.uk",
        "outlook.com",
        "hotmail.com",
        "hotmail.co.uk",
        "live.com",
        "msn.com",
        "icloud.com",
        "me.com",
        "mac.com",
        "aol.com",
        "protonmail.com",
        "proton.me",
        "mail.com",
        "gmx.com",
        "gmx.net",
        "yandex.com",
        "yandex.ru",
        "zoho.com",
        "fastmail.com",
        "tutanota.com",
        "qq.com",
        "163.com",
        "126.com",
    }
)


def extract_email_domain(email: str) -> str:
    return email.rsplit("@", 1)[-1].strip().lower()


def is_verified_domain(email_domain: str) -> bool:
    return email_domain not in _FREE_EMAIL_DOMAINS
