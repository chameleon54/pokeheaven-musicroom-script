# Roblox 4-Key Rhythm Auto-Player

Python script that plays a 4-lane rhythm game (keys `D F J K`) in Roblox. It watches one spot above each hit ring, and presses the key when a note's color covers it. Holding the key while the note stays there handles both tap and hold notes.

Windows only.

## Setup

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

1. Open the game and get to the song screen (set Roblox to the same window/resolution you will play in).
2. Run calibration:
   ```
   python calibrate.py
   ```
   For each of D, F, J, K: hover the mouse over the **upper-inside edge** of that hit circle and press **SPACE**. This writes `config.json`.
3. Start the bot while the track is **empty** (before the first notes arrive):
   ```
   python bot.py
   ```
   It samples the empty track for 2 seconds as its baseline, then starts playing.
4. Press **Q** or **ESC** to stop. All keys are released on exit.

Run the terminal as Administrator if the keys don't register in Roblox.

## Settings (`config.json`)

| Key | Meaning |
|-----|---------|
| `d`, `f`, `j`, `k` | Screen `[x, y]` of each sensor point (set by `calibrate.py`) |
| `color_threshold` | How much the pixel color must change to count as a note. Lower = more sensitive, higher = fewer false hits from stage lights. Default `55` |
| `y_offset` | Pixels added to each sensor's y. Negative moves it up so notes are hit earlier |
| `press_delay_ms` | Wait between detecting a note and pressing the key (the sensor sits above the ring). Default `80` |

Re-run `calibrate.py` if you move or resize the game window (it resets settings to defaults).

## Troubleshooting

- **Hits too early/late:** adjust `press_delay_ms` (raise = later).
- **False presses:** raise `color_threshold`.
- **Missed notes:** lower `color_threshold`, or recalibrate closer to the ring.
- **"config.json not calibrated":** run `calibrate.py`.
- `debug.log` records per-lane color differences (10 lines/sec) to help tune the threshold.
