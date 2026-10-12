<div align="center">

# Site Preview Desk

**Packed via Axiox Media**

Temporary local server that loads a website ZIP and optional SQL dump, then previews the site inside the app.

<p>
  <a href="docs/README-zh.md"><img src="https://img.shields.io/badge/中文说明-README--zh-e7c07a?style=for-the-badge" alt="Chinese README" /></a>
</p>

<p>
  <a href="#install">Install</a> ·
  <a href="#features">Features</a> ·
  <a href="#requirements">Requirements</a> ·
  <a href="#architecture">Architecture</a> ·
  <a href="#documentation">FAQ</a>
</p>

<p>
  <img src="https://img.shields.io/badge/platform-Windows_10%2F11-0b0d12?style=flat-square" alt="Windows" />
  <img src="https://img.shields.io/badge/python-3.11%2B-e7c07a?style=flat-square" alt="Python" />
  <img src="https://img.shields.io/badge/ui-zh%20%2F%20en-7ee0c6?style=flat-square" alt="i18n" />
  <img src="https://img.shields.io/badge/preview-in--app-c9a227?style=flat-square" alt="in-app preview" />
</p>

</div>

<div align="center">
  <img src="docs/APPCap.png" alt="Site Preview Desk preview" width="100%" />
</div>

> [!NOTE]
> Windows SmartScreen may warn on the unsigned EXE. That is expected for a local PyInstaller build.

---

## At a glance

| | |
|---|---|
| What | Load a site ZIP (+ optional SQL) and preview it on a temporary local server |
| Where | Fullscreen overlay inside the desk app |
| Stack | FastAPI + static UI + pywebview + PyInstaller |
| Theme | Black-gold default, light switch |
| Languages | 中文 / EN |

<a id="install"></a>

## Install

### 1. GitHub Deploy Desk (recommended)

One-click deploy this repository with [GitHub Deploy Desk](https://github.com/axioxmedia/github-deployer).

1. Get the deployer: https://github.com/axioxmedia/github-deployer
2. Paste this repo URL into Deploy Desk.
3. Read the README in the app, then confirm deploy.

That is the supported install path. Use the source / EXE steps below only if you are already building from a local checkout.

### 2. Run from source or freeze an EXE

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

Result: `dist\SitePreviewDesk.exe`. See `HOW_TO_BUILD.txt`.

<a id="features"></a>

## Features

| Feature | Detail |
|---|---|
| File dialogs | Native picker for ZIP and SQL. No typed paths. |
| Optional SQL | Next is available even if no SQL is chosen. |
| Detection | PHP presence, version, and common extensions. |
| Preview | Extract ZIP, import SQL into a temp SQLite when possible, serve with `php -S` or a pure-Python static server. |
| In-app view | Fullscreen overlay inside the desk window. No second app window. |
| Restart | Clear selections and return to step 1 from step 2 onward. |
| Theme / i18n | Black-gold and light. 中文 / EN. Session memory on. |

<a id="requirements"></a>

## Requirements

| | Minimum | Recommended |
|---|---|---|
| OS | Windows 10 | Windows 11 |
| Python | 3.11 (to build) | 3.11+ |
| PHP | Optional | On PATH if the ZIP contains `.php` |

<a id="architecture"></a>

## Architecture

```
pywebview window
    └── FastAPI (127.0.0.1)
            ├── static/  wizard UI
            └── /api/*   select, analyze, start, stop
                    └── temp extract
                            ├── php -S          (if PHP + .php files)
                            └── http.server     (frozen-safe static fallback)
                                    └── iframe overlay
```

<a id="documentation"></a>

## FAQ

<details>
<summary>The preview is blank.</summary>

Confirm the ZIP has an `index.html` or `index.php` at the root (or under `public/`). PHP pages need a system `php` on PATH.
</details>

<details>
<summary>SmartScreen blocks the EXE.</summary>

The binary is unsigned. Choose More info → Run anyway, or build it yourself with `build_exe.bat`.
</details>

---

Packed via Axiox Media · [axiox.media](https://axiox.media)
