"""
Application logging setup.

Uvicorn often leaves the root logger at WARNING, while SQLAlchemy ``echo=True`` uses its own
logger — so ``logging.info`` from ``app.*`` can be invisible. We attach a handler to the
customer-auth subtree so OTP / SMTP diagnostics always reach stdout (e.g. Docker logs).
"""

import logging
import sys

_FMT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def configure_customer_auth_logging() -> None:
    """Route INFO+ logs from customer-auth modules to stdout (single handler, no duplicate root spam)."""
    base = "app.modules.customer_auth"
    parent = logging.getLogger(base)
    parent.setLevel(logging.INFO)
    if parent.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter(_FMT))
    parent.addHandler(handler)
    parent.propagate = False
