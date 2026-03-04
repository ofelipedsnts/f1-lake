#%%
import dotenv
import os
import boto3
from tqdm import tqdm

dotenv.load_dotenv()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")

#%%
class Load:
    def __init__(self, bucket_name, bucket_folder):
        self.bucket_name = bucket_name
        self.bucket_folder = bucket_folder

        self.s3 = boto3.client(
            "s3",
            aws_access_key_id = AWS_ACCESS_KEY,
            aws_secret_access_key = AWS_SECRET_KEY,
            region_name = "us-east-2"
        )

    def upload_file(self, filename):
        try:
            self.s3.upload_file(
                f"../data/{filename}",
                self.bucket_name, 
                f"{self.bucket_folder}/{filename}"
            )

        except Exception as err:
            print(err)
            return False

        os.remove(f"../data/{self.local_filename}")

        return True
    
    def proccess_data(self, folder):
        files = os.listdir(folder)

        for f in tqdm(files):
            self.upload_file(f)
# %%
load = Load(
    "f1-lake-raw", 
    "results"
)
# %%
load.proccess_data("../data")
# %%
files = os.listdir("../data")
print(files)