# Инструкция по загрузке проекта на GitHub

## Автоматическая настройка (рекомендуется)

### Windows

1. Запустите `setup_git.bat` - это автоматически:
   - Инициализирует Git репозиторий
   - Создаст .env файл (если его нет)
   - Добавит все файлы в Git
   - Создаст первый коммит
   - Настроит remote репозиторий

2. Затем запустите `push_to_github.bat` для загрузки на GitHub

### Ручная настройка

Если автоматические скрипты не работают, выполните команды вручную:

```bash
# 1. Инициализация Git
git init

# 2. Создание .env файла (если его нет)
# Скопируйте содержимое из примера выше и заполните своими данными

# 3. Добавление всех файлов
git add .

# 4. Создание первого коммита
git commit -m "Initial commit: Bot calculator project with .env and database"

# 5. Настройка remote репозитория
git remote add origin https://github.com/Andhanc/botfinale.git

# 6. Переименование ветки в main
git branch -M main

# 7. Загрузка на GitHub
git push -u origin main
```

## Настройка аутентификации GitHub

Если при загрузке возникает ошибка аутентификации:

### Вариант 1: Personal Access Token

1. Создайте токен на GitHub: Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Используйте токен вместо пароля при push

### Вариант 2: SSH ключ

1. Сгенерируйте SSH ключ:
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

2. Добавьте публичный ключ на GitHub: Settings → SSH and GPG keys

3. Измените remote URL:
```bash
git remote set-url origin git@github.com:Andhanc/botfinale.git
```

## Важно

- Файл `.env` и база данных `*.db` включены в репозиторий согласно вашим требованиям
- Убедитесь, что в `.env` нет реальных секретных данных перед коммитом (или используйте тестовые значения)
- После первого push все файлы будут доступны на GitHub

