import os
from utils import ROOT_PROJECT_PATH
import shutil
from browser_use import BrowserSession

def create_user_data_dir():
    user_data_dir = os.path.join(ROOT_PROJECT_PATH, 'browsers/chromium/user_data')
    if os.path.exists(user_data_dir):
        shutil.rmtree(user_data_dir)
        print('Đã xóa thư mục user_data cũ')
    os.makedirs(user_data_dir)
    print('Đã tạo thư mục user_data mới tại', user_data_dir)
    return user_data_dir

async def setup_browser_session():
    # user_data_dir = os.path.join(ROOT_PROJECT_PATH, 'browsers/chromium/user_data')
    user_data_dir = create_user_data_dir()
    browser_session = BrowserSession(
        stealth=True,
        headless=False,
        channel='chromium',
        wait_for_network_idle_page_load_time=3.0,
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
        highlight_elements=True,
        viewport_expansion=500,
        disable_security=False,
        accept_downloads=True,
        downloads_path=os.path.join(ROOT_PROJECT_PATH, 'tmp/files'),
        user_data_dir=user_data_dir,
        default_timeout=60000
    )
    await browser_session.start()
    page = await browser_session.get_current_page()
    await page.goto('https://www.google.com/')


if __name__ == "__main__":
    import asyncio
    asyncio.run(setup_browser_session())
