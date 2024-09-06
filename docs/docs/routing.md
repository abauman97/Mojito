# Routing

Most applications need more than just one file to define and manage all your routes, this where the AppRouter comes in.

Similar to the APIRouter in FastAPI, the AppRouter allows for chaining routers and breaking out routes however you like. 

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

AppRouter instances still combine all routes into the same Mojito application.

## Import `AppRouter`
You import it and create an instance of the AppRouter the same way you would the `Mojito` class.
```py title="src/routers/users.py"
from mojito import AppRouter

router = AppRouter(prefix="/users")

@router.route('/')
async def users():
   return """
	<ul>
		<li>Paul</li>
		<li>Sam</li>
	</ul>
   """


@router.route('/{user_id}')
async def user(user_id: int):
   pass
```

## Path operations with `AppRouter`
