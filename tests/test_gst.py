"""GST validation tests."""

import pytest

from app.core.gst import normalize_gstin, normalize_pan, validate_gst_rates, validate_hsn


def test_normalize_gstin_valid():
    assert normalize_gstin("27aabCU9603r1zm") == "27AABCU9603R1ZM"


def test_normalize_gstin_invalid():
    with pytest.raises(ValueError, match="Invalid GSTIN"):
        normalize_gstin("INVALID")


def test_normalize_pan_valid():
    assert normalize_pan("abcde1234f") == "ABCDE1234F"


def test_normalize_pan_invalid():
    with pytest.raises(ValueError, match="Invalid PAN"):
        normalize_pan("12345")


def test_validate_gst_rates_intra_state():
    validate_gst_rates(
        enable_gst=True,
        cgst_rate=9.0,
        sgst_rate=9.0,
        igst_rate=None,
    )


def test_validate_hsn():
    assert validate_hsn("996331") == "996331"
