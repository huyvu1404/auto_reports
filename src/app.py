from browser_use.llm import ChatGoogle
from .agents import init_agent, FileStatus
from .storage import MinioClient
from dotenv import load_dotenv
load_dotenv()
import asyncio
import streamlit as st
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import utils

async def create_app():
    
    st.title("Report Automation Agent")
    st.write("This app automates the process of reporting tasks using a browser agent.")
    
    task = st.text_input("Enter your task:")
    if st.button("Start Agent"):
        if task:
            llm = ChatGoogle(model="gemini-2.5-flash", temperature=1.0)
            agent = await init_agent(task, llm, headless=True)
            history = await agent.run()
    
            if history.is_done():
                st.success("Agent completed successfully!")
                result = history.final_result()
                if result:
                    parsed: FileStatus = FileStatus.model_validate_json(result)
                    st.write(f"Downloaded file {parsed.name} successfully")
                    client = MinioClient()
                    bucket_name = "reports"
                    if client.create_bucket(bucket_name):
                        file_path = os.path.join(utils.ROOT_PROJECT_PATH, 'tmp/files', parsed.name)
                        if client.upload_file_to_minio(bucket_name, file_path, parsed.name):
                            st.write(f"File uploaded to MinIO bucket '{bucket_name}'")
                        else:
                            st.error("Failed to upload file to MinIO.")
            else:
                st.error("No result found.")
        else:
            st.error("Please enter a task.")

