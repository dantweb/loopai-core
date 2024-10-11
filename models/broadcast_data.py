import json
from collections import UserDict

class BroadcastData(UserDict):
    def __init__(self, obj_input=None):
        super().__init__()
        self.properties = []

        # If obj_input is a string, attempt to parse it as JSON
        if isinstance(obj_input, str):
            try:
                obj_input = json.loads(obj_input)
            except json.JSONDecodeError:
                obj_input = {}  # Default to an empty dictionary if parsing fails

        # If obj_input is a BroadcastData instance, use its data
        if isinstance(obj_input, BroadcastData):
            obj_input = obj_input.data

        if isinstance(obj_input, dict):
            self.data = obj_input
            self.properties = [type(v).__name__ for v in self.data.values()]
        elif isinstance(obj_input, list):
            self.data = obj_input
            if obj_input:
                if all(isinstance(item, dict) for item in obj_input):
                    for item in obj_input:
                        self.properties.extend([type(v).__name__ for v in item.values()])
                else:
                    self.properties = [type(v).__name__ for v in obj_input]
        else:
            self.data = {}

    def has(self, key):
        if isinstance(self.data, dict):
            return key in self.data
        elif isinstance(self.data, list):
            return any(isinstance(item, dict) and key in item for item in self.data)
        else:
            return False  # Handle other data types if necessary

    def set(self, key, value):
        if not isinstance(self.data, dict):
            self.data = {}  # Convert to dict if it was a list or something else
        self.data[key] = value
        if type(value).__name__ not in self.properties:
            self.properties.append(type(value).__name__)

    def get(self, key, default=None):
        if isinstance(self.data, dict):
            return self.data.get(key, default)
        elif isinstance(self.data, list):
            # Collect values from all dicts in the list that have the key
            values = [item[key] for item in self.data if isinstance(item, dict) and key in item]
            return values if values else default
        else:
            return default  # Handle other data types if necessary

    def to_json(self) -> str:
        """
        Serializes the internal data to a JSON-formatted string.
        Returns:
            A JSON-formatted string representation of the internal data.
        """
        try:
            json_string = json.dumps(self.to_serializable(), ensure_ascii=False)
            return json_string
        except (TypeError, OverflowError) as e:
            raise ValueError(f"Data contains non-serializable values: {e}")

    def __json__(self):
        """
        Returns a JSON-serializable representation of the object.
        Note: The built-in json module does not use this method by default.
        """
        return self.to_serializable()

    def to_serializable(self):
        """
        Recursively converts the data to a JSON-serializable format,
        replacing any nested BroadcastData instances with their data.
        """

        def make_serializable(obj):
            if isinstance(obj, BroadcastData):
                return make_serializable(obj.data)
            elif isinstance(obj, dict):
                return {key: make_serializable(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [make_serializable(item) for item in obj]
            else:
                return obj  # Assume other types are JSON-serializable

        return make_serializable(self.data)
