"""Code executed inside the PyRIT subprocess (`launcher.py`).

Modules here other than `request_body.py` import `pyrit`, which is installed only
in the PyRIT venv — never import them from the FastAPI process.
"""
