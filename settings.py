from starlette.config import Config
from starlette.templating import Jinja2Templates

# Configuration from environment variables or '.env' file.
config = Config(".env")
DB_URI = config("DB_URI")
SECRET_KEY = config("SECRET_KEY")
templates = Jinja2Templates(directory="templates")
BASE_HOST = "http://localhost:8000"
