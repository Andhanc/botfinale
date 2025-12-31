# Bot Calculator - Telegram бот для расчета доходности майнинга

Telegram бот для расчета доходности майнинга криптовалют на ASIC-оборудовании.

## Возможности

- 💰 Расчет доходности майнинга
- 📊 Сравнение различных ASIC-моделей
- 💎 Отслеживание актуальных цен криптовалют
- 🤖 AI-консультант по майнингу
- 📦 Заявки на продажу оборудования
- 📈 Характеристики оборудования

## Установка

### Требования

- Python 3.12+
- PostgreSQL (опционально, для продакшн) или SQLite (для разработки)

### Настройка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/Andhanc/botfinale.git
cd botfinale
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# или
source venv/bin/activate  # Linux/Mac
```

3. Установите зависимости:
```bash
pip install -r req.txt
```

4. Настройте переменные окружения в файле `.env`:
```env
# Bot Token
BOT_TOKEN=your_bot_token_here

# Admin IDs (через запятую)
ADMIN_ID=586797053
ADMIN_IDS=586797053

# AI API Key
AI_API_KEY=your_ai_api_key_here

# Database Configuration
# Для SQLite (локальная разработка)
DATABASE_URL=

# Для PostgreSQL (продакшн)
# POSTGRES_USER=your_postgres_user
# POSTGRES_PASSWORD=your_postgres_password
# POSTGRES_HOST=localhost
# POSTGRES_NAME=mainercrypto
```

5. Инициализируйте базу данных:
```bash
python main.py
```

## Запуск

### Windows
```bash
setup_local.bat
```

### Linux/Mac
```bash
python main.py
```

## Структура проекта

```
bot-calculator1/
├── handlers/          # Обработчики команд и сообщений
├── keyboards/          # Клавиатуры для бота
├── database/           # Модели и запросы к БД
├── utils/              # Утилиты (калькулятор, AI, логирование)
├── alembic/            # Миграции базы данных
├── image/              # Изображения для бота
├── main.py             # Точка входа
├── config.py           # Конфигурация
├── signature.py        # Настройки бота
└── .env                # Переменные окружения
```

## База данных

Проект использует SQLite для локальной разработки и PostgreSQL для продакшн.

Миграции выполняются автоматически при первом запуске.

## Разработка

### Добавление новых моделей ASIC

Используйте скрипт `fill_asic_models.py` или админ-панель бота.

### Обновление цен монет

Цены обновляются автоматически каждые 3 минуты из Binance P2P API.

## Контакты

- 💬 Менеджер: @snooby37
- 📢 Канал: @asic_mining_store

## Лицензия

Проект разработан для ASIC Store.

