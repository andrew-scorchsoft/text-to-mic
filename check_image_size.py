from PIL import Image
import os

icon_dir = 'assets/icons'
for filename in os.listdir(icon_dir):
    if filename.endswith('.png'):
        path = os.path.join(icon_dir, filename)
        img = Image.open(path)
        print(f"{filename}: {img.size}") 