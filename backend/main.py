from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router
from app.session_middleware import SessionMiddleware, get_session_id


app = FastAPI()


app.add_middleware(SessionMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router
from app.session_middleware import SessionMiddleware, get_session_id

app = FastAPI()

app.add_middleware(SessionMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

