import os, time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv

# Env
load_dotenv()
USER = os.getenv("USERNAME")
PASS = os.getenv("PASS")
download_dir = os.getenv("DOWNLOAD_DIR")
url = os.getenv("URL")

# Last file downloaded
files = sorted(os.listdir(download_dir), reverse=True)
if files:
    last_file = os.path.join(download_dir, files[0])
else:
    last_file = ""

print("Last payslip downloaded : "+last_file)

def month_year_to_iso(s):
    month_map = {
        "Janvier": "01",
        "Février": "02",
        "Mars": "03",
        "Avril": "04",
        "Mai": "05",
        "Juin": "06",
        "Juillet": "07",
        "Août": "08",
        "Septembre": "09",
        "Octobre": "10",
        "Novembre": "11",
        "Décembre": "12"
    }

    parts = s.strip().split()
    if len(parts) != 2:
        raise ValueError(f"Unexpected format: {s}")
    month_name, year = parts

    month_num = month_map.get(month_name)
    if not month_num:
        raise ValueError(f"Unknown month name: {month_name}")

    return f"{year}-{month_num}"

def download_slip():
    options = webdriver.ChromeOptions()
    options.binary_location = "/usr/bin/chromium-browser"
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    prefs = {"download.default_directory" : download_dir}
    options.add_experimental_option("prefs", prefs)
    # options.add_argument("--headless=new") # No windows
    service = Service("/usr/lib/chromium-browser/chromedriver")

    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url+"/login")
        print("Login...")
        
        wait = WebDriverWait(driver, 15)  # wait up to 15 seconds for elements
        wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(USER)
        wait.until(EC.presence_of_element_located((By.ID, "password"))).send_keys(PASS + Keys.RETURN)
        print("Logged in")

        driver.get(url+"/e/100630/payslips")

        dates = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tbody tr th"))
        )
        
        pdf_links = wait.until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//a[contains(@href, 'pdf')]")
            )
        )
        
        i = 0
        
        for date in dates:
            d=month_year_to_iso(date.get_attribute("innerText"))+".pdf"
            if download_dir+"/"+d == last_file:
                print("We already downloaded this file")
                break
            pdf_url=pdf_links[i].get_attribute("href")
            print("date :"+d+", links :"+pdf_url)
            driver.execute_script("window.open(arguments[0]);", pdf_url)
            time.sleep(1)
            files = sorted(os.listdir(download_dir), key=lambda f: os.path.getmtime(os.path.join(download_dir, f)))
            latest_file = os.path.join(download_dir, files[-1])
            new_name = os.path.join(download_dir, d)
            os.rename(latest_file, new_name)
            print("Renamed "+latest_file+" into "+new_name)
            i+=1

    except Exception as e:
        print("Error :", e)
    finally:
        driver.quit()
        print("Success")

if __name__ == "__main__":
    download_slip()
