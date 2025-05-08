@echo off
cd /d %~dp0

:: 激活 conda daily 环境并运行脚本
call conda activate daily
python update_dns.py 