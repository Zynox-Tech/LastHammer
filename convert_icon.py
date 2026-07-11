"""
Run this once to convert your logo.png into a proper Windows .ico file.
Requires Pillow:  pip install Pillow

Usage:
    python convert_icon.py
"""
import os
import sys

def convert():
    try:
        from PIL import Image
    except ImportError:
        print("Installing Pillow...")
        os.system(f"{sys.executable} -m pip install Pillow")
        from PIL import Image

    script_dir = os.path.dirname(os.path.abspath(__file__))
    png_path   = os.path.join(script_dir, "assets", "logo.png")
    ico_path   = os.path.join(script_dir, "assets", "logo.ico")

    if not os.path.exists(png_path):
        print(f"ERROR: logo.png not found at {png_path}")
        return

    img = Image.open(png_path)
    img = img.convert("RGBA")

    # Generate multiple sizes for a good Windows icon
    sizes = [(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)]
    icons = []
    for size in sizes:
        resized = img.resize(size, Image.LANCZOS)
        icons.append(resized)

    icons[0].save(
        ico_path,
        format="ICO",
        sizes=[(s[0], s[1]) for s in sizes],
        append_images=icons[1:]
    )
    print(f"OK  Saved icon to: {ico_path}")
    print()
    print("Now run  create_shortcut.bat  to add Last Hammer to your Desktop.")

if __name__ == "__main__":
    convert()
    input("\nPress Enter to close...")