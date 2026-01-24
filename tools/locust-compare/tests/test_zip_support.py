"""Tests for zip file support."""

import sys
import tempfile
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from compare_runs import _resolve_path, _temp_dirs, compare_reports


class TestResolvePath:
    """Tests for _resolve_path function."""

    def test_regular_directory_unchanged(self, temp_test_dir):
        """Regular directories should be returned unchanged."""
        result = _resolve_path(temp_test_dir)
        assert result == temp_test_dir

    def test_regular_file_unchanged(self, temp_test_dir):
        """Regular files should be returned unchanged."""
        csv_path = temp_test_dir / "report.csv"
        result = _resolve_path(csv_path)
        assert result == csv_path

    def test_zip_file_extraction(self, sample_csv_content):
        """Zip files should be extracted to a temp directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a zip file with report.csv
            zip_path = Path(tmpdir) / "report.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("report.csv", sample_csv_content)

            result = _resolve_path(zip_path)

            # Result should be a different path (extracted)
            assert result != zip_path
            assert result.is_dir()
            # Should contain the extracted file
            assert (result / "report.csv").exists()

    def test_zip_with_single_directory(self, sample_csv_content):
        """Zip containing a single directory should return that directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "report.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                # Put files inside a subdirectory
                zf.writestr("HTML-Report-123/report.csv", sample_csv_content)

            result = _resolve_path(zip_path)

            # Should return the inner directory
            assert result.name == "HTML-Report-123"
            assert (result / "report.csv").exists()

    def test_zip_with_multiple_files(self, sample_csv_content, sample_html_template_args):
        """Zip with multiple files at root should return the extraction root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "report.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("report.csv", sample_csv_content)
                zf.writestr("feature.html", sample_html_template_args)

            result = _resolve_path(zip_path)

            # Should return the temp directory root
            assert (result / "report.csv").exists()
            assert (result / "feature.html").exists()

    def test_invalid_zip_raises_error(self):
        """Files with .zip extension that aren't valid zips should raise."""
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            f.write(b"not a zip file")
            f.flush()

            with pytest.raises(ValueError, match="not a valid zip file"):
                _resolve_path(Path(f.name))

    def test_nonexistent_path_unchanged(self):
        """Non-existent paths should be returned unchanged (let load_report handle error)."""
        path = Path("/nonexistent/path")
        result = _resolve_path(path)
        assert result == path

    def test_temp_dirs_tracked_for_cleanup(self, sample_csv_content):
        """Extracted temp directories should be tracked for cleanup."""
        initial_count = len(_temp_dirs)

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "report.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("report.csv", sample_csv_content)

            _resolve_path(zip_path)

            # Should have added a temp dir
            assert len(_temp_dirs) > initial_count


class TestCompareReportsWithZip:
    """Tests for compare_reports with zip file input."""

    def test_compare_zip_to_zip(self, sample_csv_content, sample_csv_content_v2, capsys):
        """Should be able to compare two zip files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_zip = Path(tmpdir) / "base.zip"
            curr_zip = Path(tmpdir) / "current.zip"

            with zipfile.ZipFile(base_zip, "w") as zf:
                zf.writestr("report.csv", sample_csv_content)

            with zipfile.ZipFile(curr_zip, "w") as zf:
                zf.writestr("report.csv", sample_csv_content_v2)

            result = compare_reports(base_zip, curr_zip, output_format="json")
            assert result == 0

            captured = capsys.readouterr()
            assert "/api/users" in captured.out

    def test_compare_zip_to_directory(self, sample_csv_content, temp_test_dir_v2, capsys):
        """Should be able to compare a zip file to a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_zip = Path(tmpdir) / "base.zip"

            with zipfile.ZipFile(base_zip, "w") as zf:
                zf.writestr("report.csv", sample_csv_content)

            result = compare_reports(base_zip, temp_test_dir_v2, output_format="json")
            assert result == 0

    def test_compare_directory_to_zip(self, temp_test_dir, sample_csv_content_v2, capsys):
        """Should be able to compare a directory to a zip file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            curr_zip = Path(tmpdir) / "current.zip"

            with zipfile.ZipFile(curr_zip, "w") as zf:
                zf.writestr("report.csv", sample_csv_content_v2)

            result = compare_reports(temp_test_dir, curr_zip, output_format="json")
            assert result == 0

    def test_zip_with_nested_directory_structure(
        self, sample_csv_content, sample_csv_content_v2, capsys
    ):
        """Zip with report inside a subdirectory should work."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_zip = Path(tmpdir) / "base.zip"
            curr_zip = Path(tmpdir) / "current.zip"

            with zipfile.ZipFile(base_zip, "w") as zf:
                zf.writestr("HTML-Report-100/report.csv", sample_csv_content)

            with zipfile.ZipFile(curr_zip, "w") as zf:
                zf.writestr("HTML-Report-200/report.csv", sample_csv_content_v2)

            result = compare_reports(base_zip, curr_zip, output_format="json")
            assert result == 0

    def test_zip_with_html_files(self, sample_csv_content, sample_html_template_args, capsys):
        """Zip containing HTML feature files should be parsed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_zip = Path(tmpdir) / "base.zip"
            curr_zip = Path(tmpdir) / "current.zip"

            with zipfile.ZipFile(base_zip, "w") as zf:
                zf.writestr("report.csv", sample_csv_content)
                zf.writestr("feature_test.html", sample_html_template_args)

            with zipfile.ZipFile(curr_zip, "w") as zf:
                zf.writestr("report.csv", sample_csv_content)
                zf.writestr("feature_test.html", sample_html_template_args)

            result = compare_reports(base_zip, curr_zip, output_format="json")
            assert result == 0

            captured = capsys.readouterr()
            # Should include HTML features
            assert "HTML:feature_test" in captured.out
