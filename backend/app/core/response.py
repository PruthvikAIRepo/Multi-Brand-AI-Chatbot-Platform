from typing import Any


def api_response(
    data: Any = None,
    message: str = "Success",
    meta: dict | None = None,
) -> dict:
    """Consistent API response format: {data, message, meta}"""
    response = {
        "data": data,
        "message": message,
    }
    if meta:
        response["meta"] = meta
    return response


def paginated_response(
    data: list,
    total: int,
    page: int,
    per_page: int,
    message: str = "Success",
) -> dict:
    """Consistent paginated response format."""
    return {
        "data": data,
        "message": message,
        "meta": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
        },
    }
