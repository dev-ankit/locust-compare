"""Tests for YAML set operations."""

import pytest
import yaml
import tempfile
import os
from pathlib import Path
from click.testing import CliRunner
from cli import main, flatten_dict, unflatten_dict, perform_set_operation, load_yaml_file, make_hashable


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


@pytest.fixture
def temp_yaml_files():
    """Create temporary YAML files for testing."""
    files = {}

    # Simple file 1
    file1_data = {
        'database': 'postgres',
        'port': 5432,
        'debug': True
    }

    # Simple file 2
    file2_data = {
        'database': 'postgres',
        'port': 3306,
        'logging': 'verbose'
    }

    # Nested file 1
    nested1_data = {
        'database': {
            'host': 'localhost',
            'port': 5432
        },
        'app': {
            'name': 'myapp'
        }
    }

    # Nested file 2
    nested2_data = {
        'database': {
            'host': 'localhost',
            'port': 3306
        },
        'app': {
            'name': 'myapp'
        }
    }

    # Empty file
    empty_data = {}

    # Identical to file 1
    identical_data = file1_data.copy()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create file 1
        file1 = Path(tmpdir) / 'file1.yml'
        with open(file1, 'w') as f:
            yaml.dump(file1_data, f)
        files['file1'] = str(file1)

        # Create file 2
        file2 = Path(tmpdir) / 'file2.yml'
        with open(file2, 'w') as f:
            yaml.dump(file2_data, f)
        files['file2'] = str(file2)

        # Create nested file 1
        nested1 = Path(tmpdir) / 'nested1.yml'
        with open(nested1, 'w') as f:
            yaml.dump(nested1_data, f)
        files['nested1'] = str(nested1)

        # Create nested file 2
        nested2 = Path(tmpdir) / 'nested2.yml'
        with open(nested2, 'w') as f:
            yaml.dump(nested2_data, f)
        files['nested2'] = str(nested2)

        # Create empty file
        empty = Path(tmpdir) / 'empty.yml'
        with open(empty, 'w') as f:
            yaml.dump(empty_data, f)
        files['empty'] = str(empty)

        # Create identical file
        identical = Path(tmpdir) / 'identical.yml'
        with open(identical, 'w') as f:
            yaml.dump(identical_data, f)
        files['identical'] = str(identical)

        # Create invalid YAML file
        invalid = Path(tmpdir) / 'invalid.yml'
        with open(invalid, 'w') as f:
            f.write('invalid: yaml: content:\n  bad syntax')
        files['invalid'] = str(invalid)

        # Create non-dict file (list)
        list_file = Path(tmpdir) / 'list.yml'
        with open(list_file, 'w') as f:
            yaml.dump(['item1', 'item2'], f)
        files['list'] = str(list_file)

        yield files


class TestFlattenDict:
    """Test flatten_dict function."""

    def test_flatten_depth_1(self):
        """Test flattening with depth 1 (no flattening)."""
        data = {
            'database': {
                'host': 'localhost',
                'port': 5432
            },
            'app': {
                'name': 'myapp'
            }
        }
        result = flatten_dict(data, depth=1)
        assert result == data

    def test_flatten_depth_2(self):
        """Test flattening with depth 2."""
        data = {
            'database': {
                'host': 'localhost',
                'port': 5432
            },
            'app': {
                'name': 'myapp'
            }
        }
        result = flatten_dict(data, depth=2)
        expected = {
            'database.host': 'localhost',
            'database.port': 5432,
            'app.name': 'myapp'
        }
        assert result == expected

    def test_flatten_depth_0(self):
        """Test flattening with depth 0 (unlimited)."""
        data = {
            'level1': {
                'level2': {
                    'level3': 'value'
                }
            }
        }
        result = flatten_dict(data, depth=0)
        expected = {
            'level1.level2.level3': 'value'
        }
        assert result == expected


class TestUnflattenDict:
    """Test unflatten_dict function."""

    def test_unflatten_simple(self):
        """Test unflattening a simple dict."""
        data = {
            'database.host': 'localhost',
            'database.port': 5432,
            'app.name': 'myapp'
        }
        result = unflatten_dict(data)
        expected = {
            'database': {
                'host': 'localhost',
                'port': 5432
            },
            'app': {
                'name': 'myapp'
            }
        }
        assert result == expected


class TestMakeHashable:
    """Test make_hashable function."""

    def test_hashable_dict(self):
        """Test making a dict hashable."""
        data = {'a': 1, 'b': 2}
        result = make_hashable(data)
        assert isinstance(result, tuple)
        assert result == (('a', 1), ('b', 2))

    def test_hashable_list(self):
        """Test making a list hashable."""
        data = [1, 2, 3]
        result = make_hashable(data)
        assert isinstance(result, tuple)
        assert result == (1, 2, 3)

    def test_hashable_nested(self):
        """Test making nested structures hashable."""
        data = {'a': [1, 2], 'b': {'c': 3}}
        result = make_hashable(data)
        assert isinstance(result, tuple)


class TestUnionCommand:
    """Test union command."""

    def test_union_kv_mode(self, runner, temp_yaml_files):
        """Test union with key-value comparison."""
        result = runner.invoke(main, [
            'union',
            temp_yaml_files['file1'],
            temp_yaml_files['file2']
        ])
        assert result.exit_code == 0
        output_data = yaml.safe_load(result.output)
        assert output_data['database'] == 'postgres'
        assert output_data['port'] == 5432  # file1 takes precedence
        assert output_data['debug'] is True
        assert output_data['logging'] == 'verbose'

    def test_union_keys_mode(self, runner, temp_yaml_files):
        """Test union with keys-only comparison."""
        result = runner.invoke(main, [
            'union',
            temp_yaml_files['file1'],
            temp_yaml_files['file2'],
            '--compare', 'keys'
        ])
        assert result.exit_code == 0
        output_data = yaml.safe_load(result.output)
        assert output_data['database'] == 'postgres'
        assert output_data['port'] == 5432  # file1 value
        assert output_data['debug'] is True
        assert output_data['logging'] == 'verbose'


class TestIntersectCommand:
    """Test intersect command."""

    def test_intersect_kv_mode(self, runner, temp_yaml_files):
        """Test intersect with key-value comparison."""
        result = runner.invoke(main, [
            'intersect',
            temp_yaml_files['file1'],
            temp_yaml_files['file2']
        ])
        assert result.exit_code == 0
        output_data = yaml.safe_load(result.output)
        assert output_data == {'database': 'postgres'}

    def test_intersect_keys_mode(self, runner, temp_yaml_files):
        """Test intersect with keys-only comparison."""
        result = runner.invoke(main, [
            'intersect',
            temp_yaml_files['file1'],
            temp_yaml_files['file2'],
            '--compare', 'keys'
        ])
        assert result.exit_code == 0
        output_data = yaml.safe_load(result.output)
        assert output_data['database'] == 'postgres'
        assert output_data['port'] == 5432  # file1 value

    def test_intersect_depth_1(self, runner, temp_yaml_files):
        """Test intersect with depth 1 (root keys only)."""
        result = runner.invoke(main, [
            'intersect',
            temp_yaml_files['nested1'],
            temp_yaml_files['nested2'],
            '--depth', '1',
            '--compare', 'keys'
        ])
        assert result.exit_code == 0
        output_data = yaml.safe_load(result.output)
        assert 'database' in output_data
        assert 'app' in output_data
        assert output_data['database']['port'] == 5432  # file1 value

    def test_intersect_depth_2(self, runner, temp_yaml_files):
        """Test intersect with depth 2 (nested keys)."""
        result = runner.invoke(main, [
            'intersect',
            temp_yaml_files['nested1'],
            temp_yaml_files['nested2'],
            '--depth', '2'
        ])
        assert result.exit_code == 0
        output_data = yaml.safe_load(result.output)
        assert output_data == {
            'database': {'host': 'localhost'},
            'app': {'name': 'myapp'}
        }

    def test_intersect_depth_0(self, runner, temp_yaml_files):
        """Test intersect with depth 0 (unlimited)."""
        result = runner.invoke(main, [
            'intersect',
            temp_yaml_files['nested1'],
            temp_yaml_files['nested2'],
            '--depth', '0'
        ])
        assert result.exit_code == 0
        output_data = yaml.safe_load(result.output)
        # Should have flattened keys
        assert 'app.name' in output_data or 'app' in output_data


class TestDiffCommand:
    """Test diff command."""

    def test_diff_kv_mode(self, runner, temp_yaml_files):
        """Test diff with key-value comparison."""
        result = runner.invoke(main, [
            'diff',
            temp_yaml_files['file1'],
            temp_yaml_files['file2']
        ])
        assert result.exit_code == 0
        output_data = yaml.safe_load(result.output)
        assert output_data == {'port': 5432, 'debug': True}

    def test_diff_keys_mode(self, runner, temp_yaml_files):
        """Test diff with keys-only comparison."""
        result = runner.invoke(main, [
            'diff',
            temp_yaml_files['file1'],
            temp_yaml_files['file2'],
            '--compare', 'keys'
        ])
        assert result.exit_code == 0
        output_data = yaml.safe_load(result.output)
        assert output_data == {'debug': True}


class TestRdiffCommand:
    """Test rdiff command."""

    def test_rdiff_kv_mode(self, runner, temp_yaml_files):
        """Test rdiff with key-value comparison."""
        result = runner.invoke(main, [
            'rdiff',
            temp_yaml_files['file1'],
            temp_yaml_files['file2']
        ])
        assert result.exit_code == 0
        output_data = yaml.safe_load(result.output)
        assert output_data == {'port': 3306, 'logging': 'verbose'}

    def test_rdiff_keys_mode(self, runner, temp_yaml_files):
        """Test rdiff with keys-only comparison."""
        result = runner.invoke(main, [
            'rdiff',
            temp_yaml_files['file1'],
            temp_yaml_files['file2'],
            '--compare', 'keys'
        ])
        assert result.exit_code == 0
        output_data = yaml.safe_load(result.output)
        assert output_data == {'logging': 'verbose'}


class TestSymdiffCommand:
    """Test symdiff command."""

    def test_symdiff_kv_mode(self, runner, temp_yaml_files):
        """Test symdiff with key-value comparison."""
        result = runner.invoke(main, [
            'symdiff',
            temp_yaml_files['file1'],
            temp_yaml_files['file2']
        ])
        assert result.exit_code == 0
        output_data = yaml.safe_load(result.output)
        # Should have port from both files, debug, and logging
        assert 'debug' in output_data
        assert 'logging' in output_data
        assert 'port' in output_data

    def test_symdiff_keys_mode(self, runner, temp_yaml_files):
        """Test symdiff with keys-only comparison."""
        result = runner.invoke(main, [
            'symdiff',
            temp_yaml_files['file1'],
            temp_yaml_files['file2'],
            '--compare', 'keys'
        ])
        assert result.exit_code == 0
        output_data = yaml.safe_load(result.output)
        # Only keys that are not in both
        assert output_data == {'debug': True, 'logging': 'verbose'}


class TestErrorHandling:
    """Test error handling."""

    def test_file_not_found(self, runner, temp_yaml_files):
        """Test error when file is not found."""
        result = runner.invoke(main, [
            'intersect',
            '/nonexistent/file.yml',
            temp_yaml_files['file1']
        ])
        assert result.exit_code == 2  # Click's error code for invalid argument

    def test_invalid_yaml(self, runner, temp_yaml_files):
        """Test error when YAML is invalid."""
        result = runner.invoke(main, [
            'intersect',
            temp_yaml_files['invalid'],
            temp_yaml_files['file1']
        ])
        assert result.exit_code == 1
        assert 'Error' in result.output

    def test_non_dict_root(self, runner, temp_yaml_files):
        """Test error when root is not a dict."""
        result = runner.invoke(main, [
            'intersect',
            temp_yaml_files['list'],
            temp_yaml_files['file1']
        ])
        assert result.exit_code == 1
        assert 'Root must be a YAML mapping' in result.output


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_file(self, runner, temp_yaml_files):
        """Test with empty file."""
        result = runner.invoke(main, [
            'union',
            temp_yaml_files['empty'],
            temp_yaml_files['file1']
        ])
        assert result.exit_code == 0
        output_data = yaml.safe_load(result.output)
        # Should return all from file1
        assert output_data['database'] == 'postgres'

    def test_identical_files_intersect(self, runner, temp_yaml_files):
        """Test intersect with identical files."""
        result = runner.invoke(main, [
            'intersect',
            temp_yaml_files['file1'],
            temp_yaml_files['identical']
        ])
        assert result.exit_code == 0
        output_data = yaml.safe_load(result.output)
        # Should return full file
        assert output_data['database'] == 'postgres'
        assert output_data['port'] == 5432
        assert output_data['debug'] is True

    def test_identical_files_diff(self, runner, temp_yaml_files):
        """Test diff with identical files."""
        result = runner.invoke(main, [
            'diff',
            temp_yaml_files['file1'],
            temp_yaml_files['identical']
        ])
        assert result.exit_code == 0
        output_data = yaml.safe_load(result.output)
        # Should return empty or None
        assert output_data == {} or output_data is None

    def test_no_matches_intersect(self, runner, temp_yaml_files):
        """Test intersect with no matching keys."""
        # Create a file with completely different keys
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump({'different': 'value', 'other': 'data'}, f)
            different_file = f.name

        try:
            result = runner.invoke(main, [
                'intersect',
                temp_yaml_files['file1'],
                different_file
            ])
            assert result.exit_code == 0
            output_data = yaml.safe_load(result.output)
            # Should return empty
            assert output_data == {} or output_data is None
        finally:
            os.unlink(different_file)


class TestLoadYamlFile:
    """Test load_yaml_file function."""

    def test_load_valid_file(self, temp_yaml_files):
        """Test loading a valid YAML file."""
        data = load_yaml_file(temp_yaml_files['file1'])
        assert data['database'] == 'postgres'
        assert data['port'] == 5432

    def test_load_empty_file(self, temp_yaml_files):
        """Test loading an empty YAML file."""
        data = load_yaml_file(temp_yaml_files['empty'])
        assert data == {}

    def test_load_nonexistent_file(self):
        """Test loading a nonexistent file."""
        with pytest.raises(SystemExit) as exc_info:
            load_yaml_file('/nonexistent/file.yml')
        assert exc_info.value.code == 1

    def test_load_invalid_yaml(self, temp_yaml_files):
        """Test loading an invalid YAML file."""
        with pytest.raises(SystemExit) as exc_info:
            load_yaml_file(temp_yaml_files['invalid'])
        assert exc_info.value.code == 1

    def test_load_non_dict_root(self, temp_yaml_files):
        """Test loading a YAML file with non-dict root."""
        with pytest.raises(SystemExit) as exc_info:
            load_yaml_file(temp_yaml_files['list'])
        assert exc_info.value.code == 1


class TestPerformSetOperation:
    """Test perform_set_operation function."""

    def test_union_operation(self):
        """Test union operation."""
        file1 = {'a': 1, 'b': 2}
        file2 = {'b': 3, 'c': 4}
        result = perform_set_operation(file1, file2, 'union', 'kv', 1)
        assert result == {'a': 1, 'b': 2, 'c': 4}

    def test_intersect_operation(self):
        """Test intersect operation."""
        file1 = {'a': 1, 'b': 2, 'c': 3}
        file2 = {'b': 2, 'c': 4, 'd': 5}
        result = perform_set_operation(file1, file2, 'intersect', 'kv', 1)
        assert result == {'b': 2}

    def test_diff_operation(self):
        """Test diff operation."""
        file1 = {'a': 1, 'b': 2, 'c': 3}
        file2 = {'b': 2, 'c': 4}
        result = perform_set_operation(file1, file2, 'diff', 'kv', 1)
        assert result == {'a': 1, 'c': 3}

    def test_rdiff_operation(self):
        """Test rdiff operation."""
        file1 = {'a': 1, 'b': 2}
        file2 = {'b': 2, 'c': 4}
        result = perform_set_operation(file1, file2, 'rdiff', 'kv', 1)
        assert result == {'c': 4}

    def test_symdiff_operation(self):
        """Test symdiff operation."""
        file1 = {'a': 1, 'b': 2}
        file2 = {'b': 2, 'c': 4}
        result = perform_set_operation(file1, file2, 'symdiff', 'kv', 1)
        assert result == {'a': 1, 'c': 4}
