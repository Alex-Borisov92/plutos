"""
Pixel Picker Tool - shows mouse coordinates and pixel color in real-time.
Press Ctrl+C in terminal to exit.
Press Space to capture current position to log.
"""
import time
import ctypes
from ctypes import wintypes
import mss
import keyboard  # pip install keyboard

def get_cursor_pos():
    """Get current cursor position."""
    point = wintypes.POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
    return point.x, point.y        

def get_pixel_color(x, y):
    """Get RGB color at position."""
    with mss.mss() as sct:
        monitor = {"left": x, "top": y, "width": 1, "height": 1}
        img = sct.grab(monitor)
        pixel = img.pixel(0, 0)
        return pixel  # (R, G, B)

def main():
    print("=" * 60)
    print("PIXEL PICKER - Move mouse to see coordinates")
    print("=" * 60)
    print("Press SPACE to save position to log")
    print("Press ESC or Ctrl+C to exit")
    print("=" * 60)
    print()
    
    captured = []
    
    try:
        while True:
            x, y = get_cursor_pos()
            try:
                r, g, b = get_pixel_color(x, y)
                color_str = f"RGB({r:3d}, {g:3d}, {b:3d})"
            except Exception:
                color_str = "RGB(???, ???, ???)"
            
            # Print on same line
            print(f"\rX: {x:5d}  Y: {y:5d}  {color_str}    ", end="", flush=True)
            
            # Check for spacebar to capture
            if keyboard.is_pressed('space'):
                captured.append((x, y, color_str))
                print(f"\n>>> CAPTURED #{len(captured)}: X={x}, Y={y}, {color_str}")
                time.sleep(0.3)  # Debounce
            
            # Check for escape
            if keyboard.is_pressed('esc'):
                break
            
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        pass
    
    print("\n")
    print("=" * 60)
    print("CAPTURED POSITIONS:")
    print("=" * 60)
    for i, (x, y, color) in enumerate(captured, 1):
        print(f"  {i}. PixelCoord({x}, {y})  # {color}")
    print()

if __name__ == "__main__":
    main()
