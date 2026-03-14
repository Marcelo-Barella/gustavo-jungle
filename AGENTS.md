# Agents

## Cursor Cloud specific instructions

This is a single-process Python pygame-ce game with no external services, databases, or APIs.

### Running the game

See `README.md` for install/run commands. On headless environments, set `SDL_AUDIODRIVER=dummy` to suppress ALSA errors (audio is not required). The game renders at 1024x768 and needs a graphical display (the Cloud VM desktop or Xvfb).

### Lint and tests

The repo has no linter config, no test suite, and no build step. Syntax-check all Python files with `python3 -m py_compile <file>`. There are 21 `.py` files under `gustavo_jungle/`.

### Gotchas

- pygame-ce (not classic pygame) is the required package; `pip install -r requirements.txt` installs it.
- The game entry point is `gustavo_jungle/main.py` and must be run from the `gustavo_jungle/` directory (or adjust `PYTHONPATH`) because imports are relative to that directory.
- ESC quits the game immediately (no pause menu).
