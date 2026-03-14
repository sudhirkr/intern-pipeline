"""Deploy URL checker — validates deployed URLs and measures response metrics."""
import time
import httpx
import logging

logger = logging.getLogger(__name__)


async def check_deployed_url(url: str) -> dict:
    """Check if a deployed URL is accessible. Returns response metrics.

    Returns:
        {
            "valid": bool,
            "status_code": int,
            "response_time_ms": int,
            "has_content": bool,
            "content_length": int,
            "content_type": str,
            "error": str | None
        }
    """
    url = url.strip().rstrip("/")

    # Normalize: add https:// if missing scheme
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    try:
        start = time.monotonic()
        async with httpx.AsyncClient(
            timeout=20.0,
            follow_redirects=True,
            headers={"User-Agent": "InternPipeline-Checker/1.0"},
        ) as client:
            resp = await client.get(url)
            elapsed_ms = int((time.monotonic() - start) * 1000)

            content = resp.text or ""
            content_length = len(content.encode("utf-8"))
            content_type = resp.headers.get("content-type", "")

            # A valid deployment returns 2xx or 3xx
            is_valid = 200 <= resp.status_code < 400

            # Check for meaningful content (not just an error page)
            has_content = content_length > 100 and (
                "<html" in content.lower()
                or "<!doctype" in content.lower()
                or "application/json" in content_type.lower()
                or "text/html" in content_type.lower()
                or content_length > 500
            )

            return {
                "valid": is_valid,
                "status_code": resp.status_code,
                "response_time_ms": elapsed_ms,
                "has_content": has_content,
                "content_length": content_length,
                "content_type": content_type,
                "error": None,
            }

    except httpx.TimeoutException:
        return {
            "valid": False,
            "status_code": 0,
            "response_time_ms": 0,
            "has_content": False,
            "content_length": 0,
            "content_type": "",
            "error": "Request timed out (20s limit)",
        }
    except httpx.ConnectError as e:
        return {
            "valid": False,
            "status_code": 0,
            "response_time_ms": 0,
            "has_content": False,
            "content_length": 0,
            "content_type": "",
            "error": f"Connection failed: {str(e)}",
        }
    except Exception as e:
        logger.exception("Deploy check failed")
        return {
            "valid": False,
            "status_code": 0,
            "response_time_ms": 0,
            "has_content": False,
            "content_length": 0,
            "content_type": "",
            "error": f"Unexpected error: {str(e)}",
        }
