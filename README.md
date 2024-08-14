# Mojito
ASGI Python web framework.

Based on Starlette and Jinja2 templates, Mojito is an async python web framework meant to resemble the same ease of use as Flask but built with an ASGI implementation.

Mojito is Starlette underneath and provides a thin layer on top to make dealing with app management easier, providing ease-of-life defaults, and adding a few handy tools like g, the global context variable similar to Flask's g.

Provided handy bits:
- g: Global context variable
- Message flashing: built off of g and cookies. Provides a way of displaying messages the same way as Flask during the session.


## Route functions
Routes are created primarily by decorating a function with `@AppRouter.route()`.
Each function must take the Request as the first parameter.

The default response type of routes is HTMLResponse.


## Handy bits
### g: GlobalContextVar
Global context variable similar to g in Flask. Scoped to the request lifecycle it can be used anywhere throughout the application and will be unique to each request.

Usage
```
g.foo = 'foood'

print(g.foo) -> 'foood'
```

### Message flashing
Provides message flashing like Flask with methods `flash_message()` and `get_flashed_messages()` 