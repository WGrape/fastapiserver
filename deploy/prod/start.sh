#!/usr/bin/env bash
# 生产环境启动脚本
cd /app || exit 1
exec gunicorn src.cmd.main:app -c gunicorn_config.py
