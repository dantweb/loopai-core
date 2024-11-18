import os
from PIL import Image

from core.adapters.file_adapter_interface import FileAdapterInterface

class ImageAdapter(FileAdapterInterface):

    def __init__(self, file_path_template: str):
        super().__init__()
        self.file_path_template = file_path_template

    def read(self, *args, **kwargs):
        filename = self.get_full_path(self.file_path_template)
        # Not implemented because it's not required for images as per the provided context.
        return filename

    def write(self, step_id: str, data: dict) -> bool:
        self.logger.info(f"[ImageAdapter::write] Writing image to file...")
        self.logger.info(f"[ImageAdapter::write] data type of {type(data)} and data: {str(data)}")
        raise Exception("DEBUGGER STOPPS HERE")
        image = data['result']
        # Replace {{SESSION_ID}} with the actual session_id
        filename = self.get_full_path(self.file_path_template)
        # Ensure the directory exists
        directory = os.path.dirname(filename)

        if not os.path.exists(directory):
            os.makedirs(directory)

        try:
            image.save(filename)
            # Verify if the image is saved correctly
            if os.path.exists(filename):
                self.logger_service.log(f"Image saved successfully: {filename}")
                return True
            else:
                raise IOError(f"Failed to save image: {filename}")

        except Exception as e:
            raise IOError(f"An error occurred while saving the image: {str(e)}")
