import os
import shutil
from constants import ROOT_PROJECT_PATH, TEMP_USER_DATA_DIR, USER_DATA_DIR

def clear_temp_directories():
    """Clear temporary directories."""
    
    temp_dirs = [os.path.join(ROOT_PROJECT_PATH, 'tmp/files'), 
                 os.path.join(ROOT_PROJECT_PATH, 'tmp/log')]
    for temp_dir in temp_dirs:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f'Deleted old temporary directory: {temp_dir}')
        os.makedirs(temp_dir, exist_ok=True)

def prepare_temp_chrome_profile():
    if os.path.exists(TEMP_USER_DATA_DIR):
        shutil.rmtree(TEMP_USER_DATA_DIR)
        print('Đã xóa thư mục temp-chrome-profile cũ')

    shutil.copytree(USER_DATA_DIR, TEMP_USER_DATA_DIR)
    print('Đã sao chép user data từ chrome-profile sang temp-chrome-profile')

