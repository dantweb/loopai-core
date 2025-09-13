import base64
import io
import os
from readline import set_completer_delims

from PIL import Image

from core.adapters.file_adapter_interface import FileAdapterInterface
from core.models.broadcast_data import BroadcastData



class ImageAdapter(FileAdapterInterface):

    def __init__(self, file_path_template: str):
        super().__init__()
        self.file_path_template = file_path_template

    async def read(self, *args, **kwargs):
        filename = self.get_full_path(self.file_path_template)
        # Not implemented because it's not required for images as per the provided context.
        return filename

    async def write(self, step_id: str, data: BroadcastData) -> bool:
        self.logger.info(f"[ImageAdapter::write] Writing image to file...")
        self.logger.info(f"[ImageAdapter::write] data type of {type(data)}")
        self.logger.info(f"[ImageAdapter::write] data: {str(data)}")
        d = BroadcastData(data)
        self.logger.info(f"[ImageAdapter::write] data type of {type(d)}")
        self.logger.info(f"[ImageAdapter::write] data {str(d['result'])}")

        image = data["result"]["image_base64"]
        if len(image) == len(d["result"]["image_base64"]):
            self.logger.info(f"[ImageAdapter::write] YEEEEEEESESESESESW \n\n\n\n")

        generated_image_bytes = base64.b64decode(image)

        generated_image = Image.open(io.BytesIO(generated_image_bytes))
        self.logger.info(f"[ImageAdapter::write] image type of {type(image)}")

        filename = self.get_full_path(self.file_path_template)
        directory = os.path.dirname(filename)
        if not os.path.exists(directory):
            os.makedirs(directory)

        try:
            generated_image.save(filename)
            if os.path.exists(filename):
                self.logger.log(f"Image saved successfully: {filename}")
                return True
            else:
                raise IOError(f"Failed to save image: {filename}")

        except Exception as e:
            raise IOError(f"An error occurred while saving the image: {str(e)}")
