import os
import sys
import uuid
import streamlit as st
from dotenv import load_dotenv
from browser_use.llm import ChatGoogle
from .agents import BrowserAgent, FileStatus
from .storage import MinioClient

load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from constants import DOWNLOAD_PATH
from utils import clear_temp_directories


# Hàm xử lý đăng ký
def register_user(username, password):
    if "users" not in st.session_state:
        st.session_state["users"] = {}
    if username in st.session_state["users"]:
        return False, "Username already exists."
    st.session_state["users"][username] = password
    return True, "Registration successful."


# Hàm xử lý đăng nhập
def login_user(username, password):
    if "users" not in st.session_state:
        return False, "No users registered."
    if st.session_state["users"].get(username) == password:
        st.session_state["logged_in"] = True
        st.session_state["username"] = username
        return True, "Login successful."
    return False, "Invalid username or password."


# UI xác thực
def authentication_block():
    if not st.session_state.get("logged_in", False):
        st.subheader("User Authentication")
        tab_login, tab_register = st.tabs(["Login", "Register"])
        
        with tab_login:
            login_user_input = st.text_input("Username", key="login_username")
            login_pass_input = st.text_input("Password", type="password", key="login_password")
            if st.button("Login"):
                ok, msg = login_user(login_user_input, login_pass_input)
                st.info(msg)
        
        with tab_register:
            reg_user_input = st.text_input("New Username", key="register_username")
            reg_pass_input = st.text_input("New Password", type="password", key="register_password")
            if st.button("Register"):
                ok, msg = register_user(reg_user_input, reg_pass_input)
                st.info(msg)
        
        return False
    else:
        st.success(f"Logged in as: {st.session_state['username']}")
        if st.button("Logout"):
            st.session_state["logged_in"] = False
            st.experimental_rerun()
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
        objects = client.list_objects(bucket_name, prefix=report_uuid, recursive=True)
        has_prefix = any(True for _ in objects)
        if has_prefix:
            st.write(f"Report already exists in Minio bucket '{bucket_name}' with prefix: {report_uuid}")

    st.write("Please enter the task details below:")
    st.text_area("Task Description:", key="task_description", height=200)
    task = st.session_state.get("task_description", "").strip()

    if task:
        button = st.button("Submit Task")
        if button:
            clear_temp_directories()

            llm = ChatGoogle(model="gemini-2.5-flash", temperature=1.0)
            agent = await BrowserAgent.create(task=task, url=url, llm=llm, headless=headless)
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
                            st.write(f"File uploaded to MinIO bucket '{bucket_name}'")
                        else:
                            st.error("Failed to upload file to MinIO.")
                    else:
                        st.error("Access Denied or no file found.")
            else:
                st.error("No result found.")
    else:
        st.error("Please enter a task.")
