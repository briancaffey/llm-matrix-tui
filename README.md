# Matrix Rain TUI

A Python-based Terminal User Interface for visualizing high-throughput LLM streaming in a Matrix-style rain effect.

**Current Version:** 0.0.2 (Multilingual Prompts & Enhanced Features)

## Overview

Matrix Rain TUI provides a real-time visualization of concurrent LLM streaming operations, displaying them as falling characters in the style of the Matrix movie. The application supports multiple concurrent streams with multilingual prompts, creating a dynamic and visually appealing demonstration of AI capabilities across different languages and topics.

## Setup Options

### Option A — Local Development (uv + .venv)

**Use case:** Direct development on host system (Mac, Ubuntu, etc.)

#### Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) installed globally

#### Steps

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd llm-matrix-tui
   ```

2. Create `.env` from sample:
   ```bash
   cp .env.sample .env
   ```

3. Sync dependencies:
   ```bash
   uv sync
   ```

4. Run the application:
   ```bash
   uv run python -m matrix_tui
   ```

5. Run tests:
   ```bash
   uv run pytest
   ```

6. Format code:
   ```bash
   make black
   ```

### Option B — Containerized (Docker / Docker Compose)

**Use case:** Ensure consistent environment and easier portability.

#### Using Docker Compose (Recommended)

```bash
# Build and run
docker compose up --build

# Run in background
docker compose up -d --build
```

#### Using Docker directly

```bash
# Build the image
docker build -t matrix-tui .

# Run the container
docker run -it --env-file .env matrix-tui
```

## Commands Summary

| Command | Description |
|---------|-------------|
| `uv run python -m matrix_tui` | Run the application locally |
| `make black` | Format all Python code |
| `uv run pytest` | Run tests |
| `make test` | Run tests (alternative) |
| `make run` | Run application (alternative) |
| `make install` | Install dependencies |
| `make clean` | Clean up build artifacts |
| `docker compose up --build` | Build and run with Docker Compose |

## Configuration

Copy `.env.sample` to `.env` and modify the values as needed:

```env
OPENAI_BASE_URL=http://localhost:8000
OPENAI_API_KEY=sk-local-1234
OPENAI_MODEL=llama-3.1-8b-instruct
```

Docker Compose will automatically load the `.env` file.

## Prompts Configuration

The application uses a `prompts.yml` file to define multilingual prompts that are randomly selected for each streaming column. This allows for diverse, multilingual content generation.

### Prompts File Structure

The `prompts.yml` file contains a list of prompts with the following structure:

```yaml
prompts:
  - prompt: "Your user prompt here"
    system_prompt: "You are a helpful assistant. Please answer in [language]."
    lang: "en"  # Language code (ISO 639-1)
```

### Supported Languages

The default prompts file includes prompts in multiple languages:
- **English (en)** - 20 prompts covering AI, technology, science, and philosophy
- **Chinese (zh)** - 20 prompts in Simplified Chinese
- **Japanese (ja)** - 20 prompts in Japanese
- **Korean (ko)** - 20 prompts in Korean
- **Russian (ru)** - 20 prompts in Russian
- **Thai (th)** - 20 prompts in Thai
- **French (fr)** - 20 prompts in French
- **German (de)** - 20 prompts in German
- **Italian (it)** - 20 prompts in Italian

### Using Custom Prompts

You can specify a custom prompts file using the `--prompts` or `-p` argument:

```bash
# Use a custom prompts file
uv run python -m matrix_tui --prompts my_custom_prompts.yml

# Run with multiple columns and custom prompts
uv run python -m matrix_tui --columns 5 --prompts multilingual_prompts.yml
```

### Creating Your Own Prompts

To create your own prompts file:

1. Create a new YAML file (e.g., `my_prompts.yml`)
2. Follow the structure shown above
3. Add as many prompts as you want
4. Use standard ISO 639-1 language codes for the `lang` field
5. Ensure each prompt has a corresponding system prompt that instructs the AI to respond in the target language

Example custom prompts file:
```yaml
prompts:
  - prompt: "Explain quantum physics in simple terms"
    system_prompt: "You are a helpful physics tutor. Please answer in English."
    lang: "en"
  - prompt: "¿Cómo funciona la fotosíntesis?"
    system_prompt: "Eres un asistente útil. Por favor responde en español."
    lang: "es"
```

### Fallback Behavior

If the prompts file cannot be loaded or is invalid, the application will fall back to a set of default English prompts to ensure the application continues to function.

## Project Structure

```
matrix-tui/
├── src/
│   └── matrix_tui/
│       ├── __init__.py
│       ├── __main__.py
│       ├── config.py
│       ├── llm.py
│       ├── prompt_loader.py
│       ├── renderer.py
│       ├── supervisor.py
│       └── vertical_column.py
├── tests/
│   └── test_*.py
├── prompts.yml
├── .env.sample
├── .gitignore
├── .dockerignore
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── pyproject.toml
└── README.md
```

## Development

### Dependencies

- **Core:** `python-dotenv` for environment variable loading, `openai` for LLM API access, `blessed` for terminal UI, `pyyaml` for prompts configuration
- **Development:** `pytest` for testing, `black` for code formatting

### Code Formatting

This project uses Black for code formatting with the following configuration:
- Line length: 88 characters
- Target Python version: 3.11+

### Testing

Tests are located in the `tests/` directory and can be run with:
```bash
uv run pytest
```

## Features

- **Multilingual Support**: Prompts in 9 different languages (English, Chinese, Japanese, Korean, Russian, Thai, French, German, Italian)
- **Concurrent Streaming**: Support for multiple parallel LLM streams (up to terminal width)
- **Random Prompt Selection**: Each column gets a unique, randomly selected prompt
- **Customizable Prompts**: Easy-to-use YAML configuration for prompts
- **Terminal UI**: Beautiful Matrix-style falling character visualization
- **Docker Support**: Containerized deployment options
- **Robust Error Handling**: Fallback prompts ensure continuous operation

## Next Steps

Future enhancements may include:
- Additional language support
- Prompt categories and filtering
- Performance optimizations
- Enhanced visual effects
- Configuration UI

## License

MIT License - see LICENSE file for details.
