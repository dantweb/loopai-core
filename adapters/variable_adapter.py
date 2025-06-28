import importlib
from core.models.broadcast_data import BroadcastData


class VariableAdapter:
    """
    Dynamically handles the initialization of multiple adapters defined in the input data.

    Responsible for extracting adapter names from the input, dynamically loading their modules,
    and instantiating them with required parameters.
    """

    def __init__(self, source: str, global_user_id: int, global_loop_id: int, data: BroadcastData):
        """
        Initializes the VariableAdapter and dynamically loads adapters.

        :param source: A string representing the source of initialization.
        :param global_user_id: A unique identifier for the global user context.
        :param global_loop_id: A unique identifier for the global loop context.
        :param data: A BroadcastData object containing configuration for the adapters.
        :raises Exception: If the 'chosen_adapters' cannot be extracted from the input data.
        """
        super().__init__()
        self.source = source
        self.global_user_id = global_user_id
        self.global_loop_id = global_loop_id
        self.broadcast = BroadcastData({})
        self.adapters = {}

        # Load and initialize adapters dynamically from the input data
        self._load_and_initialize_adapters(data)

    def _load_and_initialize_adapters(self, data: BroadcastData):
        """
        Extracts adapter names from the given data and dynamically loads and initializes them.

        This method ensures that all required adapters are successfully loaded and made available
        for future operations.

        :param data: A BroadcastData object containing adapter information.
        :raises Exception: If the 'chosen_adapters' property is not found in the input data.
        """
        # Extract the 'chosen_adapters' from the input data
        chosen_adapters = self._extract_chosen_adapters(data)

        # Dynamically initialize each adapter and store it
        for adapter_name in chosen_adapters:
            self.adapters[adapter_name] = self._initialize_adapter(adapter_name)

    def _extract_chosen_adapters(self, data: BroadcastData) -> list:
        """
        Extracts the list of adapter names ('chosen_adapters') from the input data.

        :param data: A BroadcastData object containing the adapter configuration.
        :return: A list of adapter names to be initialized.
        :raises Exception: If the 'chosen_adapters' property is not found in the input data.
        """
        if 'result' in data:
            if 'response' in data['result']:
                if 'chosen_adapters' in data['result']['response']:
                    return data['result']['response']['chosen_adapters']
                return data['result']['response']
            if 'chosen_adapters' in data['result']:
                return data['result']['chosen_adapters']

        # Raise an exception if 'chosen_adapters' cannot be extracted
        self._log_error("Unable to extract 'chosen_adapters' from data", data)
        raise Exception("No response in data result or 'chosen_adapters' not found.")

    def _initialize_adapter(self, adapter_name: str):
        """
        Dynamically imports and initializes an adapter based on its name.

        :param adapter_name: The name of the adapter to initialize (e.g., 'http', 'filesystem').
        :return: An instance of the dynamically loaded adapter.
        :raises ImportError: If the adapter module or class cannot be found.
        """
        adapter_module = f"core.adapters.{adapter_name}_adapter"

        try:
            # Import the adapter module dynamically
            module = importlib.import_module(adapter_module)

            # Get the adapter class from the module (capitalize the name to follow naming conventions)
            adapter_class_name = f"{adapter_name.capitalize()}Adapter"
            adapter_class = getattr(module, adapter_class_name)

            # Initialize the adapter with required parameters and return it
            return adapter_class(
                source=self.source,
                global_user_id=self.global_user_id,
                global_loop_id=self.global_loop_id
            )

        except ModuleNotFoundError:
            raise ImportError(f"Adapter module '{adapter_module}' not found.")
        except AttributeError:
            raise ImportError(f"Adapter class '{adapter_class_name}' not found in '{adapter_module}'.")

    def _log_error(self, message: str, data: BroadcastData):
        """
        Logs an error message along with relevant data.

        This method assumes the presence of a logger, but falls back to a standard print statement
        if the logger is not available.

        :param message: The error message to log.
        :param data: The BroadcastData object containing the error details.
        """
        try:
            # Attempt to log with the logger, if available
            self.logger.error(f"{message}: {data}")
        except AttributeError:
            # Fallback to print statement if the logger is not set
            print(f"ERROR: {message}: {data}")
