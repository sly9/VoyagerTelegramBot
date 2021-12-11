RMDIR /S /Q dist
RMDIR /S /Q build
pyinstaller -F bot.spec

cd dist
bot.exe