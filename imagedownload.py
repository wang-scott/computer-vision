# ...existing code...
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import requests
import time
import os
import re
import json
import urllib.parse

BASE_DIR = os.path.dirname(__file__)
OUT_ROOT = os.path.join(BASE_DIR, 'dataset')
os.makedirs(OUT_ROOT, exist_ok=True)

keyword_file = os.path.join(BASE_DIR, 'keyword_p.txt')
if not os.path.exists(keyword_file):
    print(f'找不到關鍵字檔案: {keyword_file}')
    raise SystemExit(1)

with open(keyword_file, 'r', encoding='utf-8') as f:
    keywords = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

def setup_driver(headless=True):
    opts = Options()
    if headless:
        # 注意：不同 Chrome/selenium 版本 headless 參數可能不同
        opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--window-size=1920,1080')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    return driver

def scroll_to_bottom(driver, pause=1.0, max_scrolls=30):
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(max_scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def extract_bing_image_urls(driver, max_num=500):
    imgs = set()
    # Bing 圖片連結通常在 a.iusc 的 m 屬性裡 (JSON 格式包含 murl)
    a_elems = driver.find_elements(By.CSS_SELECTOR, "a.iusc")
    for a in a_elems:
        m = a.get_attribute('m')
        if not m:
            continue
        try:
            data = json.loads(m)
            url = data.get('murl') or data.get('turl')
            if url:
                imgs.add(url)
            if len(imgs) >= max_num:
                break
        except Exception:
            continue
    # 若數量仍不足，嘗試抓取 img 標籤的 src / data-src
    if len(imgs) < max_num:
        for img in driver.find_elements(By.CSS_SELECTOR, "img"):
            src = img.get_attribute('src') or img.get_attribute('data-src') or img.get_attribute('data-stk')
            if not src:
                continue
            if src.startswith('data:'):
                continue
            imgs.add(src)
            if len(imgs) >= max_num:
                break
    return list(imgs)[:max_num]

def download_image(url, dest_path, timeout=10):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=timeout, stream=True)
        resp.raise_for_status()
        content_type = resp.headers.get('content-type', '')
        ext = None
        if 'jpeg' in content_type or 'jpg' in content_type:
            ext = '.jpg'
        elif 'png' in content_type:
            ext = '.png'
        elif 'gif' in content_type:
            ext = '.gif'
        else:
            # 嘗試從 url 推斷副檔名
            path = urllib.parse.urlparse(url).path
            _, e = os.path.splitext(path)
            ext = e if e else '.jpg'
        with open(dest_path + ext, 'wb') as f:
            for chunk in resp.iter_content(1024):
                f.write(chunk)
        return True
    except Exception:
        return False

driver = setup_driver(headless=True)
max_num = int(input('請輸入欲下載圖片數量 (預設 500): ') or "500")
for kw in keywords:
    safe_folder = re.sub(r'[^0-9A-Za-z\u4e00-\u9fff\-_\. ]+', '_', kw)
    safe_folder = safe_folder.replace(' ', '_')[:100]
    folder_path = os.path.join(OUT_ROOT, safe_folder)
    os.makedirs(folder_path, exist_ok=True)

    print(f'搜尋並下載: "{kw}" -> {folder_path}')
    query = urllib.parse.quote_plus(kw)
    search_url = f'https://www.bing.com/images/search?q={query}&form=HDRSC2'
    try:
        driver.get(search_url)
        time.sleep(1.0)
        # 多次滾動以載入更多圖片
        scroll_to_bottom(driver, pause=1.0, max_scrolls=40)
        # 有些情況需要按 "顯示更多" 的按鈕
        try:
            more = driver.find_element(By.CSS_SELECTOR, "a.btn_seemore")
            if more:
                more.click()
                time.sleep(1.0)
                scroll_to_bottom(driver, pause=1.0, max_scrolls=20)
        except Exception:
            pass
          
        urls = extract_bing_image_urls(driver, max_num=max_num)
        print(f'擷取到 {len(urls)} 張候選圖 URL')
        count = 0
        for idx, url in enumerate(urls):
            # 過濾不合法或過短的 url
            if not url or len(url) < 10:
                continue
            fname = f'{idx:04d}'
            dest = os.path.join(folder_path, fname)
            ok = download_image(url, dest)
            if ok:
                count += 1
            # 簡單限制下載速率
            time.sleep(0.1)
        print(f'完成: {kw}，實際下載 {count} 張圖片')
    except Exception as e:
        print(f'對 "{kw}" 下載發生錯誤: {e}')

driver.quit()
# ...existing code...