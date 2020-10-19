#!/usr/bin/env bash

git pull
nohup gunicorn server.wsgi --bind=0:20011 &
