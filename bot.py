import json
from collections import deque
import time
import keyboard
import mss
import numpy as np
import pydirectinput

pydirectinput.PAUSE = 0
KEYS = ["d", "f", "j", "k"]

with open("config.json") as f:
    cfg = json.load(f)
thr = cfg["color_threshold"]
delay = cfg.get("press_delay_ms", 80) / 1000  # sensor sits above the ring; wait for the note to arrive
# y_offset shifts the sample point so notes are hit slightly early
pts = [(cfg[k][0], cfg[k][1] + cfg["y_offset"]) for k in KEYS]
if any(x == 0 and y == 0 for x, y in pts):
    raise SystemExit("config.json not calibrated. Run calibrate.py first.")

# smallest box covering all points; (x, y) -> (x - left, y - top) inside it
left, top = min(p[0] for p in pts), min(p[1] for p in pts)
right, bottom = max(p[0] for p in pts), max(p[1] for p in pts)
R = 3  # patch radius: averaging 7x7 pixels smooths stage-light noise
box = {"left": left - R, "top": top - R, "width": right - left + 1 + 2 * R, "height": bottom - top + 1 + 2 * R}
rel = [(y - top + R, x - left + R) for x, y in pts]  # patch centers (row, col)

held = {k: False for k in KEYS}
pressed = set()  # keys actually down (lags `held` by `delay`)
pending = deque()  # (due_time, key, is_down); FIFO is correct because the delay is constant


def sample(sct):
    img = np.asarray(sct.grab(box))[:, :, :3]  # BGR(A) -> BGR
    return np.array([img[r - R:r + R + 1, c - R:c + R + 1].mean(axis=(0, 1)) for r, c in rel])


with mss.mss() as sct:
    for s in range(cfg.get("start_delay_s", 5), 0, -1):  # time to click into Roblox so the baseline isn't of the terminal
        print(f"Switch to Roblox now... {s}", end="\r", flush=True)
        time.sleep(1)
    print("Sampling baseline for 2s (median of frames, so passing notes are ignored)...")
    t = time.time()
    shots = []
    while time.time() - t < 2:
        shots.append(sample(sct))
    base = np.median(shots, axis=0)
    print("Baseline captured. Running - press Q or ESC to stop.")
    frames, t0, all_held_since = 0, time.time(), None
    log, last_log = open("debug.log", "w", buffering=1), 0
    try:
        while not (keyboard.is_pressed("q") or keyboard.is_pressed("esc")):
            cur = sample(sct)
            diff = np.abs(cur - base).sum(axis=1)
            # all 4 lanes "held" for 1s = baseline is stale (window switched/changed), not 4 hold notes: retake it
            all_held_since = (all_held_since or time.time()) if all(held.values()) else None
            if all_held_since and time.time() - all_held_since > 1:
                base, all_held_since = cur.copy(), None
                print("\nBaseline looked stale, retaken.")
                continue
            for i, (k, d) in enumerate(zip(KEYS, diff)):
                if not held[k] and d <= thr:
                    base[i] += (cur[i] - base[i]) * 0.02  # follow slow background drift
                if d > thr and not held[k]:
                    pending.append((time.time() + delay, k, True))
                    held[k] = True
                elif d <= thr and held[k]:
                    pending.append((time.time() + delay, k, False))
                    held[k] = False
            while pending and pending[0][0] <= time.time():
                _, k, down = pending.popleft()
                (pydirectinput.keyDown if down else pydirectinput.keyUp)(k)
                pressed.add(k) if down else pressed.discard(k)
            frames += 1
            if time.time() - last_log >= 0.1:  # 10 lines/sec: time, diffs (D F J K), held keys
                last_log = time.time()
                log.write(f"{last_log - t0:.1f} {diff.astype(int).tolist()} {''.join(k for k in KEYS if held[k])}\n")
            if time.time() - t0 >= 1:
                print(f"\rFPS: {frames}  ", end="", flush=True)
                frames, t0 = 0, time.time()
    finally:
        log.close()
        for k in list(pressed):
            pydirectinput.keyUp(k)
        print("\nStopped. All keys released.")
