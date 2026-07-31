"""Builds the Garak RestGenerator config for an arbitrary target URL.

Garak's `rest` generator needs to be told the request/response shape of the target
API. By default we assume every target exposes a fixed, simple contract:

    POST <target_url>
    Body:     {"message": "<attack text>"}
    Response: {"response": "<model text>"}   (HTTP 200, JSON)

If your target doesn't speak this contract, either put an adapter in front of it, or
override `request_template` / `response_field` on the `ScanRequest` to match its actual
request body shape and response field name.
"""

from app.config import (
    DEFAULT_REQUEST_TEMPLATE,
    DEFAULT_REQUEST_TIMEOUT_SECONDS,
    DEFAULT_RESPONSE_FIELD,
    TIMEOUT_SKIP_STATUS_CODE,
)
from app.schemas import ScanRequest


def build_rest_generator_config(scan_request: ScanRequest) -> dict:
    return {
        "rest": {
            "RestGenerator": {
                "name": "atlas-scan-target",
                "uri": scan_request.target_url,
                "method": "post",
                "headers": {
                    "Content-Type": "application/json",
                },
                "req_template_json_object": scan_request.request_template or DEFAULT_REQUEST_TEMPLATE,
                "response_json": True,
                "response_json_field": scan_request.response_field or DEFAULT_RESPONSE_FIELD,
                "request_timeout": scan_request.request_timeout or DEFAULT_REQUEST_TIMEOUT_SECONDS,
                "skip_codes": [TIMEOUT_SKIP_STATUS_CODE],
            }
        }
    }
