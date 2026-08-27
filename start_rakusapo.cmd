@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 -m pip install -q -r rakusapo_requirements.txt
  py -3 -m streamlit run rakusapo_app.py --server.headless false --browser.gatherUsageStats false
  goto :eof
)
where python >nul 2>nul
if %errorlevel%==0 (
  python -m pip install -q -r rakusapo_requirements.txt
  python -m streamlit run rakusapo_app.py --server.headless false --browser.gatherUsageStats false
  goto :eof
)
echo Python が見つかりません。https://www.python.org/downloads/ からインストールしてください。
pause
