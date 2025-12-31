# Инструкция: Коммит и отправка на GitHub

## Быстрый способ

Запустите файл **`commit_and_push.bat`** двойным кликом.

## Ручной способ (в PowerShell или CMD)

Выполните следующие команды в терминале в папке проекта:

```bash
# 1. Перейти в папку проекта
cd "C:\Проекты\bot-calcu\bot-calculator1"

# 2. Добавить все файлы (включая .env)
git add -A

# 3. Проверить, что .env добавлен
git status

# 4. Создать коммит
git commit -m "Update: Improved error handling, added troubleshooting guide, fixed AI company name to ASIC Store, added input validation for sell equipment form"

# 5. Отправить на GitHub
git push origin main
```

## Проверка что .env включен

После `git add -A` выполните:
```bash
git ls-files | findstr .env
```

Если видите `.env` в списке - файл добавлен.

## Если .env не добавляется

Если `.env` не добавляется, проверьте `.gitignore`:
- Убедитесь, что в `.gitignore` НЕТ строки `.env`
- Если есть, удалите или закомментируйте её

## Важно

- Убедитесь, что в `.env` нет реальных секретных данных (или используйте тестовые значения)
- Все файлы проекта, включая `.env` и базу данных, будут загружены на GitHub

