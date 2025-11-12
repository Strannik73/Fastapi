import unittest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://127.0.0.1:8443"  

class SimpleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")          
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-insecure-localhost")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.wait = WebDriverWait(cls.driver, 10)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_admin_login(self):
        self.driver.get(f"{BASE_URL}/login")
        login_input = self.wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div/form/input[1]')))
        passwd_input = self.wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div/form/input[2]')))
        submit_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/form/button')))

        login_input.clear()
        passwd_input.clear()
        login_input.send_keys("admin")
        passwd_input.send_keys("admin")
        submit_btn.click()

        header = self.wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div/h1')))
        self.assertIn("Добро пожаловать", header.get_attribute("textContent"))

if __name__ == "__main__":
    unittest.main(verbosity=2)