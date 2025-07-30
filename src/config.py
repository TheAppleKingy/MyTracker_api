import os

from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '..', '../.env')
load_dotenv(env_path)

DATABASE_URL = os.getenv('DATABASE_URL')
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
FORMATTED_TEST_DATABASE_URL = os.getenv("FORMATTED_TEST_DATABASE_URL")
FORMATTED_DATABASE_URL = os.getenv("FORMATTED_DATABASE_URL")
SECRET_KEY = os.getenv('SECRET_KEY')
TOKEN_EXPIRE_TIME = int(os.getenv('TOKEN_EXPIRE_TIME'))
URL_EXPIRE_TIME = int(os.getenv('URL_EXPIRE_TIME'))
TOKEN_SALT = os.getenv('TOKEN_SALT')
QUEUE = os.getenv("TASK_SERVICE_QUEUE")
EMAIL_HOST = 'smtp.yandex.ru'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
FROM_EMAIL = EMAIL_HOST_USER
