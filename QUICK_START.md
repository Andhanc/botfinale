# Быстрый старт - Загрузка на GitHub

## Автоматическая загрузка (Windows)

Просто запустите файл **`deploy_to_github.bat`** двойным кликом.

Этот скрипт автоматически:
1. ✅ Инициализирует Git репозиторий
2. ✅ Создаст .env файл (если его нет)
3. ✅ Добавит все файлы в Git (включая .env и БД)
4. ✅ Создаст коммит
5. ✅ Настроит remote репозиторий
6. ✅ Загрузит проект на GitHub

## Ручная загрузка (если скрипт не работает)

Откройте **Command Prompt (cmd)** в папке проекта и выполните:

```cmd
git init
git add .
git commit -m "Initial commit: Bot calculator project with .env and database"
git remote add origin https://github.com/Andhanc/botfinale.git
git branch -M main
git push -u origin main
```

## Важно

- Файл `.env` будет включен в репозиторий
- База данных `mainercrypto.db` будет включена
- При первом push может потребоваться аутентификация GitHub

## Аутентификация GitHub

Если запрашивается логин/пароль:
1. Используйте **Personal Access Token** вместо пароля
2. Создайте токен: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
3. При push введите токен вместо пароля

