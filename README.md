# Site Preview Desk

**Packed via Axiox Media**

Temporary local server that loads a website ZIP + SQL dump, detects PHP settings, starts a preview on 127.0.0.1, and opens your default browser.

[![中文说明](https://img.shields.io/badge/中文说明-docs/README--zh.md-gold?style=flat-square)](docs/README-zh.md)

![APP screenshot](docs/APPCap.png)

## Features

- Native file dialog for ZIP and SQL (no typed paths)
- Auto-detect PHP presence, version, and common extensions
- Extract ZIP, attempt SQL import to temporary SQLite, start `php -S` or Python http.server
- Open default browser to the preview URL
- Stop & clean temporary files
- Black-gold theme with light switch, zh/en UI, session memory

## Install

Install with [GitHub Deploy Desk](https://github.com/axioxmedia/github-deployer) or:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

To build the Windows EXE:

```bat
build_exe.bat
```

See `HOW_TO_BUILD.txt` for details.

## License

See LICENSE.
