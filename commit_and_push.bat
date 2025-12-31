@echo off
chcp 65001 >nul
echo ========================================
echo Коммит и загрузка изменений на GitHub
echo ========================================
echo.

cd /d "%~dp0"

echo [1/5] Проверка статуса Git...
git status --short
echo.

echo [2/5] Добавление всех файлов (включая .env)...
git add .
if %errorlevel% neq 0 (
    echo Ошибка при добавлении файлов
    pause
    exit /b 1
)

echo [3/5] Проверка что .env добавлен...
git ls-files | findstr /i ".env" >nul
if %errorlevel% equ 0 (
    echo .env файл добавлен в репозиторий
) else (
    echo ВНИМАНИЕ: .env файл не найден в индексе
)

echo [4/5] Создание коммита...
git commit -m "Update: Improved error handling, added troubleshooting guide, fixed AI company name to ASIC Store"
if %errorlevel% neq 0 (
    echo Предупреждение: Возможно, нет изменений для коммита
    git status
    pause
    exit /b 1
)

echo [5/5] Отправка на GitHub...
git push origin main

if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo Ошибка при отправке на GitHub
    echo ========================================
    echo.
    echo Попробуйте выполнить вручную:
    echo   git push origin main
    echo.
    pause
    exit /b 1
) else (
    echo.
    echo ========================================
    echo УСПЕШНО! Изменения загружены на GitHub!
    echo ========================================
    echo.
    echo Репозиторий: https://github.com/Andhanc/botfinale.git
    echo.
)

pause

