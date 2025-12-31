@echo off
chcp 65001 >nul
echo ========================================
echo Настройка Git репозитория
echo ========================================
echo.

cd /d "%~dp0"

echo [1/6] Инициализация Git репозитория...
git init
if %errorlevel% neq 0 (
    echo Ошибка при инициализации Git
    pause
    exit /b 1
)

echo [2/6] Создание .env файла (если не существует)...
if not exist .env (
    (
        echo # Bot Token
        echo BOT_TOKEN=your_bot_token_here
        echo.
        echo # Admin IDs (через запятую)
        echo ADMIN_ID=586797053
        echo ADMIN_IDS=586797053
        echo.
        echo # AI API Key
        echo AI_API_KEY=your_ai_api_key_here
        echo.
        echo # Database Configuration
        echo # Для SQLite (локальная разработка) - оставьте пустым или не указывайте
        echo DATABASE_URL=
        echo.
        echo # Для PostgreSQL (продакшн) - раскомментируйте и заполните
        echo # POSTGRES_USER=your_postgres_user
        echo # POSTGRES_PASSWORD=your_postgres_password
        echo # POSTGRES_HOST=localhost
        echo # POSTGRES_NAME=mainercrypto
    ) > .env
    echo .env файл создан
) else (
    echo .env файл уже существует
)

echo [3/6] Добавление всех файлов в Git...
git add .
if %errorlevel% neq 0 (
    echo Ошибка при добавлении файлов
    pause
    exit /b 1
)

echo [4/6] Создание коммита...
git commit -m "Initial commit: Bot calculator project with .env and database"
if %errorlevel% neq 0 (
    echo Ошибка при создании коммита
    pause
    exit /b 1
)

echo [5/6] Настройка remote репозитория...
git remote remove origin 2>nul
git remote add origin https://github.com/Andhanc/botfinale.git
if %errorlevel% neq 0 (
    echo Ошибка при настройке remote
    pause
    exit /b 1
)

echo [6/6] Переименование ветки в main...
git branch -M main
if %errorlevel% neq 0 (
    echo Ошибка при переименовании ветки
    pause
    exit /b 1
)

echo.
echo ========================================
echo Готово! Репозиторий настроен.
echo ========================================
echo.
echo Теперь выполните команду для загрузки на GitHub:
echo   git push -u origin main
echo.
echo Или используйте скрипт push_to_github.bat
echo.
pause

