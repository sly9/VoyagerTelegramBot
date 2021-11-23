@echo off
set "$py=0"
call:construct

for /f "delims=" %%a in ('python #.py ^| findstr "2"') do set "$py=2"
for /f "delims=" %%a in ('python #.py ^| findstr "3"') do set "$py=3"
del #.py
goto:%$py%

echo python is not installed or python's path Path is not in the %%$path%% env. var
echo Please install latest python distribution from windows store: https://go.microsoft.com/fwlink?linkID=2082640
start "" https://go.microsoft.com/fwlink?linkID=2082640
echo Press enter to exit
set /p input=

exit/b

:2
echo running with PY 2
echo Python 2 is installed, but we only support python 3.7 and above.
echo Please install latest python distribution from windows store: https://go.microsoft.com/fwlink?linkID=2082640
start "" https://go.microsoft.com/fwlink?linkID=2082640
echo Press enter to exit
set /p input=
exit/b

:3
echo running with PY 3
pip3 install -r requirements.txt

if exist config.yml (
    python3 bot.py
) else (
    echo Please make a copy of config.yml.example, and name it config.yml in the same folder.
    echo Then update the configuration with your voyager connection info and telegram bot tokens.
    echo Press enter to exit
    set /p input=
)

exit/b

:construct
echo import sys; print('{0[0]}.{0[1]}'.format(sys.version_info^)^) >#.py

