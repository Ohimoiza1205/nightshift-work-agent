# NightShift Work Agent

An autonomous CLI agent that connects to the NightShift AGI marketplace (nightshift-agi.com) and executes digital tasks powered by Claude. It browses jobs, services, and profiles via the REST API, and performs code review, research, and document summarization with structured, verifiable output.

Built as a working demonstration of what a first class agent participant looks like on the NightShift platform.

## What It Does

NightShift Work Agent bridges two systems:

1. The NightShift AGI marketplace at nightshift-agi.com, where AI agents and humans post jobs, list services, and register profiles.
2. The Anthropic Claude API, which powers task execution including code review, research synthesis, and document summarization.

Browse commands query the live NightShift API with no credentials required. Task commands accept a target (a GitHub URL, a topic, or a file path), collect content, send it to Claude with a structured prompt, and save the result as a timestamped markdown report.

## Live Demo Output

### Browsing Jobs on the Marketplace

Pulls real job listings from the NightShift API and renders them as a formatted table.

![Browse Jobs](docs/screenshots/browse_jobs.png)

### Browsing Services

Lists all 189+ services currently registered on the platform.

![Browse Services](docs/screenshots/browse_services.png)

### Running a Code Review

Clones any public GitHub repository, reads key source files, and sends them to Claude for analysis.

![Code Review Command](docs/screenshots/code_review_command.png)

The review scores the codebase across five dimensions: code quality, security, architecture, documentation, and provides specific improvement recommendations.

![Code Review Output](docs/screenshots/code_review_output.png)

A full sample report is available at [docs/sample_review_report.md](docs/sample_review_report.md)

## Installation

Requires Python 3.9 or later.

```bash
git clone https://github.com/Ohimoiza1205/nightshift-work-agent.git
cd nightshift-work-agent
pip install -r requirements.txt
```

Set your Anthropic API key (required only for review, research, and summarize commands):

```bash
# Linux / macOS
export ANTHROPIC_API_KEY=your_key_here
```

```powershell
# Windows PowerShell
$env:ANTHROPIC_API_KEY = "your_key_here"
```

```cmd
:: Windows Command Prompt
set ANTHROPIC_API_KEY=your_key_here
```

Browse commands work without an API key.

## Usage

Browse the marketplace:

```
python agent.py browse-jobs
python agent.py browse-services
python agent.py browse-profiles
```

Code review (analyzes a public GitHub repo, scores across 5 dimensions):

```
python agent.py review https://github.com/user/repo
```

Research brief (structured brief on any topic):

```
python agent.py research "federated learning"
```

Document summarization:

```
python agent.py summarize path/to/document.txt
```

All reports are saved as timestamped markdown files in the `output/` directory.

## Architecture

```
nightshift-work-agent/
  agent.py              CLI entry point. Argument parsing and command dispatch.
  nightshift_client.py  REST client for all NightShift API endpoints.
  task_executor.py      Claude API integration for review, research, and summarization.
  report_generator.py   Table formatting, report headers, and file persistence.
  config.py             Constants: API base URL, model name, file limits, skip lists.
  requirements.txt      Dependencies: requests, anthropic.
  output/               Generated reports saved here.
  docs/                 Screenshots and sample output.
```

Each module has a single responsibility. `agent.py` contains no business logic. `task_executor.py` contains no formatting. `report_generator.py` contains no network calls.

## API Integration

NightShift AGI Marketplace base URL: `https://nightshift-agi.com/api/v1`

```
GET /jobs         List all jobs (no auth)
GET /jobs/:id     Get a single job (no auth)
GET /services     List all services (no auth)
GET /profiles     List all profiles (no auth)
```

Task commands send structured prompts to `claude-sonnet-4-20250514` via the official Anthropic Python SDK. All calls use `max_tokens=4096` and a task specific system prompt.

## License

MIT License. See LICENSE for the full text.
