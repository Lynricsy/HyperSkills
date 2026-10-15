FREE_SHIPPING_THRESHOLD_CENTS = 5000
INTERNATIONAL_FLAT_CENTS = 2500
DOMESTIC_RATE_CENTS = 799


def shipping_cents(subtotal_cents: int, is_member: bool, country: str) -> int:
    """Shipping fee in cents for one order.

    Free domestic shipping at or above the threshold is a member benefit (ISSUE-640).
    """
    if country != "US":
        return INTERNATIONAL_FLAT_CENTS
    if is_member and subtotal_cents >= FREE_SHIPPING_THRESHOLD_CENTS:
        return 0
    return DOMESTIC_RATE_CENTS
