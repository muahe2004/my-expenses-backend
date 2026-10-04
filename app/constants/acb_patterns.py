import re


AMOUNT_PATTERN = r"[+-]?[\d,.]+"

LATEST_TRANSACTION = re.compile(
    r"Latest transaction:\s*(?P<type>Debit|Credit)\s*"
    rf"(?P<amount>{AMOUNT_PATTERN})\s*VND",
    re.IGNORECASE,
)

ACCOUNT = re.compile(r"account\s+(?P<value>\d+)", re.IGNORECASE)

BALANCE = re.compile(
    r"Updated account balance:\s*(?P<value>[\d,.]+)\s*VND",
    re.IGNORECASE,
)

DESCRIPTION = re.compile(
    r"Content:\s*(?P<value>.+?)(?:\.|$)",
    re.IGNORECASE,
)

TRANSACTION_DATE = re.compile(
    r"up to\s+(?P<value>\d{2}/\d{2}/\d{4})",
    re.IGNORECASE,
)
