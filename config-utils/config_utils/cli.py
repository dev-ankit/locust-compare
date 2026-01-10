"""CLI commands for config-utils."""

import os
import sys
import yaml
from pathlib import Path
import click


@click.group()
@click.version_option()
def main():
    """config-utils: Capture environment variables and Django settings."""
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
    '--settings',
    '-s',
    help='Django settings module (e.g., myproject.settings)',
    envvar='DJANGO_SETTINGS_MODULE',
)
def capture_django_settings(output, format, settings):
    """Capture Django settings and store them in YAML format.

    Requires Django to be installed and DJANGO_SETTINGS_MODULE to be set,
    or pass it via --settings option.
    """
    try:
        # Set Django settings module if provided
        if settings:
            os.environ['DJANGO_SETTINGS_MODULE'] = settings

        # Check if DJANGO_SETTINGS_MODULE is set
        if 'DJANGO_SETTINGS_MODULE' not in os.environ:
            click.echo(
                "✗ Error: DJANGO_SETTINGS_MODULE not set. "
                "Use --settings option or set the environment variable.",
                err=True
            )
            sys.exit(1)

        # Import Django
        try:
            import django
            from django.conf import settings as django_settings
        except ImportError:
            click.echo(
                "✗ Error: Django is not installed. "
                "Install it with: pip install django",
                err=True
            )
            sys.exit(1)

        # Setup Django
        django.setup()

        # Get all Django settings
        settings_dict = {}
        for setting in dir(django_settings):
            # Skip private/magic attributes
            if setting.isupper():
                try:
                    value = getattr(django_settings, setting)
                    # Convert non-serializable types to strings
                    if not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                        value = str(value)
                    settings_dict[setting] = value
                except Exception as e:
                    settings_dict[setting] = f"<Error retrieving value: {str(e)}>"

        # Ensure output path is Path object
        output_path = Path(output)

        # Write to YAML file
        with open(output_path, 'w') as f:
            yaml.dump(settings_dict, f, default_flow_style=False, sort_keys=True)

        click.echo(f"✓ Captured {len(settings_dict)} Django settings to {output_path}")

    except Exception as e:
        click.echo(f"✗ Error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
