@echo off
chcp 65001
cd /d "%~dp0"
git add .
git commit -m "Исправление: загрузка модели ASIC из БД при перерасчете"
git remote set-url origin https://github.com/Andhanc/botfinale.git
git push -u origin main
pause

