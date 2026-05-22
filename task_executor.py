"""
Task execution engine powered by the Claude API.
Handles code review, research, and document summarization.
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path

import anthropic

from config import (
    CLAUDE_MODEL,
    MAX_FILE_SIZE_BYTES,
    MAX_FILES_TO_REVIEW,
    REVIEW_FILE_EXTENSIONS,
    SKIP_DIRS,
)


class TaskExecutor:
    """Executes digital work tasks using the Claude API."""

    def __init__(self):
        """
        Initialize the executor with an authenticated Anthropic client.
        Raises EnvironmentError if ANTHROPIC_API_KEY is not set.
        """
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY environment variable is not set. "
                "Export your Anthropic API key before running this command."
            )
        self.client = anthropic.Anthropic(api_key=api_key)

    def _call_claude(self, system_prompt, user_prompt):
        """
        Send a message to Claude and return the text response.
        Raises RuntimeError on API failures.
        """
        try:
            message = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return message.content[0].text
        except anthropic.APIConnectionError as exc:
            raise RuntimeError(f"Claude API connection error: {exc}") from exc
        except anthropic.RateLimitError:
            raise RuntimeError(
                "Claude API rate limit exceeded. Please wait a moment and try again."
            ) from None
        except anthropic.APIStatusError as exc:
            raise RuntimeError(
                f"Claude API error {exc.status_code}: {exc.message}"
            ) from exc

    def _collect_repo_files(self, repo_path):
        """
        Walk a cloned repository and collect readable source files.
        Returns a list of (relative path, content) tuples.
        Skips binary files, oversized files, and excluded directories.
        """
        repo_root = Path(repo_path)
        collected = []

        for file_path in sorted(repo_root.rglob("*")):
            if not file_path.is_file():
                continue

            relative = file_path.relative_to(repo_root)
            parts = set(relative.parts[:-1])
            if parts & SKIP_DIRS:
                continue

            if file_path.suffix.lower() not in REVIEW_FILE_EXTENSIONS:
                continue

            if len(collected) >= MAX_FILES_TO_REVIEW:
                break

            try:
                size = file_path.stat().st_size
                if size > MAX_FILE_SIZE_BYTES:
                    content = (
                        f"[File omitted: {size} bytes exceeds the "
                        f"{MAX_FILE_SIZE_BYTES} byte read limit]"
                    )
                else:
                    content = file_path.read_text(encoding="utf-8", errors="replace")
                collected.append((str(relative), content))
            except OSError:
                continue

        return collected

    def review_code(self, github_url):
        """
        Clone a public GitHub repository and produce a structured code review.
        Returns a markdown report string scored across multiple quality dimensions.
        """
        tmp_dir = tempfile.mkdtemp(prefix="nightshift_review_")
        try:
            print(f"Cloning repository: {github_url}")
            result = subprocess.run(
                ["git", "clone", "--depth", "1", github_url, tmp_dir],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"Git clone failed:\n{result.stderr.strip()}"
                )

            files = self._collect_repo_files(tmp_dir)
            if not files:
                raise RuntimeError(
                    "No readable source files found in the repository."
                )

            print(f"Analyzing {len(files)} file(s). Sending to Claude...")

            file_block = "\n\n".join(
                f"### {path}\n```\n{content}\n```"
                for path, content in files
            )

            system_prompt = (
                "You are a senior software engineer performing a professional code review. "
                "You provide detailed, actionable feedback. "
                "Respond only in clean markdown. Do not use emojis."
            )

            user_prompt = f"""Perform a comprehensive code review of the repository at: {github_url}

Score each category from 1 to 10 (10 is best). Provide specific, actionable improvement suggestions for each.

Use exactly these sections in your response:

## Code Quality
Score: X/10
[Assess naming conventions, readability, duplication, complexity, and adherence to language idioms]

## Security Concerns
Score: X/10
[Identify any vulnerabilities, unsafe patterns, hardcoded secrets, or missing input validation]

## Architecture
Score: X/10
[Evaluate module separation, dependency structure, scalability, and design patterns used]

## Documentation Gaps
Score: X/10
[Note missing docstrings, unclear APIs, absent README sections, or undocumented assumptions]

## Improvement Suggestions
[A numbered list of specific, prioritized recommendations ordered by impact]

## Overall Assessment
[A concise paragraph summarizing the repository's strengths and most critical areas for improvement]

---

Source files analyzed:

{file_block}
"""
            return self._call_claude(system_prompt, user_prompt)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def research(self, topic):
        """
        Generate a structured research brief on the given topic using Claude.
        Returns a markdown report string with overview, findings, open questions, and sources.
        """
        print(f"Generating research brief for: {topic}")

        system_prompt = (
            "You are a thorough research analyst. "
            "You produce structured, factual research briefs with clear sections. "
            "Respond only in clean markdown. Do not use emojis."
        )

        user_prompt = f"""Produce a comprehensive research brief on the following topic:

Topic: {topic}

Use exactly these sections in your response:

## Overview
[A concise introduction to the topic, its significance, and its current state of development or understanding]

## Key Findings
[The most important insights, facts, and developments. Present as a numbered list with one to two sentences per item]

## Open Questions
[Unresolved questions, active debates, or areas where expert consensus is lacking. Present as a numbered list]

## Sources to Explore
[Recommended books, academic papers, organizations, databases, and authoritative websites for further research. Include brief annotations explaining what each source offers]
"""
        return self._call_claude(system_prompt, user_prompt)

    def summarize(self, file_path):
        """
        Read a local file and generate a structured summary using Claude.
        Returns a markdown report string.
        Raises FileNotFoundError if the path does not exist.
        Raises ValueError if the path is not a file or is too large.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        size = path.stat().st_size
        max_bytes = MAX_FILE_SIZE_BYTES * 4
        if size > max_bytes:
            raise ValueError(
                f"File is too large to summarize ({size:,} bytes). "
                f"Maximum supported size is {max_bytes:,} bytes."
            )

        print(f"Reading file: {path.name} ({size:,} bytes)")
        content = path.read_text(encoding="utf-8", errors="replace")

        system_prompt = (
            "You are a precise summarization specialist. "
            "You extract core information and present it in a structured format. "
            "Respond only in clean markdown. Do not use emojis."
        )

        user_prompt = f"""Produce a structured summary of the following document.

File: {path.name}

Use exactly these sections in your response:

## Document Overview
[What this document is, its purpose, its scope, and its intended audience]

## Key Points
[The most important facts, arguments, or information. Present as a numbered list]

## Notable Details
[Secondary findings, caveats, edge cases, or specific items worth highlighting]

## Conclusion
[The document's final takeaways, recommendations, or calls to action, if applicable]

---

Document content:

{content}
"""
        return self._call_claude(system_prompt, user_prompt)
