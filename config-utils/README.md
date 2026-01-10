# config-utils

A CLI tool for capturing environment variables and Django settings in YAML format.

## Features

- **capture-env**: Capture all environment variables and export them to YAML
- **capture-django-settings**: Capture Django project settings and export them to YAML

## Installation

### Using uvx (Recommended)

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

### For Django support

Install with Django optional dependencies:

```bash
pip install ".[django]"
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

Capture Django project settings to a YAML file:

```bash
config-utils capture-django-settings
```

This will create `django_settings.yaml` with all Django settings.

#### Options

- `-o, --output PATH`: Specify output file path (default: `django_settings.yaml`)
- `-f, --format`: Output format, yaml or yml (default: `yaml`)
- `-s, --settings`: Django settings module (e.g., `myproject.settings`)

#### Examples

```bash
# Using DJANGO_SETTINGS_MODULE environment variable
export DJANGO_SETTINGS_MODULE=myproject.settings
config-utils capture-django-settings

# Specifying settings module via command line
config-utils capture-django-settings -s myproject.settings

# Custom output file
config-utils capture-django-settings -o my_django_config.yaml -s myproject.settings
```

### Using with uvx

You can run the tool directly without installation:

```bash
# From the project directory
uvx --from . config-utils capture-env

# With options
uvx --from . config-utils capture-env -o custom.yaml

# Django settings
uvx --from . config-utils capture-django-settings -s myproject.settings
```

## Requirements

- Python >= 3.8
- click >= 8.0.0
- pyyaml >= 6.0
- Django >= 3.2 (optional, for capture-django-settings)

## Development

### Setup

```bash
# Clone or navigate to the project directory
cd config-utils

# Install in editable mode with development dependencies
pip install -e .
```

### Project Structure

```
config-utils/
├── config_utils/
│   ├── __init__.py
│   └── cli.py
├── pyproject.toml
└── README.md
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
