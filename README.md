# WhyCode

> **AI-powered Git history explorer that explains why code exists, not just who wrote it.**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/github/license/VaishnaviPatil-gif/WhyCode)
![GitHub Actions](https://img.shields.io/github/actions/workflow/status/VaishnaviPatil-gif/WhyCode/test.yml?branch=main)
![Version](https://img.shields.io/badge/version-0.1.0-green)

---

## What is WhyCode?

Git can tell you:

* **Who** changed a line (`git blame`)
* **When** it changed (`git log`)
* **What** changed (`git diff`)

But it rarely tells you:

* Why was this code introduced?
* What problem was it solving?
* Why was this design chosen?
* How did this file evolve over time?

**WhyCode** bridges that gap by combining Git history with AI-powered analysis to generate human-readable explanations of code evolution.

Instead of manually reading dozens of commits, WhyCode summarizes the intent behind code changes in seconds.

---

## Features

| Feature                  | Description                                                                 |
| ------------------------ | --------------------------------------------------------------------------- |
| 🔍 Explain Mode          | Analyze a file using Git blame and generate AI explanations for code chunks |
| 📅 Timeline Mode         | Summarize how a file evolved across its Git history                         |
| 🤖 Multiple AI Providers | Supports OpenAI, Claude, and local Ollama models                            |
| ⚡ Local AI Support       | Run completely offline with Ollama                                          |
| 💾 Smart Caching         | Cache explanations to avoid repeated AI requests                            |
| 📊 JSON Output           | Machine-readable output for automation and CI pipelines                     |
| 🎯 Confidence Scoring    | AI rates confidence and context quality for each explanation                |

---

## Why WhyCode?

Imagine joining a new project.

You discover a strange function, a complicated flag, or an unusual workaround.

Normally you'd have to:

1. Search commit history
2. Read multiple diffs
3. Track related changes
4. Ask the original author

WhyCode automates that workflow and answers:

> "Why is this code here?"

---

## Installation

### Clone Repository

```bash
git clone https://github.com/VaishnaviPatil-gif/WhyCode.git
cd WhyCode
```

### Install

```bash
pip install -e .
```

### Development Installation

```bash
pip install -e ".[dev]"
```

---

## Quick Start

### Explain a File

```bash
whycode app.py
```

### Generate Timeline

```bash
whycode app.py --timeline
```

### JSON Output

```bash
whycode app.py --json
```

### Use OpenAI

```bash
whycode app.py --provider openai
```

### Use Claude

```bash
whycode app.py --provider claude
```

### Use Ollama

```bash
whycode app.py --provider ollama
```

---

## Example Output

### Explain Mode

```text
─────────────────── whycode cli.py ───────────────────

Lines 1–226 │ ea31271 │ Initial CLI implementation

Summary:
Initial CLI implementation for whycode project.

Rationale:
This commit established the command-line interface,
provider selection system, and project structure.

Confidence: 95/100
Context Quality: High
```

---

### Timeline Mode

```text
──────────────── whycode timeline ────────────────

2026-06  Initial project structure
2026-06  Added Git parsing functionality
2026-06  Added AI provider support
2026-06  Added caching system
2026-06  Improved CLI output formatting
```

---

## Architecture

```text
whycode
│
├── cli.py
├── git_parser.py
├── ai_engine.py
├── cache.py
├── formatter.py
├── config.py
├── models.py
│
└── ai
    ├── base.py
    ├── openai_provider.py
    ├── claude_provider.py
    └── ollama_provider.py
```

### Workflow

```text
Git History
     │
     ▼
Git Parser
     │
     ▼
Blame Chunks + Commit Context
     │
     ▼
AI Provider
     │
     ▼
Explanation Generation
     │
     ▼
Cache
     │
     ▼
Rich Terminal Output / JSON
```

---

## Supported Providers

| Provider | Local | API Key Required |
| -------- | ----- | ---------------- |
| OpenAI   | ❌     | ✅                |
| Claude   | ❌     | ✅                |
| Ollama   | ✅     | ❌                |

---

## Ollama Setup

Install Ollama:

https://ollama.com

Pull a model:

```bash
ollama pull qwen3:4b
```

Verify installation:

```bash
ollama list
```

Example:

```text
qwen3:4b
```

Run WhyCode:

```bash
whycode app.py --provider ollama --model qwen3:4b
```

---

## Environment Variables

| Variable                 | Description         |
| ------------------------ | ------------------- |
| WHYCODE_DEFAULT_PROVIDER | Default AI provider |
| OPENAI_API_KEY           | OpenAI API key      |
| ANTHROPIC_API_KEY        | Anthropic API key   |
| WHYCODE_OPENAI_MODEL     | OpenAI model        |
| WHYCODE_CLAUDE_MODEL     | Claude model        |
| WHYCODE_OLLAMA_MODEL     | Ollama model        |
| OLLAMA_BASE_URL          | Ollama endpoint     |
| WHYCODE_CACHE_DIR        | Cache directory     |
| WHYCODE_CACHE_TTL        | Cache lifetime      |

---

## Running Tests

```bash
python -m pytest
```

Run linting:

```bash
python -m ruff check .
```

Run coverage:

```bash
pytest --cov=whycode
```

---

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch

```bash
git checkout -b feature/my-feature
```

3. Commit your changes

```bash
git commit -m "feat: add new feature"
```

4. Push and open a Pull Request

---

## Roadmap

* [ ] Line-range explanations
* [ ] GitHub PR integration
* [ ] Commit issue-link detection
* [ ] VS Code Extension
* [ ] JetBrains Plugin
* [ ] Interactive Terminal UI
* [ ] Repository-wide analysis
* [ ] Export explanations to Markdown

---

## Author

**Vaishnavi Patil**

GitHub:
https://github.com/VaishnaviPatil-gif

---

## License

MIT License

See the LICENSE file for details.
