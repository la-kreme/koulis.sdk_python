"""Tests for HTTP status → exception mapping."""

from unittest.mock import MagicMock

from koulis._http import map_response_to_exception
from koulis.exceptions import (
    KoulisAPIError,
    KoulisAuthError,
    KoulisConflict,
    KoulisExpiredHold,
    KoulisNotFound,
    KoulisValidationError,
)


def _response(status: int, body=None):
    response = MagicMock()
    response.status_code = status
    response.is_success = 200 <= status < 300
    if isinstance(body, dict):
        response.json.return_value = body
        response.text = str(body)
    else:
        response.json.side_effect = ValueError("not json")
        response.text = body or ""
    return response


def test_400_maps_to_validation():
    exc = map_response_to_exception(_response(400, {"message": "bad input"}))
    assert isinstance(exc, KoulisValidationError)
    assert exc.status_code == 400


def test_401_maps_to_auth():
    exc = map_response_to_exception(_response(401, {"message": "missing token"}))
    assert isinstance(exc, KoulisAuthError)


def test_403_maps_to_auth():
    exc = map_response_to_exception(_response(403, {"message": "forbidden"}))
    assert isinstance(exc, KoulisAuthError)


def test_404_maps_to_not_found():
    exc = map_response_to_exception(_response(404, {"message": "missing"}))
    assert isinstance(exc, KoulisNotFound)


def test_409_maps_to_conflict():
    exc = map_response_to_exception(_response(409, {"message": "no capacity"}))
    assert isinstance(exc, KoulisConflict)


def test_410_maps_to_expired_hold():
    exc = map_response_to_exception(_response(410, {"message": "expired"}))
    assert isinstance(exc, KoulisExpiredHold)


def test_500_maps_to_base_error():
    exc = map_response_to_exception(_response(500, {"message": "server error"}))
    assert isinstance(exc, KoulisAPIError)
    assert not isinstance(exc, (KoulisConflict, KoulisNotFound))


def test_non_json_body_handled():
    exc = map_response_to_exception(_response(502, "bad gateway"))
    assert isinstance(exc, KoulisAPIError)
    assert "502" in str(exc)


def test_error_field_fallback():
    exc = map_response_to_exception(_response(400, {"error": "fallback"}))
    assert "fallback" in str(exc)


def test_body_preserved():
    body = {"message": "x", "extra": "field"}
    exc = map_response_to_exception(_response(400, body))
    assert exc.body == body