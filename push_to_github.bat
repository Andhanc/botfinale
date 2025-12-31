@echo off
chcp 65001 >nul
echo ========================================
echo Загрузка проекта на GitHub
echo ========================================
echo.

cd /d "%~dp0"

echo Проверка статуса Git...
git status
echo.

echo Загрузка на GitHub...
git push -u origin main

if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo Ошибка при загрузке на GitHub
    echo ========================================
    echo.
    echo Возможные причины:
    echo 1. Не настроена аутентификация GitHub
    echo 2. Репозиторий не существует или нет доступа
    echo 3. Нужно выполнить: git push -u origin main
    echo.
    echo Для настройки аутентификации используйте:
    echo   git config --global user.name "Your Name"
    echo   git config --global user.email "your.email@example.com"
    echo.
    pause
    exit /b 1
) else (
    echo.
    echo ========================================
    echo Успешно загружено на GitHub!
    echo ========================================
    echo.
    echo Репозиторий: https://github.com/Andhanc/botfinale.git
    echo.
)

pause

