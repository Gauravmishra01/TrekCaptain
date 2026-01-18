from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Expose a FastAPI application object named `app` so uvicorn can import it
app = FastAPI(title="Three Sides API", version="0.1.0")

# Allow the frontend static server and localhost origins for development
app.add_middleware(
	CORSMiddleware,
	allow_origins=["http://127.0.0.1:5500", "http://localhost:5500", "http://127.0.0.1:5173", "http://localhost:5173"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Import and include routers (users, agencies, admin)
from .routers.users import user
from .routers import agency  # relative imports within package
from .routers.users import getUser as get_user_router
from .routers import trek as trek_router
from .routers import search as search_router 
from .routers.upload.uploadImage import router as upload_router 
from .routers.search import router as search
from .routers.users.agenciesByTrekId import router as agencies_trek_router
from .routers.advertisement import router as advertisement
from .routers.home import router as home
from .routers.category import router as category

# include existing user router (register/verify) and the separate get-user router
app.include_router(user.router, prefix="/api/v1/users")
app.include_router(get_user_router.router, prefix="/api/v1/users")
app.include_router(trek_router.router, prefix="/api/v1/treks")
app.include_router(agency.router, prefix="/api/v1/agencies")
app.include_router(search_router.router, prefix="/api/v1/treks")
app.include_router(upload_router, prefix="/api/v1/uploads")
app.include_router(search, prefix="/api/v1/search")
app.include_router(agencies_trek_router, prefix="/api/v1")

app.include_router(advertisement)
app.include_router(home)
app.include_router(category)





@app.get("/", tags=["root"])
async def root_status():
	return {"message": "Three Sides API is running"}

