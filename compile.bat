@echo off

pip3 install -r requirements.txt
REM For Windows system, the following package is needed to hook terminal
pip3 install windows-curses

RMDIR /S /Q dist
RMDIR /S /Q build
RMDIR /S /Q __pycache__

WHERE pyinstaller
IF %ERRORLEVEL% NEQ 0 (
    ECHO "pyinstaller wasn't found, try to install it via pip3 now."
    pip3 install pyinstaller
    ECHO "pyinstaller was installed successfully, please restart the application."
)

pyinstaller bot.spec
