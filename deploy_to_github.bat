@echo off
chcp 65001 >nul
echo ========================================
echo Загрузка проекта на GitHub
echo ========================================
echo.

cd /d "%~dp0"

echo [1/7] Проверка Git...
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo ОШИБКА: Git не установлен или не найден в PATH
    pause
    exit /b 1
)

echo [2/7] Инициализация Git репозитория...
if exist .git (
    echo Git репозиторий уже инициализирован
) else (
    git init
    if %errorlevel% neq 0 (
        echo Ошибка при инициализации Git
        pause
        exit /b 1
    )
)

echo [3/7] Настройка Git пользователя...
git config user.name "Andhanc" 2>nul
git config user.email "andhanc@users.noreply.github.com" 2>nul

echo [4/7] Создание .env файла (если не существует)...
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

echo [5/7] Добавление всех файлов в Git...
git add .
if %errorlevel% neq 0 (
    echo Ошибка при добавлении файлов
    pause
    exit /b 1
)

echo [6/7] Создание коммита...
git commit -m "Initial commit: Bot calculator project with .env and database"
if %errorlevel% neq 0 (
    echo Предупреждение: Возможно, нет изменений для коммита или коммит уже существует
)

echo [7/7] Настройка remote репозитория...
git remote remove origin 2>nul
git remote add origin https://github.com/Andhanc/botfinale.git
if %errorlevel% neq 0 (
    echo Ошибка при настройке remote
    pause
    exit /b 1
)

echo.
echo Переименование ветки в main...
git branch -M main 2>nul

echo.
echo ========================================
echo Готово! Теперь загружаем на GitHub...
echo ========================================
echo.

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
    echo 3. Нужно ввести логин и пароль/токен
    echo.
    echo Для настройки аутентификации:
    echo - Используйте Personal Access Token вместо пароля
    echo - Или настройте SSH ключ
    echo.
    echo Попробуйте выполнить команду вручную:
    echo   git push -u origin main
    echo.
) else (
    echo.
    echo ========================================
    echo УСПЕШНО! Проект загружен на GitHub!
    echo ========================================
    echo.
    echo Репозиторий: https://github.com/Andhanc/botfinale.git
    echo.
)

pause

