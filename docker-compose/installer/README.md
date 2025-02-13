# Lobe Chat Installer

A Python-based installer for Lobe Chat Docker environment.

## Features

- Multi-language support (English and Chinese)
- Automatic file downloading
- Secure secret generation
- Multiple deployment mode support (Local, Remote, S3)

## Installation

Using `uv`:

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

## Usage

```bash
# English interface
python main.py

# Chinese interface
python main.py -l zh_CN

# Custom source URL
python main.py --url https://your-source-url

# Specify host
python main.py --host http://your-host
```

## Development

The project uses modern Python packaging with `pyproject.toml` and is managed with `uv`.
