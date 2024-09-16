# Routing

Most applications need more than just one file to define and manage all your routes, this where the AppRouter comes in.

Similar to the APIRouter in FastAPI or Blueprints in Flask, the AppRouter allows for chaining routers and breaking out routes however you like. 

## An example file structure
For our examples going forward we'll assume you have a file structure like this:
```
..
|-- src
|	|-- __init__.py
|	|-- main.py
|	|-- routers
|	|	|-- __init__.py
|	|	|-- users.py
|	|	|-- admin.py
```

* The src directory contains all your application code.
* It contains a `main.py` file. This is the main entry point of your application.
* The subdirectory `routers` contains individual routers for your application. For instance you have a `src/routers/users.py` that will contain all the routes for users
* The `users.py` and `admin.py` files contain routes related to users and admin operations respectively
* All directories have a `__init__.py` file to make them a module and allow for importing from one module to another: `from src.routers.users import users_router`


# AppRouter
Let's say the file dedicated to handling users is the submodule `/src/routers/users.py`.

You want to group all path operations related to your users from the rest of your code to keep it organized and/or protect those operations differently than the rest.

`AppRouter` instances still combine all routes into the same `Mojito` application.

## Import `AppRouter`
You import it and create an instance of the AppRouter the same way you would the `Mojito` class.

And then use it to declare your path operations.

```py title="src/routers/users.py"
from mojito import AppRouter

router = AppRouter()

@router.route('/users')
def users():
   return """
	<ul>
		<li>Paul</li>
		<li>Sam</li>
	</ul>
   """


@router.route('/users/{user_id}')
async def user(user_id: int):
   async with get_db_connection() as db:
		user = (await db.execute(text("select user where user.id == user_id"))).scalars().one()
```

## AppRouter Options
The `AppRouter` can be configured to privide shared configuration to all of its path operations.

### Middleware
Any ASGI middleware will work. Use `AppRouter.include_middleware()` to add a middleware such as `AuthRequiredMiddleware` to provide middleware specific to only the instances path operations.

Middleware is applied to each route individually and must be added before the path operations are defined, like so:

```py title="src/routers/users.py"
from mojito import AppRouter, auth

router = AppRouter()

router.add_middleware(auth.AuthRequiredMiddleware)

@router.route('/users')
async def users():
   return """
	<ul>
		<li>Paul</li>
		<li>Sam</li>
	</ul>
   """


@router.route('/users/{user_id}')
async def user(user_id: int):
   pass
```

### Including Sub-Routers
Routers can be included as sub-routers for better organizing and applying configurations to routes by using the `AppRouter.include_router()` method, just as routers can be included in the `Mojito` class.

Note: This will add the sub-router paths under the prefix of the router you're adding to. For example including a router into our user `users.py` router will include the prefix from the `users` router if one exists.

Note: Middleware and Lifespan is scoped to the router and any sub-routers will not inherit those configurations.

## The main `Mojito`
Now let's go back to the module `src/main.py`.

This is where we'll include the routers we defined in the `users.py` and `admin.py` files.

```py title="src.main.py"
from mojito import Mojito

from src.routers import users, admin

app = Mojito()

app.include_router(users.router)
app.include_router(admin.router)

@app.route('/')
def index():
	return "<h1>Hello, World!</h1>
```
