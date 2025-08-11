import os

# Constants for project paths and directories
ROOT_PROJECT_PATH = os.path.dirname(__file__)
USER_DATA_DIR = os.path.join(ROOT_PROJECT_PATH, 'browsers/chromium/user_data')
TEMP_USER_DATA_DIR = os.path.join(ROOT_PROJECT_PATH, 'browsers/chromium/temp_user_data')
DOWNLOAD_PATH = os.path.join(ROOT_PROJECT_PATH, 'tmp/files')
CONVERSATION_PATH = os.path.join(ROOT_PROJECT_PATH, 'tmp/log')

# Constants for prompt templates
PROMPT_TEMPLATE = """
Go to {url} and check if the content is accessible. If not, return empty name with "Access Denied" status.
If the content is accessible, follow these steps to complete the task:
Your task includes the following steps. Please follow them in order and read all notes carefully:

+ Step 1: Go to https://www.manus.im/app and wait for the main page to fully load. Then click "Sign in" if required. If you are already signed in, proceed to Step 4.
+ Step 2: In the `Sign In` window, click "Sign in with Google". From the list of accounts, select the one with the email address {google_account}.
+ Step 3: Once you have successfully logged in, wait a moment for a popup to appear. Click "Close" or the "X" in the top-right corner to dismiss it.
+ Step 4: Wait for the page to fully load. On the main page of manus.im, click to focus on the text area, type "Hello", then delete everything.
+ Step 5: Paste the following content into the text area in full: `Đọc dữ liệu từ {url}. {task}`. Then Press the **Space** key once. After that, click again into the text area, then press **Enter** to send the prompt.
+ Step 6: Wait for manus.im to generate the report (this may take a few minutes). Once complete, the site will notify you — you do not need to perform any action during this time.

After manus.im successfully generates the report, your new task is as follows. Again, follow the steps in order and read the notes carefully:

+ Step 1: Once the report has been created successfully, locate and click "View all files in this task".
+ Step 2: Click `Batch download` at the top-right with index = 0. In the selection window, choose only the presentation file and click "Batch download".
+ Step 3: If downloaded successfully, return the **name** of the presentation file with status "Downloaded successfully". Otherwise, return "Download failed" with an empty name.

IMPORTANT NOTES:
- While waiting for Manus to process the file, **DO NOT** perform any actions — this is necessary to preserve the session token.
- Follow the instructions carefully to find the correct buttons and elements.
- If you cannot find a required element or button, **STOP immediately**.

"""

# Initial actions for the browser agent
INITIAL_ACTIONS = [
    {'go_to_url': {'url': 'https://www.google.com', 'new_tab': True}},
]

