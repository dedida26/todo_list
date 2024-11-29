Requirements
python -m venv --clear venv python -m pip install -r requirements.txt

Start Server

Dependencies (DB, Server)

docker compose up -d --build

Migrations

python manage.py makemigrations
python manage.py migrate

Server

python manage.py runserver 0.0.0.0:8000