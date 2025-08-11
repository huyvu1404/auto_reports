import os
import sys
import uuid
import time
import streamlit as st
from dotenv import load_dotenv
from browser_use.llm import ChatGoogle
from .agents import create_agent, FileStatus
from .storage import MinioClient
from psycopg2 import connect, sql

load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from constants import DOWNLOAD_PATH
from utils import clear_temp_directories


# Hàm xử lý đăng ký
import bcrypt

def register_user(conn, username, password):
    # 1. Validate input
    if not username or not password:
        return False, "Username and password cannot be empty."
    if len(username) < 3 or len(password) < 6:
        return False, "Username must be at least 3 characters and password at least 6 characters long."
    if not username.isalnum():
        return False, "Username must be alphanumeric."
    if not password.isalnum():
        return False, "Password must be alphanumeric."
    with conn.cursor() as cursor:
        try:
            # 2. Kiểm tra xem username đã tồn tại trong db chưa
            existing_user = cursor.execute(
                "SELECT 1 FROM users WHERE username = %s",
                [username]
            )
            if existing_user:
                cursor.close()
                return False, "Username already exists."

            # 3. Hash mật khẩu trước khi lưu
            password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

            # 4. Lưu vào 
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                [username, password_hash]
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False

def login_user(conn, username, password):
    # 1. Kiểm tra input
    if not username or not password:
        return False, "Username and password cannot be empty."

    with conn.cursor() as cursor:
        # 2. Kiểm tra xem username có tồn tại không
        cursor.execute(
            "SELECT password_hash FROM users WHERE username = %s",
            [username]
        )
        result = cursor.fetchone()
        if not result:
            return False, "Invalid username or password."
        stored_hash = result[0]  # lấy giá trị password_hash
        # 3. Kiểm tra mật khẩu
        if bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            # Lấy user ID để lưu hoạt động
            cursor.execute(
                "SELECT id FROM users WHERE username = %s",
                [username]
            )
            user_id = cursor.fetchone()[0]
            st.session_state["user_id"] = user_id
            return True, "Login successful."
        else:
            return False, "Invalid username or password."
def go_to(page):
    st.session_state.page = page
    st.rerun()

def save_user_activity(conn, user_id, prompt):
    with conn.cursor() as cursor:
        try:
            cursor.execute(
                "INSERT INTO user_activity (user_id, prompt) VALUES (%s, %s)",
                (user_id, prompt)
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error saving user activity: {e}")
# UI xác thực
def authentication_block():
    with connect(
        dbname=os.getenv('POSTGRES_DB', 'default_db'),
        user=os.getenv('POSTGRES_USER', 'default_user'),    
        password=os.getenv('POSTGRES_PASSWORD', 'default_password'),
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', 5432)
    ) as conn:
        if not st.session_state.get("logged_in", False):
            st.subheader("Login or Register")
            tab_login, tab_register = st.tabs(["Login", "Register"])
            
            with tab_login:
                login_user_input = st.text_input("Username", key="login_username")
                login_pass_input = st.text_input("Password", type="password", key="login_password")
                if st.button("Login"):
                    ok, msg = login_user(conn, login_user_input, login_pass_input)
                    if ok:
                        st.success(msg)
                        go_to("main")
                    else:
                        st.error(msg)
                    # st.info(msg)
            
            with tab_register:
                reg_user_input = st.text_input("New Username", key="register_username")
                reg_pass_input = st.text_input("New Password", type="password", key="register_password")
                if st.button("Register"):
                    ok = register_user(conn, reg_user_input, reg_pass_input)
                    if ok:
                        st.success("Registration successful! Please log in.")
                        # go_to("login")
                    else:
                        st.error("Registration failed. Username may already exist or input is invalid.")
            
            return False
        else:
            st.success(f"Logged in as: {st.session_state['username']}")
            if st.button("Logout"):
                st.session_state["logged_in"] = False
                st.rerun()
            return True


async def create_app(headless=False):
    st.title("Report Automation Agent")

    # Kiểm tra đăng nhập
    if not authentication_block():
        return  # Nếu chưa login thì dừng

    st.write("This app automates the process of reporting tasks using a browser agent.")
    st.write("Please enter Google Docs URL. Make sure that the URL is accessible and contains the necessary data for the task.")
    st.text_area("Enter URL to data source:", key="data_source_url", height=50)
    url = st.session_state.get("data_source_url", "").strip() 

    report_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, url))
    client = MinioClient()
    bucket_name = "reports"
    if client.create_bucket(bucket_name):
        # Kiểm tra xem báo cáo đã tồn tại trong Minio chưa và lấy đường dẫn để tải file
        
        objects = list(client.list_objects(bucket_name, prefix=None, recursive=True))
        if objects:
            st.write(f"Report for URL '{url}' already exists. Downloading the file...")
            # Không cần tạo lại agent nếu đã có báo cáo 
            existing_file = objects[0].object_name
            local_path = os.path.join(DOWNLOAD_PATH, os.path.basename(existing_file))
            if client.get_file_from_minio(bucket_name, existing_file, local_path):
                with open(local_path, "rb") as f:
                    downloaded = st.download_button(
                        label="⬇️ Download file",
                        data=f,
                        file_name=os.path.basename(existing_file),
                        mime="application/octet-stream",
                        key="download_btn"
                    )

                # Khi người dùng bấm nút download
                if downloaded:
                    st.session_state["file_downloaded"] = True
                    st.rerun()

            # Sau khi rerun, hiển thị thông báo và reset state
            if st.session_state.get("file_downloaded", False):
                st.success("✅ File đã được tải về!")
                st.session_state["file_downloaded"] = False
            st.stop()

        
    st.write("Please enter the task details below:")
    st.text_area("Task Description:", key="task_description", height=200)
    task = st.session_state.get("task_description", "").strip()

    if task:
        button = st.button("Submit Task")
        if button:
            clear_temp_directories()
            # Lưu hoạt động người dùng
            with connect(
                dbname=os.getenv('POSTGRES_DB', 'default_db'),
                user=os.getenv('POSTGRES_USER', 'default_user'),
                password=os.getenv('POSTGRES_PASSWORD', 'default_password'),
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=os.getenv('POSTGRES_PORT', 5432)
            ) as conn:
                save_user_activity(conn, st.session_state["user_id"], task)

            llm = ChatGoogle(model="gemini-2.5-flash", temperature=1.0)
            agent = await create_agent(task=task, url=url, llm=llm, headless=headless)
            history = await agent.run()
    
            if history.is_done():
                st.success("Task completed!")
                result = history.final_result()
                if result:
                    parsed: FileStatus = FileStatus.model_validate_json(result)
                    file_name = parsed.name
                    if file_name:
                        st.write(f"Downloaded file {file_name} successfully")                    
                        file_path = os.path.join(DOWNLOAD_PATH, file_name)

                        object_name = f"{report_uuid}/{file_name}"
                        if client.upload_file_to_minio(bucket_name, file_path, object_name):
                            with open(file_path, "rb") as f:
                              downloaded = st.download_button(
                                    label="⬇️ Download file",
                                    data=f,
                                    file_name=file_name,
                                    # file_name=f"{report_uuid}_{file_name}",
                                    mime="application/octet-stream",
                                    key="download_btn"
                                )

                            # Khi người dùng bấm nút download
                            if downloaded:
                                st.session_state["file_downloaded"] = True
                                st.rerun()
                        else:
                            st.error("Failed to upload file to MinIO.")
                        # Sau khi rerun, hiển thị thông báo và reset state
                        if st.session_state.get("file_downloaded", False):
                            st.success("✅ File đã được tải về!")
                            st.session_state["file_downloaded"] = False
                        st.stop()  

                    else:
                        st.error("Access Denied or no file found.")
            else:
                st.error("No result found.")
    else:
        st.error("Please enter a task.")
