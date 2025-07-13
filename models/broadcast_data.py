import json
from collections import UserDict
from PIL import Image

class BroadcastData(UserDict):
    def __init__(self, obj_input=None):
        super().__init__()
        self.properties = []
        self.image = None  # Store image data if present

        # Handle None explicitly
        if obj_input is None:
            self.data = None
            return

        # Existing logic for other input types
        if isinstance(obj_input, str):
            try:
                obj_input = json.loads(obj_input)
            except json.JSONDecodeError:
                obj_input = {}

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
                        if isinstance(item, Image.Image):
                            self.image = item
                        self.properties.extend([type(v).__name__ for v in item.values()])
                else:
                    self.properties = [type(v).__name__ for v in obj_input]
        elif isinstance(obj_input, Image.Image):
            self.image = obj_input
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

    def to_dict(self) -> dict:
        """
        Returns the internal data as a dictionary.
        Returns:
            A dictionary representation of the internal data.
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
            elif isinstance(obj, Image.Image):
                return "<Image Object>"  # Placeholder for image objects to prevent JSON serialization issues
            else:
                return obj  # Assume other types are JSON-serializable

        return make_serializable(self.data) if self.image is None else self.image

    def flatten_data(self):
        """
        Flattens nested dictionaries or lists into a single-level dictionary.
        If duplicate field names are encountered, adds a suffix to create unique keys.
        """
        flat_dict = {}

        def recursive_flatten(obj, parent_key=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_key = f"{parent_key}_{key}" if parent_key else key
                    if new_key in flat_dict:
                        new_key = self.get_unique_key(new_key, flat_dict)
                    recursive_flatten(value, new_key)
            elif isinstance(obj, list):
                for index, item in enumerate(obj):
                    new_key = f"{parent_key}_{index}" if parent_key else str(index)
                    if new_key in flat_dict:
                        new_key = self.get_unique_key(new_key, flat_dict)
                    recursive_flatten(item, new_key)
            else:
                flat_dict[parent_key] = obj

        recursive_flatten(self.data)
        return flat_dict

    def get_unique_key(self, base_key, existing_keys):
        index = 1
        new_key = f"{base_key}_{index}"
        while new_key in existing_keys:
            index += 1
            new_key = f"{base_key}_{index}"
        return new_key

    def __json__(self):
        """
        Returns a JSON-serializable representation of the object.
        Note: The built-in json module does not use this method by default.
        """
        return self.to_serializable()