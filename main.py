from src import create_app
import asyncio
import os
import sys
import utils
import shutil

TEMP_DIR_DATA = os.path.join(utils.ROOT_PROJECT_PATH, 'tmp/files')
TEMP_DIR_LOG = os.path.join(utils.ROOT_PROJECT_PATH, 'tmp/log')

def main():
    if os.path.exists(TEMP_DIR_DATA):
        shutil.rmtree(TEMP_DIR_DATA)
        print('Đã xóa thư mục tạm thời cũ')
    if os.path.exists(TEMP_DIR_LOG):
        shutil.rmtree(TEMP_DIR_LOG)
        print('Đã xóa thư mục log cũ')
    os.makedirs(TEMP_DIR_DATA, exist_ok=True)
    os.makedirs(TEMP_DIR_LOG, exist_ok=True)

    asyncio.run(create_app())

if __name__ == "__main__":
    main()
