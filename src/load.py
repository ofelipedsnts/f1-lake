#%%
import dotenv
import os
import boto3
import argparse
from pathlib import Path
from tqdm import tqdm

dotenv.load_dotenv()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT/"data"

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

    def upload_file(self, filename, folder):
        local_path = f"{folder}/{filename}"
        s3_key = f"{self.bucket_folder}/{filename}"

        print(f"Enviando {filename}")

        try:
            self.s3.upload_file(
                local_path,
                self.bucket_name, 
                s3_key
            )
            print(f"✓ {filename} enviado com sucesso")

        except Exception as err:
            print(f"✗ Erro ao enviar {filename}: {err}")
            return False

        os.remove(local_path)
        print(f"✓ {filename} removido localmente")

        return True
    
    def proccess_data(self, folder):
        print(f"Procurando arquivos em: {folder}")
        files = os.listdir(folder)
        print(f"Encontrados {len(files)} arquivos")

        for f in tqdm(files):
            self.upload_file(f, folder)
# %%
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket_name", type=str)
    parser.add_argument("--folder", type=str)
    args = parser.parse_args()

    if args.bucket_name:
        print("Iniciando importação dos dados")

        load = Load(
            args.bucket_name, 
            args.folder
        )

        load.proccess_data(DATA_DIR)

        print("Importação dos dados concluída")

    else:
        print("Sem bucket definido")
