@echo off
chcp 65001 >nul
echo ========================================
echo Исправление remote и загрузка на GitHub
echo ========================================
echo.

cd /d "%~dp0"

echo [1/4] Удаление старого remote origin...
git remote remove origin 2>nul

echo [2/4] Добавление правильного remote...
git remote add origin https://github.com/Andhanc/botfinale.git
if %errorlevel% neq 0 (
    echo Ошибка при добавлении remote
    pause
    exit /b 1
)

echo [3/4] Проверка remote...
git remote -v

echo [4/4] Переименование ветки в main (если нужно)...
git branch -M main 2>nul

echo.
echo ========================================
echo Загрузка на GitHub...
echo ========================================
echo.

git push -u origin main

if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo Ошибка при загрузке
    echo ========================================
    echo.
    echo Возможные причины:
    echo 1. Нужна аутентификация GitHub
    echo 2. Репозиторий не существует
    echo.
    echo Попробуйте выполнить вручную:
    echo   git push -u origin main
    echo.
) else (
    echo.
    echo ========================================
    echo УСПЕШНО! Проект загружен!
    echo ========================================
    echo.
    echo Репозиторий: https://github.com/Andhanc/botfinale.git
    echo.
)

pause

