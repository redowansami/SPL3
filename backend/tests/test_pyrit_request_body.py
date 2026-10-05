"""Tests for the pure request/response helpers used inside the PyRIT subprocess.

These don't import `pyrit`, so they run in the normal backend venv.
"""

import pytest

from app.services.pyrit.runtime.request_body import (
    extract_response,
    render_request_body,
    template_has_placeholder,
)


def test_render_replaces_placeholder_in_nested_structure():
    template = {"message": "$INPUT", "meta": {"tags": ["x", "$INPUT"]}, "n": 1}
    rendered = render_request_body(template, "hello")
    assert rendered == {"message": "hello", "meta": {"tags": ["x", "hello"]}, "n": 1}


def test_render_does_not_mutate_original_template():
    template = {"message": "$INPUT"}
    render_request_body(template, "hello")
    assert template == {"message": "$INPUT"}


def test_template_has_placeholder():
    assert template_has_placeholder({"a": {"b": "$INPUT"}})
    assert not template_has_placeholder({"a": {"b": "nope"}})


def test_extract_response_simple_field():
    assert extract_response({"response": "hi"}, "response") == "hi"


def test_extract_response_dotted_path_with_list_index():
    data = {"choices": [{"message": {"content": "hi there"}}]}
    assert extract_response(data, "choices.0.message.content") == "hi there"


def test_extract_response_missing_field_raises():
    with pytest.raises(KeyError):
        extract_response({"response": "hi"}, "nope")


def test_extract_response_coerces_non_string():
    assert extract_response({"response": 42}, "response") == "42"
