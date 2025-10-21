@echo off
echo Activating environment...
call env\Scripts\activate
python formserver.py
echo To activate the environment in the future, run: env\Scripts\activate
call env\Scripts\deactivate
pause