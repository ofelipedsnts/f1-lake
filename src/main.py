#%%
import datetime
import os
import dotenv
import time
from pathlib import Path

from collect import Collect
from load import Load

#%%
dotenv.load_dotenv()

AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")
AWS_S3_BUCKET_FOLDER = os.getenv("AWS_S3_BUCKET_FOLDER")

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT/"data"
# %%
year = datetime.datetime.now().year
data_dir = DATA_DIR


while True:

    print('Iniciando coleta dos dados')
    collect_data = Collect(years=[year], modes=["R", "S"])
    collect_data.process_years()
    print('coleta dos dados finalizada')

    print("Iniciando carregamento dos dados")
    load_data = Load(AWS_S3_BUCKET_NAME, AWS_S3_BUCKET_FOLDER)
    load_data.proccess_data(data_dir)
    print("Carregamento dos dados finalizado")

    print("Interação finalizada")
    time.sleep(60*60*120)

# %%
