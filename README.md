Example of [Starlette](https://www.starlette.io/) Q&A application made with [Tortoise ORM](https://tortoise-orm.readthedocs.io/en/latest/) and PostgreSQL.

Open terminal and run:

```shell
virtualenv -p python3 envname
cd envname
source bin/activate
git clone https://github.com/sinisaos/starlette-tortoise.git
cd starlette-tortoise
pip install -r requirements.txt
sudo -i -u yourpostgresusername psql
CREATE DATABASE questions;
\q
touch .env
## put this two line in .env file
## DB_URI="postgres://username:password@localhost:5432/questions"
## SECRET_KEY="your secret key"
uvicorn app:app --port 8000 --host 0.0.0.0 
```

For Heroku deployment change DB_URI in .env file and BASE_HOST in settings.py and everything shoud be fine.