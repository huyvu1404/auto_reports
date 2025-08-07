from minio import Minio
from minio.error import S3Error
from dotenv import load_dotenv
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
load_dotenv()

MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minio')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minio123')

class MinioClient:
    """Singleton class to manage MinIO client connection."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MinioClient, cls).__new__(cls)
            cls._instance.client = Minio(
                MINIO_ENDPOINT,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=False
            )
        return cls._instance

    def upload_file_to_minio(self, bucket_name, file_path, object_name=None):
        """Upload a file to a MinIO bucket."""
        if object_name is None:
            object_name = os.path.basename(file_path)

        try:
            self.client.fput_object(bucket_name, object_name, file_path)
            print(f"File '{file_path}' uploaded to '{bucket_name}/{object_name}'")
        except S3Error as e:
            print(f"Error uploading file: {e}")
            return False
        return True

    def create_bucket(self, bucket_name):
        """Create a bucket in MinIO."""
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                print(f"Bucket '{bucket_name}' created")
            else:
                print(f"Bucket '{bucket_name}' already exists")
        except S3Error as e:
            print(f"Error creating bucket: {e}")
            return False
        return True

    def get_file_from_minio(self, bucket_name, object_name, file_path):
        """Download a file from a MinIO bucket."""
        try:
            self.client.fget_object(bucket_name, object_name, file_path)
            print(f"File '{object_name}' downloaded to '{file_path}'")
        except S3Error as e:
            print(f"Error downloading file: {e}")
            return False
        return True
    
    def list_objects(self, bucket_name, prefix='', recursive=True):
        """List objects in a MinIO bucket."""
        try:
            return self.client.list_objects(bucket_name, prefix=prefix, recursive=recursive)
        except S3Error as e:
            print(f"Error listing objects: {e}")
            return []
