from browser_use.llm import ChatGoogle
from .agents import init_agent, FileStatus
from .storage import MinioClient
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import os
import sys
import uuid

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import utils

async def create_app(headless=False):
    
    st.title("Report Automation Agent")
    st.write("This app automates the process of reporting tasks using a browser agent.")
    # st.selectbox("Select Report Type:", ["Weekly", "Monthly", "Quarterly"], key="report_type")
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
            if task:
                # Clear temporary directories to store new data
                utils.clear_temp_directories()

                llm = ChatGoogle(model="gemini-2.5-flash", temperature=1.0)
                agent = await init_agent(task, url, llm, headless)
                history = await agent.run()
        
                if history.is_done():
                    st.success("Task completed!")
                    result = history.final_result()
                    if result:
                        parsed: FileStatus = FileStatus.model_validate_json(result)
                        file_name = parsed.name
                        if file_name:
                            st.write(f"Downloaded file {file_name} successfully")                    
                            file_path = os.path.join(utils.ROOT_PROJECT_PATH, 'tmp/files', )
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

