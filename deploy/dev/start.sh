#!/usr/bin/env bash

case "$APP_NAME" in
    *)
        exec gunicorn src.cmd.main:app -c gunicorn_config.py
        ;;
esac
