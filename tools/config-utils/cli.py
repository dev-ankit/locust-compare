"""CLI commands for config-utils."""

import os
import sys
import yaml
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Set, Tuple
import click


def flatten_dict(data: Dict[str, Any], depth: int, parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """
    Flatten a nested dictionary to a specified depth.

    Args:
        data: The dictionary to flatten
        depth: How many levels deep to flatten (0 = unlimited, 1 = root only, no flattening)
        parent_key: The parent key for recursion
        sep: The separator for nested keys

    Returns:
        Flattened dictionary
    """
    # Depth 1 means no flattening - just return the dict as is
    if depth == 1 and not parent_key:
        return data.copy()

    items = {}
    current_depth = len(parent_key.split(sep)) if parent_key else 0

    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key

        # Calculate the depth of the new key
        new_depth = len(new_key.split(sep))

        # If we've reached the depth limit, don't flatten further
        if depth > 0 and new_depth >= depth:
            items[new_key] = value
        elif isinstance(value, dict) and value:
            # Continue flattening
            items.update(flatten_dict(value, depth, new_key, sep=sep))
        else:
            items[new_key] = value

    return items


def unflatten_dict(data: Dict[str, Any], sep: str = '.') -> Dict[str, Any]:
    """
    Unflatten a dictionary with dot-separated keys back to nested structure.

    Args:
        data: The flattened dictionary
        sep: The separator used in keys

    Returns:
        Nested dictionary
    """
    result = {}

    for key, value in data.items():
        parts = key.split(sep)
        current = result

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

    return result


def load_yaml_file(file_path: str) -> Dict[str, Any]:
    """
    Load a YAML file and return its contents.

    Args:
        file_path: Path to the YAML file

    Returns:
        Dictionary containing YAML data

    Raises:
        SystemExit: If file not found or invalid YAML
    """
    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f) or {}

        if not isinstance(data, dict):
            click.echo(f"Error: Root must be a YAML mapping in {file_path}", err=True)
            sys.exit(1)

        return data
    except FileNotFoundError:
        click.echo(f"Error: File not found: {file_path}", err=True)
        sys.exit(1)
    except yaml.YAMLError as e:
        click.echo(f"Error: Invalid YAML in {file_path}: {e}", err=True)
        sys.exit(1)


def make_hashable(value: Any) -> Any:
    """
    Convert a value to a hashable type for set operations.

    Args:
        value: The value to convert

    Returns:
        A hashable representation of the value
    """
    if isinstance(value, dict):
        return tuple(sorted((k, make_hashable(v)) for k, v in value.items()))
    elif isinstance(value, list):
        return tuple(make_hashable(item) for item in value)
    elif isinstance(value, set):
        return frozenset(make_hashable(item) for item in value)
    else:
        return value


def perform_set_operation(
    file1_data: Dict[str, Any],
    file2_data: Dict[str, Any],
    operation: str,
    compare_mode: str,
    depth: int
) -> Dict[str, Any]:
    """
    Perform set operations on two dictionaries.

    Args:
        file1_data: First file data
        file2_data: Second file data
        operation: One of 'union', 'intersect', 'diff', 'rdiff', 'symdiff'
        compare_mode: Either 'keys' or 'kv' (key-value)
        depth: Depth level for comparison (0 = unlimited)

    Returns:
        Dictionary with the result of the set operation
    """
    # Flatten both dictionaries
    flat1 = flatten_dict(file1_data, depth)
    flat2 = flatten_dict(file2_data, depth)

    if compare_mode == 'keys':
        # Compare only keys
        keys1 = set(flat1.keys())
        keys2 = set(flat2.keys())

        if operation == 'union':
            result_keys = keys1 | keys2
        elif operation == 'intersect':
            result_keys = keys1 & keys2
        elif operation == 'diff':
            result_keys = keys1 - keys2
        elif operation == 'rdiff':
            result_keys = keys2 - keys1
        elif operation == 'symdiff':
            result_keys = keys1 ^ keys2
        else:
            result_keys = set()

        # Build result dictionary, preferring values from file1
        result = {}
        for key in result_keys:
            if key in flat1:
                result[key] = flat1[key]
            else:
                result[key] = flat2[key]

    else:  # compare_mode == 'kv'
        # Compare key-value pairs using hashable representations
        # Create sets of (key, hashable_value) tuples
        items1 = set((k, make_hashable(v)) for k, v in flat1.items())
        items2 = set((k, make_hashable(v)) for k, v in flat2.items())

        if operation == 'union':
            # For union, we need to handle conflicts - file1 takes precedence
            result_items = items1 | items2
            result = {}
            for key, _ in result_items:
                # Prefer file1 values
                if key in flat1:
                    result[key] = flat1[key]
                else:
                    result[key] = flat2[key]
        elif operation == 'intersect':
            result_items = items1 & items2
            result = {k: flat1[k] for k, _ in result_items}
        elif operation == 'diff':
            result_items = items1 - items2
            result = {k: flat1[k] for k, _ in result_items}
        elif operation == 'rdiff':
            result_items = items2 - items1
            result = {k: flat2[k] for k, _ in result_items}
        elif operation == 'symdiff':
            result_items = items1 ^ items2
            result = {}
            for key, _ in result_items:
                if key in flat1:
                    result[key] = flat1[key]
                else:
                    result[key] = flat2[key]
        else:
            result = {}

    # Unflatten the result if depth > 1
    # For depth=1, we didn't flatten, so no need to unflatten
    # For depth>1, we need to unflatten back to nested structure
    if depth > 1:
        result = unflatten_dict(result)

    return result


@click.group()
@click.version_option()
def main():
    """config-utils: Capture environment variables, Django settings, and perform YAML set operations."""
    pass


@main.command()
@click.option(
    '--output',
    '-o',
    default='env_config.yaml',
    help='Output file path (default: env_config.yaml)',
    type=click.Path(),
)
@click.option(
    '--format',
    '-f',
    type=click.Choice(['yaml', 'yml'], case_sensitive=False),
    default='yaml',
    help='Output format (default: yaml)',
)
def capture_env(output, format):
    """Capture all environment variables and store them in YAML format."""
    try:
        # Get all environment variables
        env_vars = dict(os.environ)

        # Ensure output path is Path object
        output_path = Path(output)

        # Write to YAML file
        with open(output_path, 'w') as f:
            yaml.dump(env_vars, f, default_flow_style=False, sort_keys=True)

        click.echo(f"✓ Captured {len(env_vars)} environment variables to {output_path}")

    except Exception as e:
        click.echo(f"✗ Error: {str(e)}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    '--output',
    '-o',
    default='django_settings.yaml',
    help='Output file path (default: django_settings.yaml)',
    type=click.Path(),
)
@click.option(
    '--format',
    '-f',
    type=click.Choice(['yaml', 'yml'], case_sensitive=False),
    default='yaml',
    help='Output format (default: yaml)',
)
@click.option(
    '--manage-py',
    '-m',
    default='manage.py',
    help='Path to manage.py (default: manage.py)',
    type=click.Path(exists=True),
)
@click.option(
    '--settings',
    '-s',
    help='Django settings module (e.g., myproject.settings)',
    envvar='DJANGO_SETTINGS_MODULE',
)
def capture_django_settings(output, format, manage_py, settings):
    """Capture Django settings and store them in YAML format.

    Uses 'python manage.py shell' to access Django settings.
    Requires manage.py to be present in the current directory or specify path with --manage-py.
    """
    try:
        # Check if manage.py exists
        manage_path = Path(manage_py)
        if not manage_path.exists():
            click.echo(
                f"✗ Error: manage.py not found at {manage_path}. "
                "Run this command from your Django project root or use --manage-py to specify the path.",
                err=True
            )
            sys.exit(1)

        # Python script to run in Django shell
        django_script = """
import json
from django.conf import settings

settings_dict = {}
for setting in dir(settings):
    if setting.isupper():
        try:
            value = getattr(settings, setting)
            # Convert non-serializable types to strings
            if not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                value = str(value)
            settings_dict[setting] = value
        except Exception as e:
            settings_dict[setting] = f"<Error retrieving value: {str(e)}>"

print(json.dumps(settings_dict))
"""

        # Prepare environment variables
        env = os.environ.copy()
        if settings:
            env['DJANGO_SETTINGS_MODULE'] = settings

        # Run manage.py shell with the script
        result = subprocess.run(
            ['python', str(manage_path), 'shell'],
            input=django_script,
            capture_output=True,
            text=True,
            env=env,
            timeout=30
        )

        if result.returncode != 0:
            click.echo(f"✗ Error running Django shell:", err=True)
            click.echo(result.stderr, err=True)
            sys.exit(1)

        # Parse JSON output
        try:
            settings_dict = json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            click.echo(f"✗ Error: Could not parse Django settings output", err=True)
            click.echo(f"Output: {result.stdout}", err=True)
            sys.exit(1)

        # Ensure output path is Path object
        output_path = Path(output)

        # Write to YAML file
        with open(output_path, 'w') as f:
            yaml.dump(settings_dict, f, default_flow_style=False, sort_keys=True)

        click.echo(f"✓ Captured {len(settings_dict)} Django settings to {output_path}")

    except subprocess.TimeoutExpired:
        click.echo("✗ Error: Django shell command timed out", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Error: {str(e)}", err=True)
        sys.exit(1)


# Set operation commands
def create_set_operation_command(operation: str, description: str):
    """Factory function to create set operation commands."""
    @main.command(name=operation, help=description)
    @click.argument('file1', type=click.Path(exists=True))
    @click.argument('file2', type=click.Path(exists=True))
    @click.option(
        '--compare',
        type=click.Choice(['keys', 'kv'], case_sensitive=False),
        default='kv',
        help='Comparison mode: keys or kv (key-values). Default: kv',
    )
    @click.option(
        '--depth',
        type=int,
        default=1,
        help='How many levels deep to compare. 1 = root keys only, 0 = unlimited (full depth). Default: 1',
    )
    def command(file1, file2, compare, depth):
        try:
            # Load YAML files
            file1_data = load_yaml_file(file1)
            file2_data = load_yaml_file(file2)

            # Perform set operation
            result = perform_set_operation(file1_data, file2_data, operation, compare, depth)

            # Output result as YAML to stdout
            yaml.dump(result, sys.stdout, default_flow_style=False, sort_keys=False, allow_unicode=True)

        except Exception as e:
            click.echo(f"Error: {str(e)}", err=True)
            sys.exit(1)

    return command


# Create all set operation commands
union_cmd = create_set_operation_command(
    'union',
    'Returns all keys (or key-value pairs) present in either file.'
)

intersect_cmd = create_set_operation_command(
    'intersect',
    'Returns only keys (or key-value pairs) present in both files.'
)

diff_cmd = create_set_operation_command(
    'diff',
    'Returns keys (or key-value pairs) in file1 but not in file2 (A - B).'
)

rdiff_cmd = create_set_operation_command(
    'rdiff',
    'Returns keys (or key-value pairs) in file2 but not in file1 (B - A).'
)

symdiff_cmd = create_set_operation_command(
    'symdiff',
    'Returns keys (or key-value pairs) in either file but not in both (symmetric difference).'
)


if __name__ == '__main__':
    main()
