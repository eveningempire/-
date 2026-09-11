import os

# 基础路径配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_STORAGE_PATH = os.path.join(BASE_DIR, 'static', 'data')
TRAIN_DATA_PATH = os.path.join(DATA_STORAGE_PATH, 'traindata')
TEST_DATA_PATH = os.path.join(DATA_STORAGE_PATH, 'testdata')
MODEL_PATH = os.path.join(BASE_DIR, 'predict', 'model')
ROAMING_DIR = os.path.join(BASE_DIR, "static", "roaming")

# 创建必要的目录
for path in [TRAIN_DATA_PATH, TEST_DATA_PATH, MODEL_PATH, ROAMING_DIR]:
    if not os.path.exists(path):
        os.makedirs(path)

# 应用配置
TIME_RESAMPLE = 0.125
FILL_MAX = 100
WASH_ABS = 1E20
WORKER_NUM = 5

# 上传文件配置
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
