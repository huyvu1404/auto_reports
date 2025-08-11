import os
import sys
import shutil
import asyncio
from pydantic import BaseModel
from dotenv import load_dotenv
from browser_use import Agent, BrowserSession, Controller

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from utils import prepare_temp_chrome_profile
from constants import TEMP_USER_DATA_DIR, DOWNLOAD_PATH, CONVERSATION_PATH, PROMPT_TEMPLATE, INITIAL_ACTIONS
load_dotenv()

class SlidesInfo(BaseModel):
    name: str
    content: str
class FileStatus(BaseModel):
    name: str
    status: str

controller = Controller(output_model=FileStatus)

async def create_agent(**kwargs):
    prepare_temp_chrome_profile()

    browser_session = BrowserSession(
        stealth=True,
        headless=kwargs.get("headless", False),
        channel='chromium',
        wait_for_network_idle_page_load_time=3.0,
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
        highlight_elements=True,
        viewport_expansion=500,
        disable_security=False,
        accept_downloads=True,
        downloads_path=DOWNLOAD_PATH,
        user_data_dir=TEMP_USER_DATA_DIR,
        default_timeout=60000
    )
    await browser_session.start()
    page = await browser_session.get_current_page()
    
    llm = kwargs.get("llm")
    if not llm:
        raise ValueError("LLM must be provided.")

    task = PROMPT_TEMPLATE.format(
        google_account=os.getenv("GOOGLE_ACCOUNT"),
        url=kwargs.get("url", ""),
        task=kwargs.get("task", "")
    )

    agent = Agent(
        task=task,
        llm=llm,
        page=page,
        initial_actions=INITIAL_ACTIONS,
        browser_session=browser_session,
        controller=controller,
        max_actions_per_step=6,
        max_failures=6,
        retry_delay=5,
        save_conversation_path=CONVERSATION_PATH,
        llm_timeout=30
    )
    return agent

    
# async def init_agent(task, url, llm, headless=False):
#     controller = Controller(output_model=FileStatus)
#     initial_actions = [
#         {'go_to_url': {'url': 'https://www.google.com', 'new_tab': True}},
#     ]   

#     browser_session = BrowserSession(
#         stealth=True,
#         headless=headless,
#         channel='chromium',
#         wait_for_network_idle_page_load_time=3.0,
#         user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36',
#         highlight_elements=True,
#         viewport_expansion=500,
#         disable_security=False,
#         accept_downloads=True,
#         downloads_path=os.path.join(utils.ROOT_PROJECT_PATH, 'tmp/files'),
#         user_data_dir=TEMP_USER_DATA_DIR,
#         default_timeout=60000
#     )
#     await browser_session.start()
#     page = await browser_session.get_current_page()
    
#     prompt = PROMP_TEMPLATE.format(google_account=os.getenv("GOOGLE_ACCOUNT"), task=task, url=url)
#     return Agent(
#         task=prompt,
#         llm=llm,
#         page=page,
#         initial_actions=initial_actions,
#         browser_session=browser_session,
#         controller=controller,
#         max_actions_per_step=6,
#         max_failures=6,
#         retry_delay=5,
#         save_conversation_path= os.path.join(utils.ROOT_PROJECT_PATH, 'tmp/log'),
#         llm_timeout=30
#     )


