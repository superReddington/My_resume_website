from fastapi import Cookie, Header, HTTPException

from app.core.config import settings


def require_admin(
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
    admin_token: str | None = Cookie(default=None),
) -> str:
    provided = x_admin_token or admin_token
    if not provided or provided != settings.admin_token:
        raise HTTPException(status_code=401, detail="管理令牌无效")
    return provided
