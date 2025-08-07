import os
import shutil

ROOT_PROJECT_PATH = os.path.dirname(__file__)

def clear_temp_directories():
    """Clear temporary directories."""
    
    temp_dirs = [os.path.join(ROOT_PROJECT_PATH, 'tmp/files'), 
                 os.path.join(ROOT_PROJECT_PATH, 'tmp/log')]
    for temp_dir in temp_dirs:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f'Deleted old temporary directory: {temp_dir}')
        os.makedirs(temp_dir, exist_ok=True)
