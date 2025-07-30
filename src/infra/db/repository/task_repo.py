from sqlalchemy import text, select, insert, delete, update
from sqlalchemy.orm import selectinload

from domain.repositories.task_repository import AbstractTaskRepository
from domain.entities.tasks import Task
from domain.repositories.exceptions import TaskRepositoryError

from .auto_commit import commitable


class TaskRepository(AbstractTaskRepository):
    async def get_task(self, id: int) -> Task | None:
        return await self.session.scalar(select(Task).where(Task.id == id))

    async def get_root_tasks(self) -> list[Task]:
        db_resp = await self.session.scalars(select(Task).where(Task.task_id == None).options(selectinload(Task.user)))
        return db_resp.all()

    async def get_root_tasks_for_user(self, user_id: int):
        db_resp = await self.session.scalars(select(Task).where(Task.user_id == user_id, Task.task_id == None))
        return db_resp.all()

    @commitable
    async def create_task(self, **task_data) -> Task:
        return await self.session.scalar(insert(Task).values(**task_data).returning(Task))

    @commitable
    async def delete_task(self, id: int) -> Task:
        return await self.session.scalar(delete(Task).where(Task.id == id).returning(Task))

    @commitable
    async def update_task(self, id: int, **kwargs) -> Task:
        return await self.session.scalar(update(Task).where(Task.id == id).values(**kwargs).returning(Task))

    async def get_nested_tasks(self, from_task_id: int, return_list: bool = False) -> Task | list[Task]:
        query = text(f"""WITH RECURSIVE task_tree AS (
            SELECT * FROM tasks WHERE id = {from_task_id}
            UNION ALL
            SELECT t.* FROM tasks t
            INNER JOIN task_tree tt ON t.task_id = tt.id
        )
        SELECT * FROM task_tree;""")
        res = await self.session.execute(query)
        tasks_data = res.mappings().all()
        if not tasks_data:
            raise TaskRepositoryError(f'Task does not exist')
        ids = [task_data['id'] for task_data in tasks_data]
        tasks_objs = await self.session.scalars(select(Task).where(Task.id.in_(ids)).options(selectinload(Task.subtasks)))
        task_map = {task.id: task for task in tasks_objs}
        ordered = [task_map[id_] for id_ in ids]
        if return_list:
            return ordered
        return ordered[0]
