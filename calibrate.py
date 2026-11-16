import ctypes
import json
import time

user32 = ctypes.windll.user32
VK_SPACE = 0x20


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def space_down():
    return user32.GetAsyncKeyState(VK_SPACE) & 0x8000


cfg = {"color_threshold": 55, "y_offset": -15, "press_delay_ms": 80}

for k in ["d", "f", "j", "k"]:
    print(f"Hover mouse over the upper-inside edge of the {k.upper()} circle, then press SPACE...")
    while not space_down():
        time.sleep(0.01)
    p = POINT()
    user32.GetCursorPos(ctypes.byref(p))
    cfg[k] = [p.x, p.y]
    print(f"  {k.upper()} = ({p.x}, {p.y})")
    while space_down():  # wait for release so one press = one capture
        time.sleep(0.01)

with open("config.json", "w") as f:
    json.dump(cfg, f, indent=2)
print("Saved config.json. Run: python bot.py")
