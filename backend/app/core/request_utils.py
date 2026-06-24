"""Helpers for extracting request metadata (e.g. client IP for audit/rate-limit).

Behind a reverse proxy (Nginx/Dokploy/ALB) request.client.host is the proxy IP,
so we prefer the left-most X-Forwarded-For entry (the original client)."""

from fastapi import Request


def get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # "client, proxy1, proxy2" -> take the original client
        return forwarded.split(",")[0].strip() or None
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip() or None
    return request.client.host if request.client else None
