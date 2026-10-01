# Notebook demonstrations

The executable implementation lives in `src/music_support`; the PDF deliverable
notebook imports that package and demonstrates the same workflow. The automated
regression coverage is in `tests/test_system.py`, and the command-line entry point
is also available:

```bash
python -m music_support
python -m pytest -q
```
