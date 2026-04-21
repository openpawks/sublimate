from fastapi import Depends

from services.project_service import ProjectService
from services.daemon_service import DaemonService
from services.task_service import TaskService


def get_task_service():
    return TaskService()


def get_daemon_service():
    return DaemonService()


def get_project_service(daemon_service: DaemonService = Depends(get_daemon_service)):
    return ProjectService(daemon_service)
