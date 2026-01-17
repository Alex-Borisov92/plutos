"""
Template Capture Tool - capture card templates from screen.

Usage:
1. Run this script
2. Position your mouse at TOP-LEFT corner of the area to capture
3. Press SPACE to set start point
4. Move mouse to BOTTOM-RIGHT corner
5. Press SPACE again to capture
6. Enter filename (e.g., "A" for Ace, "hearts" for hearts suit)
7. Repeat for all cards/suits
"""
import time
import ctypes
from ctypes import wintypes
from pathlib import Path
import mss
from PIL import Image
import keyboard

# Output directories
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
NUMBER_TEMPLATES_DIR = Path(__file__).parent.parent / "number_templates"


def get_cursor_pos():
    """Get current cursor position."""
    point = wintypes.POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
    return point.x, point.y


def capture_region(x1, y1, x2, y2):
    """Capture screen region and return as PIL Image."""
    left = min(x1, x2)
    top = min(y1, y2)
    width = abs(x2 - x1)
    height = abs(y2 - y1)
    
    with mss.mss() as sct:
        monitor = {"left": left, "top": top, "width": width, "height": height}
        img = sct.grab(monitor)
        return Image.frombytes("RGB", img.size, img.rgb)


def main():
    print("=" * 60)
    print("TEMPLATE CAPTURE TOOL")
    print("=" * 60)
    print()
    print("Instructions:")
    print("  1. Move mouse to TOP-LEFT corner of card element")
    print("  2. Press SPACE to mark start point")
    print("  3. Move mouse to BOTTOM-RIGHT corner")
    print("  4. Press SPACE to capture")
    print("  5. Enter filename when prompted")
    print()
    print("Press ESC to exit")
    print("=" * 60)
    print()
    
    while True:
        # Wait for first point
        print("Move mouse to TOP-LEFT corner, then press SPACE...")
        while True:
            x, y = get_cursor_pos()
            print(f"\rPosition: ({x}, {y})    ", end="", flush=True)
            
            if keyboard.is_pressed('space'):
                x1, y1 = x, y
                print(f"\n>>> Start point set: ({x1}, {y1})")
                time.sleep(0.3)
                break
            if keyboard.is_pressed('esc'):
                print("\nExiting...")
                return
            time.sleep(0.05)
        
        # Wait for second point
        print("Move mouse to BOTTOM-RIGHT corner, then press SPACE...")
        while True:
            x, y = get_cursor_pos()
            w = abs(x - x1)
            h = abs(y - y1)
            print(f"\rPosition: ({x}, {y}) - Size: {w}x{h}    ", end="", flush=True)
            
            if keyboard.is_pressed('space'):
                x2, y2 = x, y
                print(f"\n>>> End point set: ({x2}, {y2})")
                time.sleep(0.3)
                break
            if keyboard.is_pressed('esc'):
                print("\nExiting...")
                return
            time.sleep(0.05)
        
        # Capture the region
        img = capture_region(x1, y1, x2, y2)
        print(f"Captured: {img.size[0]}x{img.size[1]} pixels")
        
        # Ask for filename
        print()
        print("Save options:")
        print("  - For ranks: enter 2, 3, 4, 5, 6, 7, 8, 9, 10, J, Q, K, A")
        print("  - For suits: enter spades, hearts, diamonds, clubs")
        print("  - Or enter custom filename (without .png)")
        print("  - Press ENTER to skip without saving")
        print()
        
        name = input("Filename: ").strip()
        
        if not name:
            print("Skipped.\n")
            continue
        
        # Determine save directory
        if name.lower() in ['spades', 'hearts', 'diamonds', 'clubs']:
            save_dir = TEMPLATES_DIR
        else:
            save_dir = NUMBER_TEMPLATES_DIR
        
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / f"{name}.png"
        
        # Convert to grayscale and save
        img_gray = img.convert('L')
        img_gray.save(save_path)
        
        print(f">>> Saved: {save_path}")
        print(f"    Size: {img.size[0]}x{img.size[1]}")
        print()


if __name__ == "__main__":
    main()
