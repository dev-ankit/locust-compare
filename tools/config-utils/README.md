# config-utils

A CLI tool for capturing environment variables and Django settings in YAML format, plus performing set operations on YAML configuration files.

## Features

- **capture-env**: Capture all environment variables and export them to YAML
- **capture-django-settings**: Capture Django project settings and export them to YAML
- **Set Operations**: Compare and merge YAML files using set operations (union, intersect, diff, rdiff, symdiff)

## Installation

### Using uv tool install (Recommended)

Install the tool globally using `uv`:

```bash
uv tool install .
```

Or install from a remote location:

```bash
uv tool install config-utils
```

This will install the `config-utils` executable in your PATH.

### Using uvx

Run the tool directly without installation:

```bash
uvx --from . config-utils capture-env
```

### Using pip

Install from the local directory:

```bash
pip install .
```

Or install in editable mode for development:

```bash
pip install -e .
```

## Usage

### Capture Environment Variables

Capture all environment variables to a YAML file:

```bash
config-utils capture-env
```

This will create `env_config.yaml` with all your environment variables.

#### Options

- `-o, --output PATH`: Specify output file path (default: `env_config.yaml`)
- `-f, --format`: Output format, yaml or yml (default: `yaml`)

#### Examples

```bash
# Capture to custom file
config-utils capture-env -o my_env.yaml

# Capture with yml extension
config-utils capture-env -o config.yml -f yml
```

### Capture Django Settings

Capture Django project settings to a YAML file using `python manage.py shell`:

```bash
# Run from your Django project directory
cd /path/to/your/django/project
config-utils capture-django-settings
```

This will create `django_settings.yaml` with all Django settings.

#### Options

- `-o, --output PATH`: Specify output file path (default: `django_settings.yaml`)
- `-f, --format`: Output format, yaml or yml (default: `yaml`)
- `-m, --manage-py PATH`: Path to manage.py (default: `manage.py`)
- `-s, --settings`: Django settings module (e.g., `myproject.settings`)

#### Examples

```bash
# From Django project root directory
config-utils capture-django-settings

# Specifying settings module via command line
config-utils capture-django-settings -s myproject.settings

# Custom output file
config-utils capture-django-settings -o my_django_config.yaml

# Specify manage.py path if not in current directory
config-utils capture-django-settings -m /path/to/manage.py

# Using DJANGO_SETTINGS_MODULE environment variable
export DJANGO_SETTINGS_MODULE=myproject.settings
config-utils capture-django-settings
```

**Note**: This command must be run from your Django project directory or you must specify the path to `manage.py` using the `--manage-py` option.

### YAML Set Operations

Perform set operations on two YAML configuration files. All operations output valid YAML to stdout.

#### Commands

- `union`: Returns all keys (or key-value pairs) present in either file
- `intersect`: Returns only keys (or key-value pairs) present in both files
- `diff`: Returns keys (or key-value pairs) in file1 but not in file2 (A - B)
- `rdiff`: Returns keys (or key-value pairs) in file2 but not in file1 (B - A)
- `symdiff`: Returns keys (or key-value pairs) in either file but not in both (symmetric difference)

#### Options

- `--compare <mode>`: Comparison mode - `keys` or `kv` (key-values). Default: `kv`
  - `kv`: Compares key-value pairs. Two entries match only if both key AND value are identical
  - `keys`: Compares only keys. Values are ignored when determining matches
- `--depth <n>`: How many levels deep to compare. Default: `1`
  - `1`: Root keys only
  - `2`: Compare up to 2 levels (root and one level of nesting)
  - `0`: Unlimited depth (fully flatten using dot notation)

#### Examples

**file1.yml:**

```yaml
database: postgres
port: 5432
debug: true
```

**file2.yml:**

```yaml
database: postgres
port: 3306
logging: verbose
```

**Find common configuration (intersect with key-values):**

```bash
config-utils intersect file1.yml file2.yml
# Output:
# database: postgres
```

**Find common keys regardless of values:**

```bash
config-utils intersect file1.yml file2.yml --compare keys
# Output:
# database: postgres
# port: 5432
```

**Find all unique configuration (union):**

```bash
config-utils union file1.yml file2.yml
# Output:
# database: postgres
# port: 5432
# debug: true
# logging: verbose
```

**Find what's in file1 but not file2 (diff):**

```bash
config-utils diff file1.yml file2.yml
# Output:
# port: 5432
# debug: true
```

**Find what's in file2 but not file1 (rdiff):**

```bash
config-utils rdiff file1.yml file2.yml
# Output:
# port: 3306
# logging: verbose
```

**Nested comparison with depth:**

**nested1.yml:**

```yaml
database:
  host: localhost
  port: 5432
app:
  name: myapp
```

**nested2.yml:**

```yaml
database:
  host: localhost
  port: 3306
app:
  name: myapp
```

```bash
# Depth 1 - root keys only
config-utils intersect nested1.yml nested2.yml --depth 1
# Output:
# database:
#   host: localhost
#   port: 5432
# app:
#   name: myapp

# Depth 2 - compare nested keys
config-utils intersect nested1.yml nested2.yml --depth 2
# Output:
# database:
#   host: localhost
# app:
#   name: myapp
```

### Using with uvx

You can run the tool directly without installation:

```bash
# Capture environment variables
uvx --from . config-utils capture-env

# With options
uvx --from . config-utils capture-env -o custom.yaml

# Django settings (from Django project directory)
cd /path/to/django/project
uvx --from /path/to/config-utils config-utils capture-django-settings

# Or specify manage.py path
uvx --from /path/to/config-utils config-utils capture-django-settings -m /path/to/manage.py
```

## Requirements

- Python >= 3.8
- click >= 8.0.0
- pyyaml >= 6.0

**For Django settings capture**: The command uses `python manage.py shell`, so Django must be installed in your Django project's environment. The config-utils tool itself does not need Django as a dependency.

## Development

### Setup

```bash
# Clone or navigate to the project directory
cd config-utils

# Install in editable mode with development dependencies
pip install -e ".[dev]"
```

### Running Tests

The project includes comprehensive pytest tests for all set operations functionality.

```bash
# Run all tests
python -m pytest

# Run with coverage report
python -m pytest --cov=cli --cov-report=term-missing

# Run specific test class
python -m pytest tests/test_set_operations.py::TestUnionCommand -v

# Run specific test
python -m pytest tests/test_set_operations.py::TestUnionCommand::test_union_kv_mode -v
```

### Test Coverage

The test suite covers:

- All 5 set operations (union, intersect, diff, rdiff, symdiff)
- Both comparison modes (keys and kv)
- All depth levels (0, 1, 2+)
- Error handling (missing files, invalid YAML, non-dict roots)
- Edge cases (empty files, identical files, no matches)
- Helper functions (flatten_dict, unflatten_dict, make_hashable, perform_set_operation, load_yaml_file)

### Project Structure

```
config-utils/
├── cli.py
├── tests/
│   ├── __init__.py
│   └── test_set_operations.py
├── pyproject.toml
└── README.md
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
