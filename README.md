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
### JWT Auth

| Variable             | Description                                                  |
|----------------------|--------------------------------------------------------------|
| `SECRET_KEY`         | Secret key to sign JWT tokens                                |
| `TOKEN_EXPIRE_TIME`  | Token expiration time (in seconds)                           |


### PostgreSQL

| Variable                   | Description                                                           |
|----------------------------|-----------------------------------------------------------------------|
| `POSTGRES_DB`              | Name of the main database                                             |
| `POSTGRES_USER`            | PostgreSQL username                                                   |
| `POSTGRES_PASSWORD`        | PostgreSQL password                                                   |
| `POSTGRES_HOST`            | Hostname of container with database. If was not specified manually just service name from compose.yaml

---

To build and start the backend app:

```bash
make tracker.prod.build.up
```

>This backend is used by the [MyTracker_bot](https://github.com/TheAppleKingy/MyTracker_bot).  
>The bot will not work correctly unless this backend is running.

---

## 🚀 Quickstart

Once containers are up, the API will be ready to accept requests.  
Swagger documentation is available at:

🔗 [http://localhost:8000/docs](http://localhost:8000/docs)

> ✅ Be sure to set the backend container name to `BASE_API_URL`.

---

## 📦 Usage

The API provides basic authentication features:

- Registration
>This endpoint just save user by provided telegram name. Does not require password. Each request protected by jwt. Client should has the same secret as this backend to be accessed. It is assumed that client provides to API one-time(has very short lifetime) jwt token as cookie named "token". For dev you can create token with long lifetime or even without expiration time.    

**Refer to Swagger UI for request details.**

---

### 🧩 Task management

The Telegram bot communicates with this API using a JWT token (sent via cookies).  
The backend authenticates the user and returns JSON responses.

**Available endpoints:**

| Method | Endpoint                        | Description                                           |
|--------|----------------------------------|-------------------------------------------------------|
| GET    | `/api/v1/tasks`             | Returns active tasks data(not finished yet)                  |
| GET    | `/api/v1/tasks/finished`        | Returns finished tasks data      |
| GET    | `/api/v1/tasks/{task_id}`        | Returns task data      |
| POST   | `/api/v1/tasks`          | Creates a new task and returns its data              |
| PATCH  | `/api/v1/tasks/{task_id}`     | Updates one or more fields of the specified task     |
| PATCH  | `/api/v1/tasks/{task_id}/finish`     | Marks the task as completed                          |
| PATCH  | `/api/v1/tasks/{task_id}/finish/force`     | Marks the task and all subtasks as completed                          |
| DELETE | `/api/v1/tasks/{task_id}`     | Deletes the specified task with all subtasks                           |

**Refer to Swagger UI for request details.**

---

## 🧰 Stack

- **FastAPI** – web framework  
- **PostgreSQL** – database  
- **SQLAlchemy** – ORM  
- **Alembic** – DB migrations  
- **Uvicorn** – ASGI server  
- **asyncpg** – async PostgreSQL driver  
- **Docker** – containerization
---

Feel free to contribute or open issues.
