import os
import sys
import shutil
from pydantic import BaseModel
from dotenv import load_dotenv
from browser_use import Agent, BrowserSession, Controller
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import utils
load_dotenv()

USER_DATA_DIR = os.path.join(utils.ROOT_PROJECT_PATH, 'browsers/chromium/user_data')
TEMP_USER_DATA_DIR = os.path.join(utils.ROOT_PROJECT_PATH, 'browsers/chromium/temp_user_data')

if os.path.exists(TEMP_USER_DATA_DIR):
    shutil.rmtree(TEMP_USER_DATA_DIR)
    print('Đã xóa thư mục temp-chrome-profile cũ')

shutil.copytree(USER_DATA_DIR, TEMP_USER_DATA_DIR)
print('Đã sao chép user data từ chrome-profile sang temp-chrome-profile')

class SlidesInfo(BaseModel):
    name: str
    content: str

class FileStatus(BaseModel):
    name: str
    status: str
   

async def init_agent(task, llm, headless=False):
    controller = Controller(output_model=FileStatus)
    initial_actions = [
        {'go_to_url': {'url': 'https://www.google.com', 'new_tab': True}},
        {'go_to_url': {'url': 'https://www.manus.im/app', 'new_tab': False}},
     
    ]   

    browser_session = BrowserSession(
        stealth=True,
        headless=False,
        storage_stage='./storage_stage.json',
        channel='chromium',
        execute_path='/snap/bin/chromium',
        wait_for_network_idle_page_load_time=3.0,
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
        highlight_elements=True,
        viewport_expansion=500,
        disable_security=False,
        accept_downloads=True,
        downloads_path=os.path.join(utils.ROOT_PROJECT_PATH, 'tmp/files'),
        user_data_dir=TEMP_USER_DATA_DIR,
        default_timeout=60000
    )
    await browser_session.start()
    page = await browser_session.get_current_page()
    return Agent(
        task=task,
        llm=llm,
        page=page,
        initial_actions=initial_actions,
        browser_session=browser_session,
        controller=controller,
        max_actions_per_step=6,
        max_failures=6,
        retry_delay=5,
        save_conversation_path= os.path.join(utils.ROOT_PROJECT_PATH, 'tmp/log'),
        llm_timeout=30
    )


