# SuperDuperBot

## Структура проекта и назначение папок/файлов

- **.env.example**  
  [Ссылка](https://github.com/Elenthrill/SuperDuperBot/blob/main/.env.example)  
  Пример переменных окружения, необходимых для за��уска проекта (используется для настройки секретов и параметров интеграций).

- **.gitignore**  
  [Ссылка](https://github.com/Elenthrill/SuperDuperBot/blob/main/.gitignore)  
  Определяет файлы и папки, которые не должны попадать в систему контроля версий Git.

- **README.md**  
  [Ссылка](https://github.com/Elenthrill/SuperDuperBot/blob/main/README.md)  
  Описание, инструкция по запуску и работе с проектом.

- **app/**  
  [Ссылка](https://github.com/Elenthrill/SuperDuperBot/tree/main/app)  
  Основная папка с исходным кодом приложения (логика и структура бота).

- **config/**  
  [Ссылка](https://github.com/Elenthrill/SuperDuperBot/tree/main/config)  
  Конфигурационные файлы: настройки окружения, параметры запуска, параметры интеграций.

- **docker-compose.yml**  
  [Ссылка](https://github.com/Elenthrill/SuperDuperBot/blob/main/docker-compose.yml)  
  Описывает запуск и сборку контейнеров Docker для проекта (автоматизация развертывания).

- **locales/**  
  [Ссылка](https://github.com/Elenthrill/SuperDuperBot/tree/main/locales)  
  Папка локализаций: файлы для поддержки разных языков и переводов.

- **main.py**  
  [Ссылка](https://github.com/Elenthrill/SuperDuperBot/blob/main/main.py)  
  Основной скрипт для старта приложения. Обычно содержит точку входа.

- **migrations/**  
  [Ссылка](https://github.com/Elenthrill/SuperDuperBot/tree/main/migrations)  
  Файлы для управления изменениями структуры базы данных (миграции).

- **requirements.txt**  
  [Ссылка](https://github.com/Elenthrill/SuperDuperBot/blob/main/requirements.txt)  
  Список зависимостей Python, которые необходимы для запуска проекта.

## Описание папок и файлов внутри `app/bot`

- **__init__.py**  
  [Ссылка](https://github.com/Elenthrill/SuperDuperBot/blob/main/app/bot/__init__.py)  
  Позволяет использовать папку как модуль Python, инициализирует пакет bot.

- **bot.py**  
  [Ссылка](https://github.com/Elenthrill/SuperDuperBot/blob/main/app/bot/bot.py)  
  Основной файл логики бота: здесь описана архитектура, запуск и взаимодействие с платформой (Telegram/Discord или другой).

- **enums/**  
  [Ссылка](https://github.com/Elenthrill/SuperDuperBot/tree/main/app/bot/enums)  
  Содержит классы перечислений (Enum) — для типизированных констант, статусов, событий и т.д.

- **filters/**  
  [Ссылка](https://github.com/Elenthrill/SuperDuperBot/tree/main/app/bot/filters)  
  Фильтры сообщений и событий: реализуют дополнительную логику для обработки пользовательских запросов.

- **handlers/**  
  [Ссылка](https://github.com/Elenthrill/SuperDuperBot/tree/main/app/bot/handlers)  
  Описывает обработчики сообщений, команд, событий (реакции на действия пользователей).

- **i18n/**  
  [Ссылка](https://github.com/Elenthrill/SuperDuperBot/tree/main/app/bot/i18n)  
  Реализует международализацию (i18n) — поддержка разных языков, перевод сообщений.

- **keyboards/**  
  [Ссылка](https://github.com/Elenthrill/SuperDuperBot/tree/main/app/bot/keyboards)  
  Здесь формируются пользовательские интерфейсы клавиатур (inline, reply), используемых ботом.

- **midlewares/**  
  [Ссылка](https://github.com/Elenthrill/SuperDuperBot/tree/main/app/bot/midlewares)  
  Промежуточные обработчики (middlewares) для дополнительных операций между получением и обработкой сообщения.

- **states/**  
  [Ссылка](https://github.com/Elenthrill/SuperDuperBot/tree/main/app/bot/states)  
  Содержит описание состояний, используемых ботом (например, для FSM — конечных автоматов состояний при взаимодействии с пользователем).


---

## Как начать работу

Clone the repository:

bash
git clone https://github.com/kmsint/aiogram3_stepik_course.git
Move to the db_echo_bot folder:

bash
cd aiogram3_stepik_course/db_echo_bot
Create .env file and copy the code from .env.example file into it.

Fill in the file .env with real data (BOT_TOKEN, POSTGRES_USER, POSTGRES_PASSWORD, etc.)

Launch containers with Postgres, Redis, and pgAdmin with the command (You need docker and docker-compose installed on your local machine):

bash
docker compose up -d
Create a virtual environment in the project root and activate it.

Install the required libraries in the virtual environment with pip:

bash
pip install -r requirements.txt
Apply database migrations using the command:

bash
python3 -m migrations.create_tables
Run main.py to launch the bot:

bash
python3 main.py

---

## Контакты и поддержка

По вопросам работы с проектом обращайтесь через [issues](https://github.com/Elenthrill/SuperDuperBot/issues).