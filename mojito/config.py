# TODO - Load config from os if it exists
class Config:
    SECRET_KEY: str = "poaiuvnepwoijsoxmkcpaoiu"
    MESSAGE_FLASH_COOKIE: str = "flash_messages"
    LOGIN_URL: str = "/login"
    SESSION_EXPIRES: int = 60 * 60 * 24 * 7  # 1wk default
    "In seconds. How long the session cookie should be allowed to exist before being replaced."
    SESSION_REVALIDATE_AFTER: int = 0  # Revalidate on every request
    """In seconds.
    How long the session cookie should be considered valid before running revalidation
      on the users authentication. Within this time, as long as the cookie signature is
      valid, the user will be considered authenticated and all the cookie data will be used.
      """
