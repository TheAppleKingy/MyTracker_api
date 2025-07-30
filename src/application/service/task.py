from typing import Sequence

from domain.entities.tasks import Task
from domain.repositories.task_repository import AbstractTaskRepository
from domain.repositories.user_repository import AbstractUserRepository
from domain.repositories.exceptions import TaskRepositoryError

from application.dto.task_dto import TaskCreateForUser, TaskUpdateForUser

from .exceptions import TaskServiceError


class TaskService:
    def __init__(self, task_repository: AbstractTaskRepository, user_repository: AbstractUserRepository):
        self.repo = task_repository
        self.user_repo = user_repository

    def check_belongs_to_user(self, user_id: int, task: Task):
        if task.user_id != user_id:
            raise TaskServiceError(f'Task {task.id} does not belong to user ')

    async def check_is_root_for_user(self, user_id: int, task_id: int):
        task = await self.repo.get_task(task_id)
        print(task, 'task for checkin')
        self.check_belongs_to_user(user_id, task)
        if not task.is_root():
            raise TaskServiceError(
                f'Task {task.id} is not root task for user {user_id}')
        print('is root')

    async def get_full_trees(self, return_lists: bool = False):
        roots = await self.repo.get_root_tasks()
        ids = [root.id for root in roots]
        return await self.get_tasks_trees(ids, return_lists=return_lists)

    async def get_task_tree(self, from_task_id: Task, return_list: bool = False):
        """Returns root of task tree or all tasks of tree starting from task has id = from_task_id"""
        try:
            return await self.repo.get_nested_tasks(from_task_id, return_list=return_list)
        except TaskRepositoryError as e:
            raise TaskServiceError(str(e))

    async def get_tasks_trees(self, from_task_ids: Sequence[int], return_lists: bool = False):
        return [await self.get_task_tree(task, return_list=return_lists) for task in from_task_ids]

    async def get_user_task_tree(self, user_id: int, root_task_id: int, return_list: bool = False):
        await self.check_is_root_for_user(user_id, root_task_id)
        return await self.get_task_tree(root_task_id, return_list=return_list)

    async def get_user_tasks_trees(self, user_id: int, return_lists: bool = False):
        roots = await self.repo.get_root_tasks_for_user(user_id)
        root_ids = [task.id for task in roots]
        return await self.get_tasks_trees(root_ids, return_lists=return_lists)

    async def finish_task(self, task_id: int):
        tree = await self.get_task_tree(task_id, return_list=True)
        task = tree[0]
        not_finished_subtasks = []
        subtasks = tree[1:]
        if task.is_done():
            raise TaskServiceError("Task is already done")
        for subtask in subtasks:
            if not subtask.is_done():
                not_finished_subtasks.append(str(subtask.id))
        if not_finished_subtasks:
            raise TaskServiceError(
                f'Cannot finish task {task.id} while not finished subtasks with next ids: {', '.join(not_finished_subtasks)}')
        task.finish()
        await self.repo.update_task(task.id, pass_date=task.pass_date)
        return task

    async def add_task_to_user(self, user_id: int, task_schema: TaskCreateForUser):
        created = await self.repo.create_task(**task_schema.model_dump(exclude_none=True), user_id=user_id)
        return await self.get_task_tree(created.id)

    async def update_task_for_user(self, user_id: int, task_id: int, task_update_schema: TaskUpdateForUser):
        task = await self.get_task_tree(task_id)
        self.check_belongs_to_user(user_id, task)
        await self.repo.update_task(task_id, **task_update_schema.model_dump(exclude_none=True))
        return task

    async def finish_task_for_user(self, user_id: int, task_id: int):
        task = await self.repo.get_task(task_id)
        if task.user_id != user_id:
            raise TaskServiceError(
                f'Task {task.id} does not belong to user with id {user_id}')
        return await self.finish_task(task_id)
