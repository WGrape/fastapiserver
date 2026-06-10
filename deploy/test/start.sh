#!/usr/bin/env bash
# 测试环境启动脚本
cd /app || exit 1
exec gunicorn src.cmd.main:app -c gunicorn_config.py
