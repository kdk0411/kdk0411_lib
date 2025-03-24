@echo off
if not exist "config.ini" (
    echo config.ini 파일이 존재하지 않습니다.
    pause
    exit
)
if not exist "db_info.txt" (
    echo db_info.txt 파일이 존재하지 않습니다.
    pause
    exit
)
path %path%;c:\python34;c:\python34\scripts;c:\python38;c:\python38\scripts;
python main.py
pause
exit
