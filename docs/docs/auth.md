# Auth

Authentication is essential to almost all applications. Mojito provides a simple authentication system with pluggable backends similar to that found in Django but more flexible.

## Overview
The auth system contains the following parts:
- Backend - An implementation of BaseAuth which provides `authenticate` and `get_user` methods.
- Route Protection - Middleware or decorator based protection to indicate what routes are to be protected with what rules.
- Helpers - Additional functions like `hash_password` to reduce boilerplate operations.

# Configuring Authentication
Configuration can be fairly simple to implement. We'll assume you already have a database with a user table to pull from.

Steps:
1. Create a backend
2. Protect routes
3. Login to access protected routes

# Creating a backend
Backends must implement `authenticate` and `get_user` methods but can include any other methods you wish to add. A prototype class `BaseAuth` is provided to simplify the process.

```py title="src/auth.py"
from mojito import auth, Request

from src.db import get_db

class PasswordAuth(auth.BaseAuth):
    "Authenticate with username and password"

    async def authenticate(self, request: Request, **kwargs: dict[str, str]):
        email: str = kwargs.get("username")
        password: str = kwargs.get("password")
        async with get_db() as db:
            user = await (
                await db.execute(f"SELECT * FROM users where email = '{email}'")
            ).fetchone()
        if not user:
            raise ValueError("No user found in database")
        if not auth.hash_password(password) == user["password"]:
            return None
        user_dict = dict(user)
        del user_dict["password"]
        auth_data = auth.AuthSessionData(
            is_authenticated=True,
            auth_handler="PasswordAuth",
            user_id=user["id"],
            user=dict(user),
            permissions=["admin"],
        )
        return auth_data

    async def get_user(self, user_id: int) -> auth.AuthSessionData:
        async with get_db() as db:
            user = await (
                await db.execute(
                    f"SELECT id, name, email, is_active FROM users where id = {user_id}"
                )
            ).fetchone()
        if not user:
            raise ValueError("No user found in database")
        return auth.AuthSessionData(
            is_authenticated=True,
            auth_handler="PasswordAuth",
            user_id=user["id"],
            user=dict(user),
            permissions=["admin"],
        )


```

And in `main.py` add this to include the auth handler. This doesn't need to be included in the `main.py` file but does need to be run prior to any protected routes being called or else you will get an error.
```py title="src/main.py"
from mojito import auth

auth.include_auth_handler(PasswordAuth, primary=True)
```

# Protecting routes
There are two primary ways of protecting routes, middlware and decorators.

## `AuthMiddleware` middleware
The `AuthMiddleware` class will require authentication and authorization to all the routes within its router.

## `require_auth` decorator
The `require_auth` decorator provides protection only to the routes it's applied to. This must be applied before, i.e. below, the route decorator so that no matter how the route function is called, the auth process will be applied.