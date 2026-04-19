# File Access Controls

Sublimate provides robust read/write access controls for agents based on pathspec patterns defined in `sublimate-compose.yml`. This ensures agents can only interact with files they are authorized to access, improving security and preventing accidental modifications.

## Configuration

Each agent definition can include three optional fields:

```yaml
agents:
  my_agent:
    model: favorite-model
    file_access:
      - "./src/*"
      - "./config/*.json"
    read_only_file_access:
      - "./docs/*"
      - "./tests/*"
    deny_file_access:
      - "./secrets/*"
      - "./*.env"
```

### Fields

- **`file_access`**: List of glob patterns where the agent has **both read and write** permissions.
- **`read_only_file_access`**: List of glob patterns where the agent has **read-only** permissions. Write attempts to matching paths will be denied.
- **`deny_file_access`**: List of glob patterns where the agent has **no access** (both read and write denied).

> **Note**: The field `read_file_access` is also supported as an alias for `read_only_file_access` for backward compatibility.

## Pattern Syntax

Patterns use glob-style matching with the following rules:

- `*` matches any sequence of characters within a single directory (does **not** cross directory boundaries).
- `?` matches any single character within a directory.
- `**` matches zero or more directories (recursive).
- Patterns are evaluated relative to the project root directory (the `root_folder` configured for the composer).
- Leading `./` is optional and automatically normalized.

### Examples

| Pattern          | Matches                                 | Does Not Match                     |
|------------------|-----------------------------------------|------------------------------------|
| `*.py`           | `main.py`, `utils.py`                   | `src/main.py`, `tests/unit.py`     |
| `src/*.py`       | `src/main.py`, `src/utils.py`           | `main.py`, `src/lib/parser.py`     |
| `docs/**/*.md`   | `docs/index.md`, `docs/api/v1/readme.md`| `README.md`                        |
| `./*.json`       | `config.json` (in root)                 | `src/config.json`                  |
| `**/*.txt`       | Any `.txt` file anywhere in the project |                                    |

## Precedence

When a file path matches multiple patterns, the most restrictive permission wins, in this order:

1. **Deny** (`deny_file_access`) – highest priority
2. **Read-only** (`read_only_file_access`)
3. **Read/write** (`file_access`) – lowest priority

If a file path matches **no patterns**, access is **denied** by default.

## How It Works

### Agent Initialization

When a composer parses `sublimate-compose.yml`, it extracts the file access patterns for each agent and passes them to the `WorkerAgent` constructor. The agent stores these patterns and provides a `check_file_access(file_path, mode)` method that evaluates permissions.

### Tool Wrapping

The `read_file` and `write_file` tools are automatically wrapped with permission checks during agent initialization. When an agent attempts to read or write a file:

1. The wrapped tool calls `check_file_access` with the file path and mode (`"read"` or `"write"`).
2. If access is denied, the tool returns an error message: `"Access denied to read|write file: <path>"`.
3. If access is allowed, the original tool function is invoked.

### Path Resolution

File paths provided to tools can be absolute or relative. Relative paths are resolved relative to the agent's `root_folder`. Absolute paths are checked to ensure they fall under the `root_folder`; if not, access is denied.

## Examples

### Basic Restriction

```yaml
agents:
  coder:
    model: deepseek-coder
    file_access:
      - "./src/**/*.py"
      - "./tests/**/*.py"
    read_only_file_access:
      - "./requirements.txt"
      - "./README.md"
    deny_file_access:
      - "./.env"
      - "./secrets/**"
```

With this configuration:
- The `coder` agent can read and write any `.py` file under `src/` and `tests/`.
- It can read `requirements.txt` and `README.md` but cannot modify them.
- It cannot read or write anything under `secrets/` or the `.env` file.

### Strict Sandboxing

```yaml
agents:
  reviewer:
    model: reviewer-model
    file_access:
      - "./reports/*.md"
    read_only_file_access:
      - "./src/**/*.py"
    deny_file_access:
      - "./*"  # deny everything else
```

Here:
- The `reviewer` can only write markdown files in the `reports/` directory.
- It can read Python source code but not modify it.
- All other files are inaccessible.

## Testing Access Controls

Unit tests for file access patterns are available in `tests/test_permissions.py`. You can run them with:

```bash
uv run pytest tests/test_permissions.py
```

Integration tests verify that the wrapped tools correctly enforce permissions when agents are instantiated via the composer.

## Limitations

- Pattern matching is case-sensitive and uses forward slashes as directory separators (even on Windows).
- Symlinks are not specially handled; they are resolved to their real paths.
- Permission checks occur only at the tool level; internal agent operations (like loading prompt files) bypass these checks (they are considered trusted).

## Future Enhancements

- Support for regex patterns.
- Dynamic permission updates at runtime.
- Audit logging of file access attempts.
