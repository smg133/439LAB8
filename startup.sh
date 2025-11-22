#!/bin/bash
python manage.py collectstatic --noinput
gunicorn mysite1.wsgi --bind=0.0.0.0:$PORT
