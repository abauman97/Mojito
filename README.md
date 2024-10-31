# Welcome to the Mojito framework

Mojito is a fresh, simple, and fast micro-framework for building html-first web applications and sites. 

The key features are:

* Fast: Based on Starlette, a fast and lightweight ASGI micro-framework.
* Simple to code: An intuitve API that anyone familir with Flask or FastAPI will pick up on easily.
* Batteries included: Providing helper functions to simplify repetitive tasks like auth and form processing.

**Documentation**: <a href="https://abauman97.github.io/Mojito/" target="_blank">https://abauman97.github.io/Mojito/</a>

**Source Code**: <a href="https://github.com/abauman97/Mojito" target="_blank">https://github.com/abauman97/Mojito</a>


# Inspirations
Mojito is built off the work done both previously and currently by projects like Flask, FastAPI, and Django.

While still a micro-framework we aim to provide you all the glue you need to get your personal or line-of-business app running in the shortest time possible.

# Installation
`pip install mojito-web[standard]`

This will install Mojito with standard dependencies like uvicorn for serving your application and httpx for using the TestClient.

## First Steps
Create a very basic Mojito app:

```py title="main.py"
from mojito import Mojito

app = Mojito()

@app.route('/')
async def index():
    return "<h1>Hello, World!</h1>"
```

then run the live server in your terminal:
```sh
$ uvicorn main:app --reload
INFO:     Will watch for changes in these directories: ['/home/user/dev/myapp/main.py']
INFO:     Uvicorn running on http://localhost:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [17096] using WatchFiles
INFO:     Started server process [16220]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

Open [http://localhost:8000](http://localhost:8000) to view the live server.

## Going Deeper
Read the [docs](https://abauman97.github.io/Mojito/) to learn more about the features you need to build out your application.