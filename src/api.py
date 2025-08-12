from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from .agents import create_agent, FileStatus
from .storage import MinioClient
from browser_use.llm import ChatGoogle
import os
import sys
from psycopg2 import connect
import uuid
import bcrypt

from pydantic import BaseModel

class ReportRequest(BaseModel):
    url: str
    task: str

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from constants import DOWNLOAD_PATH
from utils import clear_temp_directories

security = HTTPBasic()


def verify_user(credentials: HTTPBasicCredentials = Depends(security)):
    username = credentials.username
    password = credentials.password

    with connect(
        dbname=os.getenv('POSTGRES_DB', 'default_db'),
        user=os.getenv('POSTGRES_USER', 'default_user'),
        password=os.getenv('POSTGRES_PASSWORD', 'default_password'),
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', 5432)
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT password_hash FROM users WHERE username = %s",
                (username,)
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=401, detail="Invalid username or password")
            
            stored_hash = row[0]
            if not bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
                raise HTTPException(status_code=401, detail="Invalid username or password")

    return username


def create_api() -> FastAPI:
    app = FastAPI()

    @app.post("/generate-report")
    async def generate_report(body: ReportRequest, user: str = Depends(verify_user)):
        if not body:
            raise HTTPException(status_code=400, detail="URL and task are required")
        url, task = body.url, body.task
        with connect(
            dbname=os.getenv('POSTGRES_DB', 'default_db'),
            user=os.getenv('POSTGRES_USER', 'default_user'),
            password=os.getenv('POSTGRES_PASSWORD', 'default_password'),
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', 5432)
        ) as conn:
            try:
                report_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, url))
                client = MinioClient()
                bucket_name = "reports"

                if client.create_bucket(bucket_name):
                    objects = list(client.list_objects(bucket_name, prefix=report_uuid, recursive=True))
                    if objects:
                        existing_file = objects[0].object_name
                        if os.getenv('MINIO_SECURE', 'false').lower() == 'true':
                            return {"status": "200", "url": f"https://{os.getenv('MINIO_ENDPOINT', 'localhost:9000')}/{bucket_name}/{existing_file}"}
                        else:
                            return {"status": "200", "url": f"http://{os.getenv('MINIO_ENDPOINT', 'localhost:9000')}/{bucket_name}/{existing_file}"}

                clear_temp_directories()
                llm = ChatGoogle(model="gemini-2.5-flash", temperature=1.0)
                agent = await create_agent(
                    url=url,
                    task=task,
                    llm=llm,
                    headless=False
                )

                history = await agent.run()

                if history.is_done():
                    result = history.final_result()
                    if result:
                        parsed: FileStatus = FileStatus.model_validate_json(result)
                        file_name = parsed.name
                        if file_name:
                            file_path = os.path.join(DOWNLOAD_PATH, file_name)
                            if client.upload_file_to_minio(bucket_name, file_path, object_name=file_name):
                                if os.getenv('MINIO_SECURE', 'false').lower() == 'true':
                                    return {"status": "200", "url": f"https://{os.getenv('MINIO_ENDPOINT', 'localhost:9000')}/{bucket_name}/{file_name}"}
                                else:
                                    return {"status": "200", "url": f"http://{os.getenv('MINIO_ENDPOINT', 'localhost:9000')}/{bucket_name}/{file_name}"}
                            else:
                                raise HTTPException(status_code=500, detail="Failed to upload file to MinIO")
                        else:
                            return {"status": "200", "message": "No file generated", "url": ""}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error creating agent: {str(e)}")

    return app
# Run app 
