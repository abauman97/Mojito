# Getting Started

## Installation
`pip install mojito-web[standard]`

This will install Mojito with standard dependencies like uvicorn for serving your application and httpx for using the TestClient.

## First Steps
The simplest Mojito file could look like this:

```py title="main.py"
from mojito import Mojito

app = Mojito()

@app.route('/')
async def index():
    return "<h1>Hello, World!</h1>"
```

Run the live server in your terminal:
```sh
$ uvicorn main:app --reload
INFO:     Will watch for changes in these directories: ['/home/user/dev/myapp/main.py']
INFO:     Uvicorn running on http://localhost:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [17096] using WatchFiles
INFO:     Started server process [16220]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```