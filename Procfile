release: flask db upgrade
web: gunicorn cards_against_bubba.app:create_app\(\) -b 0.0.0.0:$PORT -w 3
