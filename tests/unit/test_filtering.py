from pathlib import Path

from PIL import Image
import os


def filter_binary_data(data):
    filtered_data = {}
    for key, value in data.items():
        # Check for PIL Image objects
        if isinstance(value, Image.Image):
            continue
        # Check for bytes or bytearray
        if isinstance(value, (bytes, bytearray)):
            continue
        # Add additional checks for image paths or URLs if needed
        if isinstance(value, str) and value.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')):
            continue
        filtered_data[key] = value
    return filtered_data


current_file = Path(__file__).resolve()   # absolute Path to the current file
current_dir = current_file.parent
image = os.path.join(current_dir, '../_data/input/img/binary_fitr_test.jpg')

# Example usage
data = {
    'name': 'Sample Post',
    'content': 'This is a sample content.',
    'image': Image.open(image),  # This is a PIL Image object
    'profile_pic': 'https://example.com/fraudblock.jpg',
    'binary_data': bytearray(b'\x00\x01\x02\x03'),
    'category': 'News'
}

filtered_data = filter_binary_data(data)
print(filtered_data)
