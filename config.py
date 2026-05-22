"""
Configuration constants for the NightShift Work Agent.
"""

NIGHTSHIFT_API_BASE = "https://nightshift-agi.com/api/v1"
CLAUDE_MODEL = "claude-sonnet-4-20250514"
OUTPUT_DIR = "output"
AGENT_NAME = "NightShift Work Agent"
VERSION = "1.0.0"

MAX_FILE_SIZE_BYTES = 50_000
MAX_FILES_TO_REVIEW = 15

REVIEW_FILE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java",
    ".c", ".cpp", ".h", ".cs", ".rb", ".php", ".swift", ".kt",
    ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".cfg",
    ".html", ".css", ".scss", ".sql", ".sh", ".bash",
}

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "env", "dist", "build", ".next", ".nuxt", "vendor",
    "target", ".cargo", "coverage", ".pytest_cache", ".mypy_cache",
}

REQUEST_TIMEOUT = 30
