from emporio_agent.config import PROJECT_ROOT
from emporio_agent.textutils import EMOJI

# Versioned text content (generated/local folders such as .venv, .cache and runtime are excluded).
TEXT_LOCATIONS = ["src", "tests", "evals", "scripts", "conversations"]
TEXT_SUFFIXES = {".py", ".md", ".yaml", ".toml", ".txt"}


def test_repository_has_no_emojis():
    files = [PROJECT_ROOT / "README.md", PROJECT_ROOT / "pyproject.toml", PROJECT_ROOT / ".env.example"]
    for folder in TEXT_LOCATIONS:
        files += [p for p in (PROJECT_ROOT / folder).rglob("*") if p.suffix in TEXT_SUFFIXES and "sessions" not in p.parts]
    offenders = []
    for path in files:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if EMOJI.search(line):
                offenders.append(f"{path.relative_to(PROJECT_ROOT)}:{number}")
    assert not offenders, offenders
