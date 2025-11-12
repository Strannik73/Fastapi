import os
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

USERS_CSV = "users.csv"
LOG_CSV = "log.csv"
SESSION_TTL = timedelta(days=10)
WHITE_URLS = {"/", "/login", "/register", "/logout", "/static"}
DEV_MODE = os.getenv("DEV_MODE", "1") == "1" 

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

sessions: dict[str, dict] = {}


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def ensure_users_file():
    if not os.path.exists(USERS_CSV):
        df = pd.DataFrame(columns=["users", "password_hash", "role"])
        df.to_csv(USERS_CSV, index=False)


def read_users() -> pd.DataFrame:
    ensure_users_file()
    try:
        df = pd.read_csv(USERS_CSV)
    except Exception:
        df = pd.DataFrame(columns=["users", "password_hash", "role"])
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    if "users" not in df.columns:
        df["users"] = []
    if "password_hash" not in df.columns:
        if "password" in df.columns:
            df["password_hash"] = df["password"].astype(str).apply(hash_password)
            df = df.drop(columns=["password"])
        else:
            df["password_hash"] = ""
    if "role" not in df.columns:
        df["role"] = "user"
    return df


def write_users(df: pd.DataFrame):
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    if "password" in df.columns:
        df = df.drop(columns=["password"])
    df.to_csv(USERS_CSV, index=False)


def append_log(user: str, role: str, action: str):
    entry = { "user": user, "role": role, "action": action, "Date": datetime.now().date().isoformat(), "Time": datetime.now().time().isoformat(timespec="seconds"),}
    try:
        if not os.path.exists(LOG_CSV):
            pd.DataFrame([entry]).to_csv(LOG_CSV, index=False)
        else:
            lg = pd.read_csv(LOG_CSV)
            lg = lg.loc[:, ~lg.columns.str.contains("^Unnamed")]
            lg = pd.concat([lg, pd.DataFrame([entry])], ignore_index=True)
            lg.to_csv(LOG_CSV, index=False)
    except Exception:
        pd.DataFrame([entry]).to_csv(LOG_CSV, index=False)


ensure_users_file()
if not os.path.exists(LOG_CSV):
    pd.DataFrame(columns=["user", "role", "action", "Date", "Time"]).to_csv(LOG_CSV, index=False)


@app.middleware("http")
async def session_middleware(request: Request, call_next):
    path = request.url.path
    if path.startswith("/static") or path in WHITE_URLS:
        return await call_next(request)

    session_id = request.cookies.get("session_id")
    if not session_id:
        return RedirectResponse(url="/login")

    session = sessions.get(session_id)
    if not session:
        return RedirectResponse(url="/login")

    created: Optional[datetime] = session.get("created")
    if not created or (datetime.now() - created) > SESSION_TTL:
        sessions.pop(session_id, None)
        return RedirectResponse(url="/login")

    session["created"] = datetime.now()
    return await call_next(request)


@app.get("/", response_class=HTMLResponse)
@app.get("/login", response_class=HTMLResponse)
def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def post_login(request: Request, username: str = Form(...), password: str = Form(...)):
    users = read_users()
    if username not in users["users"].values:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Неверный логин "})

    row = users.loc[users["users"] == username].iloc[0]
    stored_hash = row.get("password_hash", "")
    role = row.get("role", "user")
    if stored_hash != hash_password(password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Неверный пароль"})

    session_id = str(uuid.uuid4())
    sessions[session_id] = {"created": datetime.now(), "username": username, "role": role}

    response = RedirectResponse(url="/main", status_code=303)
    secure_flag = False if DEV_MODE else True
    response.set_cookie("session_id", session_id, httponly=True, secure=secure_flag, samesite="strict")
    response.set_cookie("username", username, httponly=True, secure=secure_flag, samesite="strict")
    response.set_cookie("role", role, httponly=True, secure=secure_flag, samesite="strict")

    append_log(username, role, "login")
    return response


@app.get("/register", response_class=HTMLResponse)
def get_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register")
def post_register(request: Request, username: str = Form(...), password: str = Form(...)):
    users = read_users()
    if username in users["users"].values:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Пользователь уже существует"})

    password_hash = hash_password(password)
    role = "admin" if username == "admin" else "user"
    new_row = {"users": username, "password_hash": password_hash, "role": role}
    users = pd.concat([users, pd.DataFrame([new_row])], ignore_index=True)
    write_users(users)

    session_id = str(uuid.uuid4())
    sessions[session_id] = {"created": datetime.now(), "username": username, "role": role}
    response = RedirectResponse(url="/main", status_code=303)
    secure_flag = False if DEV_MODE else True
    response.set_cookie("session_id", session_id, httponly=True, secure=secure_flag, samesite="strict")
    response.set_cookie("username", username, httponly=True, secure=secure_flag, samesite="strict")
    response.set_cookie("role", role, httponly=True, secure=secure_flag, samesite="strict")

    append_log(username, role, "register")
    return response


@app.get("/main", response_class=HTMLResponse)
def get_main(request: Request):
    session_id = request.cookies.get("session_id")
    user = None
    if session_id:
        s = sessions.get(session_id)
        if s:
            user = {"username": s.get("username"), "role": s.get("role")}
    return templates.TemplateResponse("main.html", {"request": request, "user": user})


@app.get("/logout", response_class=HTMLResponse)
def logout(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id:
        sessions.pop(session_id, None)
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("session_id")
    response.delete_cookie("username")
    response.delete_cookie("role")
    return response


@app.exception_handler(404)
async def not_found(request: Request, exc):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)


@app.exception_handler(403)
async def forbidden(request: Request, exc):
    return templates.TemplateResponse("403.html", {"request": request}, status_code=403)
