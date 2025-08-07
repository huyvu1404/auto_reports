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
   
PROMP_TEMPLATE = """
Go to {url} and check if the content is accessible. If not, return empty name with "Access Denied" status.
If the content is accessible, follow these steps to complete the task:
Your task includes the following steps. Please follow them in order and read all notes carefully:

+ Step 1: Go to https://www.manus.im/app and wait for the main page to fully load. Then click "Sign in" if required. If you are already signed in, proceed to Step 4.
+ Step 2: In the `Sign In` window, click "Sign in with Google". From the list of accounts, select the one with the email address {google_account}.
+ Step 3: Once you have successfully logged in, wait a moment for a popup to appear. Click "Close" or the "X" in the top-right corner to dismiss it.
+ Step 4: Wait for the page to fully load. On the main page of manus.im, click to focus on the text area, type "Hello", then delete everything.
+ Step 5: Paste the following content into the text area in full: `{task}`. Then Press the **Space** key once. After that, click again into the text area, then press **Enter** to send the prompt.
+ Step 6: Wait for manus.im to generate the report (this may take a few minutes). Once complete, the site will notify you — you do not need to perform any action during this time.

After manus.im successfully generates the report, your new task is as follows. Again, follow the steps in order and read the notes carefully:

+ Step 1: Wait for the page to fully load. Then click "Sign in with Google". Wait for any popups to appear, and close them if necessary.
+ Step 2: Navigate to https://manus.im/app/OmZGyhz5QM56WnwTrvUOY2 and wait for the page to fully load. Locate and click "View all files in this task".
+ Step 3: Click `Batch download` at the top of the popup (index 0). In the selection window, choose only the presentation file and click "Batch download".
+ Step 4: Return the **name** of the presentation file and its **status**.

IMPORTANT NOTES:
- While waiting for Manus to process the file, **DO NOT** perform any actions — this is necessary to preserve the session token.
- Follow the instructions carefully to find the correct buttons and elements.
- If you cannot find a required element or button, **STOP immediately**.

"""

async def init_agent(task, url, llm, headless=False):
    controller = Controller(output_model=FileStatus)
    initial_actions = [
        {'go_to_url': {'url': 'https://www.google.com', 'new_tab': True}},
    ]   

    browser_session = BrowserSession(
        stealth=True,
        headless=headless,
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
    
    prompt = PROMP_TEMPLATE.format(google_account=os.getenv("GOOGLE_ACCOUNT"), task=task, url=url)
    return Agent(
        task=prompt,
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


