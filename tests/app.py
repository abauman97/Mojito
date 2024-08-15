import uvicorn
from mojito import Mojito
from tests.app_routes import router as routes_router


app = Mojito(debug=True)

app.include_router(routes_router)

print(f"Routes registered: {app.routes}")

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", reload=True)
