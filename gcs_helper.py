from google.cloud import storage
import os
from werkzeug.utils import secure_filename
import tempfile

class GoogleCloudStorage:
    def __init__(self, bucket_name):
        self.client = storage.Client()
        self.bucket_name = bucket_name
        self.bucket = self.client.bucket(bucket_name)
    
    def upload_file(self, file, filename, folder='uploads'):
        """Upload a file to Google Cloud Storage"""
        try:
            # Secure the filename
            filename = secure_filename(filename)
            
            # Create blob path
            blob_path = f"{folder}/{filename}"
            blob = self.bucket.blob(blob_path)
            
            # Upload file
            blob.upload_from_file(file)
            
            # Return the public URL
            return f"gs://{self.bucket_name}/{blob_path}"
            
        except Exception as e:
            print(f"Error uploading file: {e}")
            return None
    
    def download_file(self, blob_path, local_path):
        """Download a file from Google Cloud Storage"""
        try:
            blob = self.bucket.blob(blob_path)
            blob.download_to_filename(local_path)
            return local_path
        except Exception as e:
            print(f"Error downloading file: {e}")
            return None
    
    def delete_file(self, blob_path):
        """Delete a file from Google Cloud Storage"""
        try:
            blob = self.bucket.blob(blob_path)
            blob.delete()
            return True
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
    
    def list_files(self, folder='uploads'):
        """List files in a folder"""
        try:
            blobs = self.client.list_blobs(self.bucket_name, prefix=folder)
            return [blob.name for blob in blobs]
        except Exception as e:
            print(f"Error listing files: {e}")
            return []

# Usage example for your routes
def save_uploaded_file(file, filename, folder='uploads'):
    """Save file to Google Cloud Storage or local storage based on environment"""
    bucket_name = os.getenv('GCS_BUCKET_NAME')
    
    if bucket_name:
        # Use Google Cloud Storage
        gcs = GoogleCloudStorage(bucket_name)
        return gcs.upload_file(file, filename, folder)
    else:
        # Use local storage (for development)
        upload_folder = os.getenv('UPLOAD_FOLDER', 'uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        file_path = os.path.join(upload_folder, secure_filename(filename))
        file.save(file_path)
        return file_path