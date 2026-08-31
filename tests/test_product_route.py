"""Regression tests for product create error handling and CORS origins."""
import re

from fastapi import HTTPException as FastAPIHTTPException

from app.core.config import Settings
from app.modules.product import route as product_route


def test_product_route_binds_http_exception():
    """create_product must catch FastAPI HTTPException, not raise NameError."""
    assert product_route.HTTPException is FastAPIHTTPException


def test_http_exception_is_catchable_in_product_route():
    try:
        raise FastAPIHTTPException(status_code=403, detail="limit")
    except product_route.HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("HTTPException was not caught")


def test_cors_origin_regex_matches_admin_frontend():
    regex = re.compile(r"https://([a-zA-Z0-9-]+\.)*v11tech\.com")
    assert regex.fullmatch("https://pos.v11tech.com")
    assert regex.fullmatch("https://apipos.v11tech.com")
    assert regex.fullmatch("https://v11tech.com")
    assert regex.fullmatch("https://api.pos.v11tech.com")
    assert not regex.fullmatch("http://pos.v11tech.com")
    assert not regex.fullmatch("https://evil.com")


def test_production_cors_includes_pos_admin_origin():
    settings = Settings.model_construct(
        APP_ENV="production",
        CORS_ORIGINS=(
            "https://pos.v11tech.com,https://apipos.v11tech.com,"
            "https://posv11tech.web.app"
        ),
    )
    assert "https://pos.v11tech.com" in settings.cors_origins
    assert settings.cors_origin_regex is not None
    assert re.compile(settings.cors_origin_regex).fullmatch("https://pos.v11tech.com")
