[![Build Status](https://github.com/PivnoyFei/task_for_mango_fzco/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/PivnoyFei/task_for_mango_fzco/actions/workflows/main.yml)

<h1 align="center"><a target="_blank" href="">task_for_mango_fzco</a></h1>

### Стек
![Python](https://img.shields.io/badge/Python-171515?style=flat-square&logo=Python)![3.11](https://img.shields.io/badge/3.11-blue?style=flat-square&logo=3.11)
![FastAPI](https://img.shields.io/badge/FastAPI-171515?style=flat-square&logo=FastAPI)![0.89.1](https://img.shields.io/badge/0.89.1-blue?style=flat-square&logo=0.89.1)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-171515?style=flat-square&logo=PostgreSQL)![13.0](https://img.shields.io/badge/13.0-blue?style=flat-square&logo=13.0)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-171515?style=flat-square&logo=SQLAlchemy)
![Docker-compose](https://img.shields.io/badge/Docker--compose-171515?style=flat-square&logo=Docker)
![Redis](https://img.shields.io/badge/Redis-171515?style=flat-square&logo=Redis)
![Nginx](https://img.shields.io/badge/Nginx-171515?style=flat-square&logo=Nginx)
![Pytest](https://img.shields.io/badge/Pytest-171515?style=flat-square&logo=Pytest)

#### У текущего тестового задания есть только общее описание требований, конкретные детали реализации остаются на усмотрение разработчика. Стек, который Вам необходимо использовать: FastAPI, PostgeSQL, Socketio, JWToken
---
#### 1. Задача

> Разработать backend для чата с пользователями. Вначале пользователь должен пройти авторизацию или зарегистрироваться по номеру телефона с помощью JWToken.
При входе, у пользователя должен быть следующий функционал:
Реализовать простое редактирование профиля с изменением информации о нём и аватарки. Аватарку принимать в base64, сохранять её в 3-ёх размерах: 50х50, 100х100, 400х400, и оригинал.
Реализовать функционал чатов с использованием Socketio. Можно посмотреть список чатов для текущего пользователя, завести новый чат или создать группу с несколькими другими пользователями. Также реализовать общение в чате.
Дополнительно должны быть реализованы закреплённые чаты, типы сообщений и лайки для каждого из сообщений.
Сущности необходимо придумать и реализовать самим, на основе текущего задания. Для примера можете ориентироваться на популярные мессенджеры.
Также необходимо реализовать:
> - организовать тестирование написанного кода;
> - обеспечить автоматическую сборку/тестирование с помощью GitHub CI;
> - подготовить docker-compose для запуска всех сервисов проекта одной командой;
> - написать конфигурационные файлы (deployment, ingress, …) для запуска проекта в kubernetes и описать как их применить к работающему кластеру;
> - сделать так, чтобы по адресу /docs/ открывалась страница со Swagger UI и в нём отображалось описание разработанного API. Пример: https://petstore.swagger.io;
> - обеспечить подробное логирование на всех этапах обработки запросов, чтобы при эксплуатации была возможность найти в логах всю информацию.

#### 2. Результат выполнения задания
> Результатом задания должен быть работоспособный swagger site со всем вышеупомянутым функционалом. Проект предоставляется в виде ссылки на git-проект.


### Маршруты

| Название | Метод | Описание | Авторизация |
|----------|-------|----------|-------------|
| /api/users/signup           | POST | Регистрация нового пользователя           | Нет
| /api/users/me               | GET  | Возвращает самого себя                    | Да
| /api/users/&lt;username&gt; | GET  | Посмотреть профиль пользователя           | Нет
| /api/users/&lt;username&gt; | PUT  | Редактировать профиль                     | Да
| /api/auth/login             | POST | Авторизация, получение jwt-токена         | Нет
| /api/auth/refresh           | POST | Обновить токен                            | Да
| /api/auth/logout            | POST | Выйти, удаляет все refresh-токены из бд   | Да
||
| /api/chat/room                          | POST   | Создать комнату для чата    | Да
| /api/chat/room/&lt;room_name&gt;        | GET    | Посмотреть комнату          | Да
| /api/chat/room/&lt;room_name&gt;/member | GET    | Посмотреть список участников комнаты, доступно только для участника | Да
| /api/chat/room/&lt;room_name&gt;        | POST   | Добавить пользователя в чат | Да
| /api/chat/rooms                         | GET    | Посмотреть все комнаты      | Да
| /api/chat/room/&lt;room_name&gt;        | DELETE | Удалить комнату             | Да
| /api/chat/ws/&lt;room_name&gt;          | ws     | Вебсокет чат                | Да


### Запуск проекта
Клонируем репозиторий и переходим в него:
```bash
gh clone https://github.com/PivnoyFei/task_for_mango_fzco
cd task_for_mango_fzco
```

### Для быстрого запуска (поднимаем только контейнер бд) создадим виртуальное окружение и установим зависимости:
#### Создаем и активируем виртуальное окружение:
```bash
python3 -m venv venv
source venv/bin/activate
```
#### для Windows
```bash
python -m venv venv
source venv/Scripts/activate
```
#### Обновиляем pip и ставим зависимости из requirements.txt:
```bash
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

#### Переходим в папку с файлом docker-compose.yaml:
```bash
cd infra
```

### Перед запуском сервера, в папке infra необходимо создать .env файл со своими данными.
```bash
POSTGRES_DB="postgres" # имя БД
POSTGRES_USER="postgres" # логин для подключения к БД
POSTGRES_PASSWORD="postgres" # пароль для подключения к БД
POSTGRES_SERVER="db" # название контейнера
POSTGRES_PORT="5432" # порт для подключения к БД

REDIS_PORT="6379"
REDIS_HOST="redis"

ALGORITHM="HS256"
JWT_SECRET_KEY="key"
JWT_REFRESH_SECRET_KEY="key"
```

#### Чтобы сгенерировать безопасный случайный секретный ключ, используйте команду:
```bash
openssl rand -hex 32
```

### Быстрый запуск, из контейнеров запускаем только бд и redis:
```bash
docker-compose up -d db
docker-compose up -d redis
```

#### Открываем в консоли папку backend и запускаем сервер:
```bash
uvicorn main:app --reload --host 0.0.0.0
```

### Запуск проекта с полной сборкой
```bash
docker-compose up -d --build
```

#### Миграции базы данных (не обязательно):
```bash
docker-compose exec backend alembic revision --message="Initial" --autogenerate
docker-compose exec backend alembic upgrade head
```

### Документация будет доступна по адресу:
```bash
http://127.0.0.1:8000/docs/
http://127.0.0.1:8000/redoc/
```
#### Останавливаем контейнеры:
```bash
docker-compose down -v
```

#### Автор
[Смелов Илья](https://github.com/PivnoyFei)