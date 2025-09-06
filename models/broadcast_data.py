import json
import re
from collections import UserDict, deque
from PIL import Image

class BroadcastData(UserDict):
    def __init__(self, obj_input=None):
        super().__init__()
        self.properties = []
        self.image = None

        if obj_input is None:
            self.data = None
            return

        normalized_data = self._normalize_and_flatten(obj_input)

        if isinstance(normalized_data, dict):
            self.data = normalized_data
            self.properties = [type(v).__name__ for v in self.data.values()]
        elif isinstance(normalized_data, list):
            self.data = normalized_data
            if normalized_data:
                if all(isinstance(item, dict) for item in normalized_data):
                    for item in normalized_data:
                        if isinstance(item, Image.Image):
                            self.image = item
                        else:
                            self.properties.extend([type(v).__name__ for v in item.values()])
                else:
                    self.properties = [type(v).__name__ for v in normalized_data]
        elif isinstance(normalized_data, Image.Image):
            self.image = normalized_data
            self.data = {}
        else:
            self.data = {}

    def _normalize_and_flatten(self, data, depth=0, max_depth=100):
        if depth > max_depth:
            return data

        stack = deque([(data, [])])
        result = {}
        visited = set()

        while stack:
            current, path = stack.pop()
            obj_id = id(current)

            if obj_id in visited:
                continue
            visited.add(obj_id)

            if isinstance(current, BroadcastData):
                stack.append((current.data, path))
            elif isinstance(current, dict):
                temp_dict = {}
                for key, value in current.items():
                    temp_dict[key] = None
                    stack.append((value, path + [key]))
                if path:
                    parent = result
                    for key in path[:-1]:
                        parent = parent[key]
                    parent[path[-1]] = temp_dict
                else:
                    result.update(temp_dict)
            elif isinstance(current, list):
                temp_list = [None] * len(current)
                for i, item in enumerate(current):
                    stack.append((item, path + [i]))
                if path:
                    parent = result
                    for key in path[:-1]:
                        parent = parent[key]
                    parent[path[-1]] = temp_list
                else:
                    result = temp_list
            elif isinstance(current, str) and self._looks_like_json(current):
                normalized = self._normalize_json_string(current)
                try:
                    parsed = json.loads(normalized)
                    stack.append((parsed, path))
                except json.JSONDecodeError:
                    if path:
                        parent = result
                        for key in path[:-1]:
                            parent = parent[key]
                        parent[path[-1]] = normalized
                    else:
                        result = normalized
            else:
                if path:
                    parent = result
                    for key in path[:-1]:
                        parent = parent[key]
                    parent[path[-1]] = current
                else:
                    result = current

        return result

    def _looks_like_json(self, text: str) -> bool:
        if not isinstance(text, str):
            return False
        text = text.strip()
        return (text.startswith('{') and text.endswith('}')) or \
               (text.startswith('[') and text.endswith(']'))

    def _normalize_json_string(self, json_string: str) -> str:
        if not isinstance(json_string, str):
            return json_string
        json_string = json_string.strip()
        try:
            json.loads(json_string)
            return json_string
        except json.JSONDecodeError:
            pass
        json_string = re.sub(r"(?<!\\)'", '"', json_string)
        json_string = json_string.replace("True", "true").replace("False", "false").replace("None", "null")
        json_string = re.sub(r'(\w+):', r'"\1":', json_string)
        json_string = re.sub(r',\s*}', '}', json_string)
        json_string = re.sub(r',\s*]', ']', json_string)
        json_string = re.sub(r'\s+', ' ', json_string)
        try:
            json.loads(json_string)
            return json_string
        except json.JSONDecodeError:
            return json_string

    def has(self, key):
        if isinstance(self.data, dict):
            return key in self.data
        elif isinstance(self.data, list):
            return any(isinstance(item, dict) and key in item for item in self.data)
        else:
            return False

    def set(self, key, value):
        if not isinstance(self.data, dict):
            self.data = {}
        self.data[key] = value
        if type(value).__name__ not in self.properties:
            self.properties.append(type(value).__name__)

    def get(self, key, default=None):
        if isinstance(self.data, dict):
            return self.data.get(key, default)
        elif isinstance(self.data, list):
            values = [item[key] for item in self.data if isinstance(item, dict) and key in item]
            return values if values else default
        else:
            return default

    def to_json(self) -> str:
        try:
            return json.dumps(self.to_serializable(), ensure_ascii=False)
        except (TypeError, OverflowError) as e:
            raise ValueError(f"Data contains non-serializable values: {e}")

    def to_serializable(self):
        stack = deque([(self.data, [])])
        result = {}
        visited = set()

        while stack:
            current, path = stack.pop()
            obj_id = id(current)

            if obj_id in visited:
                continue
            visited.add(obj_id)

            if isinstance(current, dict):
                temp_dict = {}
                for key, value in current.items():
                    temp_dict[key] = None
                    stack.append((value, path + [key]))
                if path:
                    parent = result
                    for key in path[:-1]:
                        parent = parent[key]
                    parent[path[-1]] = temp_dict
                else:
                    result.update(temp_dict)
            elif isinstance(current, list):
                temp_list = [None] * len(current)
                for i, item in enumerate(current):
                    stack.append((item, path + [i]))
                if path:
                    parent = result
                    for key in path[:-1]:
                        parent = parent[key]
                    parent[path[-1]] = temp_list
                else:
                    result = temp_list
            elif isinstance(current, Image.Image):
                if path:
                    parent = result
                    for key in path[:-1]:
                        parent = parent[key]
                    parent[path[-1]] = "<Image Object>"
                else:
                    result = "<Image Object>"
            else:
                if path:
                    parent = result
                    for key in path[:-1]:
                        parent = parent[key]
                    parent[path[-1]] = current
                else:
                    result = current

        return result if self.image is None else self.image

    def flatten_data(self):
        flat_dict = {}
        stack = deque([(self.data, "")])
        visited = set()

        while stack:
            obj, parent_key = stack.pop()
            obj_id = id(obj)

            if obj_id in visited:
                continue
            visited.add(obj_id)

            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_key = f"{parent_key}_{key}" if parent_key else key
                    if new_key in flat_dict:
                        new_key = self.get_unique_key(new_key, flat_dict)
                    stack.append((value, new_key))
            elif isinstance(obj, list):
                for index, item in enumerate(obj):
                    new_key = f"{parent_key}_{index}" if parent_key else str(index)
                    if new_key in flat_dict:
                        new_key = self.get_unique_key(new_key, flat_dict)
                    stack.append((item, new_key))
            else:
                flat_dict[parent_key] = obj

        return flat_dict

    def get_unique_key(self, base_key, existing_keys):
        index = 1
        new_key = f"{base_key}_{index}"
        while new_key in existing_keys:
            index += 1
            new_key = f"{base_key}_{index}"
        return new_key

    def __json__(self):
        return self.to_serializable()

    def get_by_path(self, path: str):
        if not path:
            return self.data

        keys = path.split('/')
        stack = deque([(self.data, keys)])
        results = []

        while stack:
            current, remaining_keys = stack.pop()

            if not remaining_keys:
                results.append(current)
                continue

            key = remaining_keys[0]

            if isinstance(current, dict):
                if key in current:
                    stack.append((current[key], remaining_keys[1:]))
            elif isinstance(current, list):
                for item in current:
                    stack.append((item, remaining_keys))

        return results[0] if len(results) == 1 else results if results else None

    def find_value_recursive_by_key(self, field):
        if isinstance(field, str) and '/' in field:
            res = self.get_by_path(field)
            if res is None:
                return []
            return [res] if not isinstance(res, list) else res

        matches = []
        stack = deque([(self.data, False)])
        visited = set()

        while stack:
            data, parsed = stack.pop()
            obj_id = id(data)

            if obj_id in visited:
                continue
            visited.add(obj_id)

            if isinstance(data, dict):
                for k, v in data.items():
                    if k == field:
                        matches.append(v)
                    if isinstance(v, (dict, list)):
                        stack.append((v, False))
                    elif isinstance(v, str) and not parsed:
                        parsed_v = self._try_parse_string(v)
                        if parsed_v is not None:
                            stack.append((parsed_v, True))
            elif isinstance(data, list):
                for item in data:
                    stack.append((item, False))

        return matches

    def _try_parse_string(self, s):
        if not isinstance(s, str):
            return None
        try:
            candidate = s.replace("'", '"')
            return json.loads(candidate)
        except Exception:
            return None