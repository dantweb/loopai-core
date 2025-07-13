import uuid
from typing import Optional, Any

from core.models.broadcast_data import BroadcastData


class SessionManager:
    def __init__(self):
        self._loop_index = None
        self._global_step_name = None
        self._global_loop_index = None
        self._step_name = None
        self._user_id: Optional[int] = None
        self._loop_id: Optional[int] = None
        self._environment: Optional[dict] = None
        self._session_id: str = str(uuid.uuid4())
        self._project_id: Optional[int] = None
        self._bc_collection = []


    def get_session_id(self):
        return self._session_id

    def regenerate_session_id(self):
        self._session_id = str(uuid.uuid4())
        self._step_name = None
        self._user_id: Optional[int] = None
        self._loop_id: Optional[int] = None
        self._loop_index = None
        self._environment: Optional[dict] = None
        self._global_step_name = None
        self._global_loop_index = None
        self._project_id: Optional[int] = None

    def set_environment(self, environment):
        self._environment = environment

    def get_env(self, value_name: str):
        if not self._environment:
            return None
        if value_name not in self._environment:
            return None

        return self._environment[value_name]

    def set_loop_id(self, loop_id: int):
        self._loop_id = loop_id

    def set_user_id(self, user_id: int):
        self._user_id = user_id

    def get_user_id(self) -> int:
        return self._user_id

    def set_project_id(self, project_id: int):
        self._project_id = project_id

    def get_project_id(self) -> int:
        return self._project_id

    def get_loop_id(self) -> int:
        return self._loop_id

    def get_loop_index(self) -> int:
        return self._loop_index

    def set_loop_index(self, index):
        self._loop_index = index

    def get_environment(self) -> dict:
        return self._environment

    def set_step_name(self, step_name: str):
        self._step_name = step_name

    def set_global_loop_index(self, loop_index: int):
        self._global_loop_index = loop_index

    def set_global_step_name(self, step_name: str):
        self._global_step_name = step_name

    def get_global_step_name(self):
        return self._global_step_name

    def collect_broadcast(self, bc: BroadcastData):
        self._bc_collection.append(bc)

    def get_broadcast_collection(self) -> list:
        return self._bc_collection

    def get_bc_collection_json(self) -> list[Any]:
        bc_list = []
        for bc in self._bc_collection:
            bc_list.append(bc.to_dict())

        return bc_list


# Singleton instance for global usage
session_manager = SessionManager()

