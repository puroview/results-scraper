from google.cloud import storage

class Storage:
    def __init__(self, bucket_name, file_name, blob_name=None):

        self.bucket_name = bucket_name
        self.file_name = file_name
        if blob_name:
            self.blob_name = blob_name
        else:
            self.blob_name = file_name

        self.client = storage.Client()
        
    def upload_file(self):
        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(self.blob_name)
        blob.upload_from_filename(self.file_name, )
        url = blob.public_url
        
        return url