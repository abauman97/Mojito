import os
from typing import Optional


class Config:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    """Secret key used to encrypt sensitive data.
    
    Defaults to empty string.
    """
    MESSAGE_FLASH_COOKIE: str = os.getenv("MESSAGE_FLASH_COOKIE", "mo_flash_messages")
    """Name of the cookie message flash data will be stored to.
    
    Defaults to `mo_flash_messages`
    """
    LOGIN_URL: str = os.getenv("LOGIN_URL", "/login")
    "Defaults to `/login`"
    USER_SESSION_COOKIE: str = os.getenv("USER_SESSION_COOKIE", "mo_user_session")
    """Name of the user session cookie.
    
    Defaults to `mo_user_session`
    """
    USER_SESSION_EXPIRES: int = int(os.getenv("USER_SESSION_EXPIRES", 60 * 60 * 24 * 7))
    """In seconds. How long the session cookie should be allowed to exist before being replaced.
    
    Defaults to 1 week.
    """
    USER_SESSION_REVALIDATE_AFTER: int = int(
        os.getenv("USER_SESSION_REVALIDATE_AFTER", 0)
    )
    """In seconds. How long the session cookie should be considered valid before running revalidation
    on the users authentication. Within this time, as long as the cookie signature is
    valid, the user will be considered authenticated and all the cookie data will be used.

    Defaults to 0, revalidate on every request.
    """
    SUPERUSER_PERMISSION_NAME: Optional[str] = os.getenv("SUPERUSER_PERMISSION_NAME")
    """The name of the superuser permission.

    When present in the Request.user.permissions, this role will bypass any permission (authorization) 
    requirements defined for a route function. This permission does not bypass authentication.
    """
