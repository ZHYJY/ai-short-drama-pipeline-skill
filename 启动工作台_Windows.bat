@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 "asset-locked-storyboard-video\scripts\studio_server.py" --project "projects\我的短剧"
) else (
  python "asset-locked-storyboard-video\scripts\studio_server.py" --project "projects\我的短剧"
)
echo.
echo 如果无法启动，请确认已安装 Python 3.10+ 并加入 PATH。
pause
