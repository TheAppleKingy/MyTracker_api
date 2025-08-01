# MyTracker

**MyTracker** is a personal task tracker controlled via a Telegram bot.  
This repository contains the backend part of the application.

- [Install](#install)
- [Quickstart](#quickstart)
- [Usage](#usage)
- [Stack](#stack)

---

## ⚙️ Install

Before running the app, set the following environment variables:

### Core & Celery

| Variable               | Description                                 |
|------------------------|---------------------------------------------|
| `CELERY_WORKERS`       | Number of CPU cores Celery can use          |
| `TASK_SERVICE_QUEUE`   | Name of the Celery task queue               |
| `CELERY_BROKER_URL`    | URL of the message broker (usually Redis)   |

### Redis

| Variable         | Description                      |
|------------------|----------------------------------|
| `REDIS_URL`      | Redis connection URL             |
| `REDIS_PASSWORD` | Redis connection password        |

### JWT Auth

| Variable             | Description                                                  |
|----------------------|--------------------------------------------------------------|
| `SECRET_KEY`         | Secret key to sign JWT tokens                                |
| `TOKEN_EXPIRE_TIME`  | Token expiration time (in seconds)                           |
| `URL_EXPIRE_TIME`    | Lifetime of confirmation URLs (in seconds)                   |
| `TOKEN_SALT`         | Salt to strengthen token signatures                          |

### PostgreSQL

| Variable                   | Description                                                           |
|----------------------------|-----------------------------------------------------------------------|
| `DATABASE_URL`             | Should start with `postgresql+asyncpg://...`                          |
| `FORMATTED_DATABASE_URL`   | Same as above but starts with `postgresql://...`, used in testing     |
| `POSTGRES_DB`              | Name of the main database                                             |
| `POSTGRES_USER`            | PostgreSQL username                                                   |
| `POSTGRES_PASSWORD`        | PostgreSQL password                                                   |

### Testing

| Variable                       | Description                                            |
|--------------------------------|--------------------------------------------------------|
| `TEST_DB_NAME`                 | Test database name                                     |
| `TEST_DATABASE_URL`            | Like `DATABASE_URL` but for testing                   |
| `FORMATTED_TEST_DATABASE_URL`  | Same as above without `+asyncpg`                      |

### Email (SMTP)

| Variable              | Description                          |
|-----------------------|--------------------------------------|
| `EMAIL_HOST_USER`     | Sender email address                 |
| `EMAIL_HOST_PASSWORD` | SMTP password for the sender account |

---

To start the backend app:

```bash
docker compose up --build
```

>This backend is used by the [MyTracker_bot](https://github.com/TheAppleKingy/MyTracker_bot).  
>The bot will not work correctly unless this backend is running.

---

## 🚀 Quickstart

Once containers are up, the API will be ready to accept requests.  
Swagger documentation is available at:

🔗 [http://localhost:8000/docs](http://localhost:8000/docs)

> ✅ Be sure to set the backend URL in the bot's environment as `BASE_API_URL`.

---

## 📦 Usage

The API provides basic authentication features:

- Registration (via email confirmation)
- Login / Logout
- Change password

>Every new registration requires email confirmation.  
>Refer to Swagger UI for request details.

---

### 🧩 Task management

The Telegram bot communicates with this API using a JWT token (sent via cookies).  
The backend authenticates the user and returns JSON responses.

**Available endpoints:**

| Method | Endpoint                        | Description                                           |
|--------|----------------------------------|-------------------------------------------------------|
| GET    | `/api/bot/my_tasks`             | Returns full task tree for the user                  |
| GET    | `/api/bot/my_tasks/{id}`        | Returns task tree starting from a specific task      |
| POST   | `/api/bot/create_task`          | Creates a new task and returns its data              |
| PATCH  | `/api/bot/update_task/{id}`     | Updates one or more fields of the specified task     |
| PATCH  | `/api/bot/finish_task/{id}`     | Marks the task as completed                          |
| DELETE | `/api/bot/delete_task/{id}`     | Deletes the specified task                           |

> 🧠 User-task ownership is validated on the bot side.

---

## 🧰 Stack

- **FastAPI** – web framework  
- **PostgreSQL** – database  
- **Redis** – task broker  
- **Celery** – background task queue  
- **SQLAlchemy** – ORM  
- **Alembic** – DB migrations  
- **Uvicorn** – ASGI server  
- **asyncpg** – async PostgreSQL driver  
- **Docker** – containerization
---

Feel free to contribute or open issues.
