from datetime import datetime, timezone
from typing import Any, Dict

# TODO add request id
def build_error_response(
    error_type: str ,
    message: str,
    status_code: int,
    details: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """The Single Source of Truth for error response formatting."""
    return {
        "error_type": error_type,
        "message": message,
        "status_code": status_code,
        "details": details,
        "timestamps": datetime.now(timezone.utc).isoformat()
    }