import uvicorn
from mojito import Mojito, auth
from tests.app_routes import router as routes_router
from tests.auth import PasswordAuth


app = Mojito(debug=True)

auth.add_auth_handler(PasswordAuth)

app.include_router(routes_router)

print(f"Routes registered: {app.routes}")

if __name__ == "__main__":
    uvicorn.run("tests.app:app", host="localhost", port=5001, reload=True)
