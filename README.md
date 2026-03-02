# Gospel Piano Key Trainer (Windows Desktop App)

A minimalist desktop application for building a gospel song bank and practicing all 12 keys based on real key frequency.

## Features

- Add songs with:
  - Song name
  - Artist(s) (comma-separated)
  - Primary key
  - Optional modulated key(s)
- Filter song list by key (matches both primary and modulated keys)
- Edit existing songs by selecting from the list and clicking **Update Selected**
- Artist autocomplete suggestions based on artists previously entered
- Key frequency ranking (highest to lowest)
- Export all songs and key frequencies to a `.txt` file
- Light/Dark mode toggle
- Data persistence to `songs_data.json`

## Run

```bash
python gospel_piano_song_bank.py
```

> On Windows, if `python` is unavailable, try `py gospel_piano_song_bank.py`.

## Notes

- The app uses Python's built-in `tkinter` only (no external dependencies).
- Keys available are: `C, Db, D, Eb, E, F, Gb, G, Ab, A, Bb, B`.

## Troubleshooting

- If you saw `_tkinter.TclError: unknown option "-selectcolor"`, update to the latest `gospel_piano_song_bank.py` from this repository.
- Then run:

```bash
python gospel_piano_song_bank.py
```

(Or `py gospel_piano_song_bank.py` on Windows.)
