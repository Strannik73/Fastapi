from datetime import datetime, timedelta
import uuid
import pandas as pd
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import hashlib

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

USERS = "users.csv"
SESSION_TTL = timedelta(days=10)
sessions = {}
white_urls = ["/", "/login", "/logout", "/register"]  # /main убрал

def hash_password(password) -> str:
    return hashlib.sha256(str(password).encode("utf-8")).hexdigest()

df = pd.read_csv("users.csv")

# если есть колонка "password", пересчитаем в hash
if "password" in df.columns:
    df["password_hash"] = df["password"].apply(hash_password)
    df = df.drop(columns=["password"])

df.to_csv("users.csv", index=False)
print("users.csv обновлён:", df.head())

@app.middleware("http")
async def check_session(request: Request, call_next):
    if request.url.path.startswith("/static") or request.url.path in white_urls:
        return await call_next(request)
    
    session_id = request.cookies.get("session_id")
    session_data = sessions.get(session_id)

    if not session_data:
        return RedirectResponse(url="/login")
    
    created = session_data.get("created")
    if datetime.now() - created > SESSION_TTL:
        sessions.pop(session_id, None)
        return RedirectResponse(url="/login")
    
    return await call_next(request)

@app.get("/", response_class=HTMLResponse)
@app.get("/login", response_class=HTMLResponse)
def get_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def post_login(request: Request, 
               username: str = Form(...), 
               password: str = Form(...)):
    try:
        users = pd.read_csv(USERS)
        users = users.loc[:, ~users.columns.str.contains('^Unnamed')]
    except Exception:
        users = pd.DataFrame(columns=["users", "password", "password_hash"])

    if "role" not in users.columns:
        users["role"] = "user"

    if username in users["users"].values:
        stored_hash = users.loc[users["users"] == username, "password_hash"].values[0]
        user_role = users.loc[users["users"] == username, "role"].values[0]

        if stored_hash == hash_password(password):
            session_id = str(uuid.uuid4())
            sessions[session_id] = {
                "created": datetime.now(),
                "username": username,
                "avatar": "static/avatars/default.png",
                "password_hash": stored_hash,
                "role": user_role
            }
            response = RedirectResponse(url="/main", status_code=303)
            response.set_cookie(key="session_id", value=session_id, httponly=True)
            response.set_cookie(key="username", value=username, httponly=True)
            response.set_cookie(key="role", value=user_role, httponly=True)
            return response

        return templates.TemplateResponse("login.html", {"request": request, "error": "Неверный пароль"})
    
    return templates.TemplateResponse("login.html", {"request": request, "error": "Неверный логин"})

@app.get("/register", response_class=HTMLResponse)
def get_register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def post_register(request: Request, 
                  username: str = Form(...), 
                  password: str = Form(...)):
    try:
        users = pd.read_csv(USERS)
        users = users.loc[:, ~users.columns.str.contains('^Unnamed')]
    except Exception:
        users = pd.DataFrame(columns=["users", "password", "password_hash", "role"])

    if "role" not in users.columns:
        users["role"] = "user"

    if username in users["users"].values:
        return templates.TemplateResponse("register.html", {"request": request, "error": "такой пользователь существует"})
    
    password_hash = hash_password(password)
    role = "admin" if username == "admin" else "user"
    new_user = pd.DataFrame([{"users": username, 
                              "password": password,
                              "password_hash": password_hash,
                              "role": role}])
    users = pd.concat([users, new_user], ignore_index=True)
    users.to_csv(USERS, index=False)

    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "created": datetime.now(),
        "username": username,
        "avatar": "static/avatars/default.png",
        "password_hash": password_hash,
        "role": role
    }
    response = RedirectResponse(url="/main", status_code=303)
    response.set_cookie(key="session_id", value=session_id, httponly=True)
    response.set_cookie(key="username", value=username, httponly=True)
    response.set_cookie(key="role", value=role, httponly=True)
    return response

@app.get("/main", response_class=HTMLResponse)
def main_page(request: Request):
    session_id = request.cookies.get("session_id")
    users = None
    if session_id and session_id in sessions:
        session_data = sessions[session_id]
        if isinstance(session_data, dict):
            users = {
                "username": session_data.get("username"),
                "avatar": session_data.get("avatar", "static/avatars/default.png"),
                "password_hash": session_data.get("password_hash", ""),
                "role": session_data.get("role", "user")
            }
    return templates.TemplateResponse("main.html", {"request": request, "user": users})

@app.get("/logout", response_class=HTMLResponse)
def logout(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id:
        sessions.pop(session_id, None)
    return RedirectResponse(url="/login", status_code=303)

@app.exception_handler(404)
async def not_found(request: Request, exc):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)


@app.exception_handler(403)
async def forbidden(request: Request, exc):
    return templates.TemplateResponse("403.html", {"request": request}, status_code=403)
