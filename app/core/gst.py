"""India GST compliance validators."""

from __future__ import annotations

import re
from typing import Optional

# 15-char GSTIN: 2 digit state + 10 PAN + entity + Z + checksum
GSTIN_RE = re.compile(
    r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
)
PAN_RE = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")
HSN_RE = re.compile(r"^[0-9]{4,8}$")


def normalize_gstin(value: Optional[str]) -> Optional[str]:
    if value is None or str(value).strip() == "":
        return None
    gstin = str(value).strip().upper()
    if not GSTIN_RE.match(gstin):
        raise ValueError(
            "Invalid GSTIN. Expected 15 characters, e.g. 27AABCU9603R1ZM"
        )
    return gstin


def normalize_pan(value: Optional[str]) -> Optional[str]:
    if value is None or str(value).strip() == "":
        return None
    pan = str(value).strip().upper()
    if not PAN_RE.match(pan):
        raise ValueError("Invalid PAN. Expected format ABCDE1234F")
    return pan


def validate_gst_rates(
    *,
    enable_gst: bool,
    cgst_rate: Optional[float],
    sgst_rate: Optional[float],
    igst_rate: Optional[float],
    is_inter_state: bool = False,
) -> None:
    """Validate CGST/SGST/IGST rate configuration for Indian GST."""
    if not enable_gst:
        return

    rates = [r for r in (cgst_rate, sgst_rate, igst_rate) if r is not None]
    if not rates:
        return

    for rate in rates:
        if rate < 0 or rate > 100:
            raise ValueError("GST rates must be between 0 and 100")

    if is_inter_state:
        if igst_rate is None or igst_rate <= 0:
            raise ValueError("Inter-state supply requires IGST rate")
    else:
        if (cgst_rate or 0) + (sgst_rate or 0) <= 0 and (igst_rate or 0) <= 0:
            raise ValueError("Intra-state supply requires CGST+SGST or IGST rate")


def validate_hsn(value: Optional[str]) -> Optional[str]:
    if value is None or str(value).strip() == "":
        return None
    hsn = str(value).strip()
    if not HSN_RE.match(hsn):
        raise ValueError("Invalid HSN/SAC code (4–8 digits)")
    return hsn
