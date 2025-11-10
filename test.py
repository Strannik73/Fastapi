# # tests/test_main.py
# import os
# import shutil
# import importlib
# from pathlib import Path
# import pandas as pd
# import pytest
# from fastapi.testclient import TestClient

# MODULE_NAME = "main"

# @pytest.fixture
# def isolated_app(tmp_path, monkeypatch):
#     """
#     Импортирует main.py в изолированном временном каталоге.
#     Создаёт пустые users.csv и log.csv (если нужно) и возвращает TestClient(app).
#     """

#     project_dir = tmp_path / "proj"
#     project_dir.mkdir()

#     src_main = Path.cwd() / "main.py"
#     if not src_main.exists():
#         pytest.skip("main.py not found in working directory")
#     shutil.copy(src_main, project_dir / "main.py")

#     templates_dir = project_dir / "templates"
#     templates_dir.mkdir()
#     (templates_dir / "login.html").write_text("<html>login</html>")
#     (templates_dir / "register.html").write_text("<html>register</html>")
#     (templates_dir / "main.html").write_text("<html>main: {{ user.username if user else ''}}</html>")
#     (templates_dir / "admin.html").write_text("<html>admin: {{ user.username }}</html>")
#     (templates_dir / "404.html").write_text("<html>404</html>")
#     (templates_dir / "403.html").write_text("<html>403</html>")

#     static_dir = project_dir / "static"
#     avatars_dir = static_dir / "avatars"
#     avatars_dir.mkdir(parents=True)
#     (avatars_dir / "default.png").write_text("PNG")

#     old_cwd = Path.cwd()
#     os.chdir(project_dir)

#     if MODULE_NAME in importlib.util.sys.modules:
#         importlib.reload(importlib.import_module(MODULE_NAME))
#     else:
#         importlib.invalidate_caches()

#     try:
#         main = importlib.import_module(MODULE_NAME)
#         importlib.reload(main)
#         client = TestClient(main.app)
#         yield client, project_dir
#     finally:
#         os.chdir(old_cwd)
#         if MODULE_NAME in importlib.util.sys.modules:
#             importlib.util.sys.modules.pop(MODULE_NAME)


# def test_register_autologin_and_main_access(isolated_app):
#     client, project_dir = isolated_app


#     resp = client.post("/register", data={"username": "alice", "password": "secret"}, allow_redirects=False)
#     assert resp.status_code in (302, 303) 

#     cookies = resp.cookies
#     assert "session_id" in cookies

#     client.cookies.set("session_id", cookies["session_id"])
#     r = client.get("/main")
#     assert r.status_code == 200
#     assert "main" in r.text

#     users_csv = project_dir / "users.csv"
#     assert users_csv.exists()
#     df = pd.read_csv(users_csv)
#     assert "alice" in df["users"].values
#     assert df.loc[df["users"] == "alice", "role"].values[0] == "user"


# def test_login_wrong_password_and_success(isolated_app):
#     client, project_dir = isolated_app

#     users_csv = project_dir / "users.csv"
#     df = pd.DataFrame([{"users": "bob", "password": None, "password_hash": "", "role": "user", "avatar": "static/avatars/default.png"}])
#     df.to_csv(users_csv, index=False)

#     r1 = client.post("/login", data={"username": "bob", "password": "badpass"})
#     assert r1.status_code == 200
#     assert "Неверный пароль" in r1.text or "login" in r1.text

#     client.post("/register", data={"username": "bob", "password": "goodpass"}, allow_redirects=False)
#     r2 = client.post("/login", data={"username": "bob", "password": "goodpass"}, allow_redirects=False)
#     assert r2.status_code in (302, 303)
#     assert "session_id" in r2.cookies


# def test_protected_route_requires_login(isolated_app):
#     client, project_dir = isolated_app

#     r = client.get("/main", allow_redirects=False)
#     assert r.status_code in (307, 302, 303)
#     assert "/login" in r.headers.get("location", "")


# def test_admin_access_control(isolated_app):
#     client, project_dir = isolated_app

#     resp = client.post("/register", data={"username": "admin", "password": "adm1n"}, allow_redirects=False)
#     assert resp.status_code in (302, 303)
#     sid = resp.cookies.get("session_id")
#     client.cookies.set("session_id", sid)

#     r = client.get("/admin")
#     assert r.status_code == 200
#     assert "admin" in r.text

#     r2 = client.post("/register", data={"username": "charlie", "password": "p"}, allow_redirects=False)

#     sid2 = r2.cookies.get("session_id")
#     client.cookies.set("session_id", sid2)

#     r_forbidden = client.get("/admin")
#     assert r_forbidden.status_code in (200, 403)
#     assert "Доступ запрещён" in r_forbidden.text or "admin" not in r_forbidden.text

from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoAlertPresentException, NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver
import pandas as pd
import numpy as np
import unittest
import time

class TestStringMethods(unittest.TestCase):

    def test_admin_login(self):
        driver = webdriver.Chrome()
        driver.get("https://127.0.0.1")

        time.sleep(5)

        login_input = driver.find_element(By.XPATH, value='/html/body/div/form/input[1]')
        passwd_input = driver.find_element(By.XPATH, value='/html/body/div/form/input[2]')
        submit_btn = driver.find_element(By.XPATH, value='/html/body/div/form/button')

        login_input.clear()
        passwd_input.clear()

        login_input.send_keys("admin")
        passwd_input.send_keys("admin")

        submit_btn.click()
        self.assertEqual(driver.find_element(By.XPATH, value='/html/body/div/h1').get_attribute("textContent"), "Добро пожаловать, admin!")
        driver.quit()

    def test_admin_registration_and_user_login(self):
        TESTING_NICKNAME = "testSuiteUser"
        TESTING_PWD = "1234"
        driver = webdriver.Chrome()
        driver.get("https://127.0.0.1")

        time.sleep(5)

        login_input = driver.find_element(By.XPATH, value='/html/body/div/form/input[1]')
        passwd_input = driver.find_element(By.XPATH, value='/html/body/div/form/input[2]')
        submit_btn = driver.find_element(By.XPATH, value='/html/body/div/form/button')

        login_input.clear()
        passwd_input.clear()

        login_input.send_keys("admin")
        passwd_input.send_keys("admin")

        submit_btn.click()


        time.sleep(5)
        new_user_input = driver.find_element(By.XPATH, value='/html/body/div/form/input[1]')
        new_pwd_input = driver.find_element(By.XPATH, value='/html/body/div/form/input[2]')
        new_user_btn = driver.find_element(By.XPATH, value='/html/body/div/form/button')

        new_user_input.clear()
        new_pwd_input.clear()

        new_user_input.send_keys(TESTING_NICKNAME)
        new_pwd_input.send_keys(TESTING_PWD)
        new_user_btn.click()

        leave_link = driver.find_element(By.XPATH, value='/html/body/div/a')
        leave_link.click()


        time.sleep(5)
        login_input = driver.find_element(By.XPATH, value='/html/body/div/form/input[1]')
        passwd_input = driver.find_element(By.XPATH, value='/html/body/div/form/input[2]')
        submit_btn = driver.find_element(By.XPATH, value='/html/body/div/form/button')

        login_input.clear()
        passwd_input.clear()

        login_input.send_keys(TESTING_NICKNAME)
        passwd_input.send_keys(TESTING_PWD)
        submit_btn.click()
        self.assertEqual(driver.find_element(By.XPATH, value='/html/body/div/h1').get_attribute("textContent"), f"Добро пожаловать, {TESTING_NICKNAME}!")
        driver.quit()

    def alert_session_continue_test(self):
        driver = webdriver.Chrome()
        driver.get("https://127.0.0.1")

        time.sleep(5)

        login_input = driver.find_element(By.XPATH, value='/html/body/div/form/input[1]')
        passwd_input = driver.find_element(By.XPATH, value='/html/body/div/form/input[2]')
        submit_btn = driver.find_element(By.XPATH, value='/html/body/div/form/button')

        login_input.clear()
        passwd_input.clear()

        login_input.send_keys("admin")
        passwd_input.send_keys("admin")

        submit_btn.click()
        try:
            WebDriverWait(driver, 180).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            
            print("Alert text:", alert.text)
            alert.accept()
            
        except NoAlertPresentException:
            print("No alert was present.")
        self.assertEqual(alert.text, "Сессия продлена")
        driver.quit()
        

    def alert_session_break_test(self):
        driver = webdriver.Chrome()
        driver.get("https://127.0.0.1")

        time.sleep(5)

        login_input = driver.find_element(By.XPATH, value='/html/body/div/form/input[1]')
        passwd_input = driver.find_element(By.XPATH, value='/html/body/div/form/input[2]')
        submit_btn = driver.find_element(By.XPATH, value='/html/body/div/form/button')

        login_input.clear()
        passwd_input.clear()

        login_input.send_keys("admin")
        passwd_input.send_keys("admin")

        submit_btn.click()
        try:
            WebDriverWait(driver, 180).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            
            print("Alert text:", alert.text)
            alert.dismiss()
            
        except NoAlertPresentException:
            print("No alert was present.")
        self.assertEqual(driver.find_element(By.XPATH, value='/html/body/div/form/button').get_attribute("textContent"), "Войти")
        driver.quit()

    def test_404(self):
        driver404 = webdriver.Chrome()
        driver404.get("https://127.0.0.1/fantastic/site/that/should/be/never/existed")

        time.sleep(5)

        header = driver404.find_element(By.XPATH, value='/html/body/h1')
        self.assertEqual(header.get_attribute("textContent"), "Page not found (404 ERROR)")
        driver404.quit()

    def test_403(self):
        driver403 = webdriver.Chrome()
        driver403.get("https://127.0.0.1/admin")

        time.sleep(5)

        header = driver403.find_element(By.XPATH, value='/html/body/h1')
        self.assertEqual(header.get_attribute("textContent"), "FORBIDDEN (403 ERROR)") 
        driver403.quit()

    def incorrect_pwd(self):
        driver = webdriver.Chrome()
        driver.get("https://127.0.0.1")

        login_input = driver.find_element(By.XPATH, value='/html/body/div/form/input[1]')
        passwd_input = driver.find_element(By.XPATH, value='/html/body/div/form/input[2]')
        submit_btn = driver.find_element(By.XPATH, value='/html/body/div/form/button')

        login_input.clear()
        passwd_input.clear()

        login_input.send_keys("admin")
        passwd_input.send_keys("123")

        submit_btn.click()
        try:
            error_msg = driver.find_element(By.XPATH, value='/html/body/div/p[1]')
            self.assertEqual(error_msg.get_attribute("textContent"), "Неверный логин или пароль") 
        except NoSuchElementException:
            print("Element does not exist.")
        driver.quit()

if __name__ == '__main__':
    unittest.main()