apt update
apt install python3 python3-pip
gunicorn -w 4 -b 0.0.0.0:8000 bot:app
