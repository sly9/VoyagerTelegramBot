@echo off

RMDIR /S /Q dist
RMDIR /S /Q build

WHERE pyinstaller
IF %ERRORLEVEL% NEQ 0 (
    ECHO "pyinstaller wasn't found, try to install it via pip3 now"
    pip3 install pyinstaller
) ELSE (
    pyinstaller -F bot.spec
)

