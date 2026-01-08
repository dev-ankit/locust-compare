"""Tests for markdown output functionality."""
import pytest
import sys
import json
import tempfile
from pathlib import Path
from io import StringIO

sys.path.insert(0, str(Path(__file__).parent.parent))
from compare_runs import compare_reports, _verdict_to_emoji


class TestMarkdownOutput:
    """Tests for markdown output functionality."""

    def test_verdict_to_emoji_better(self):
        """Test emoji for 'better' verdict."""
        assert _verdict_to_emoji("better") == "✅"

    def test_verdict_to_emoji_worse(self):
        """Test emoji for 'worse' verdict."""
        assert _verdict_to_emoji("worse") == "❌"

    def test_verdict_to_emoji_same(self):
        """Test emoji for 'same' verdict."""
        assert _verdict_to_emoji("same") == "➖"

    def test_verdict_to_emoji_none(self):
        """Test emoji for None verdict."""
        assert _verdict_to_emoji(None) == ""

    def test_markdown_output_structure(self, temp_test_dir, temp_test_dir_v2, capsys):
        """Test that markdown output has correct structure."""
        result = compare_reports(temp_test_dir, temp_test_dir_v2, output_format="markdown")
        assert result == 0

        captured = capsys.readouterr()
        output = captured.out

        # Should have markdown headers
        assert "# Locust Performance Comparison" in output
        assert "## Aggregated" in output
        assert "### Endpoint:" in output

        # Should have markdown table syntax
        assert "|" in output
        assert "---" in output

    def test_markdown_output_includes_metrics(self, temp_test_dir, temp_test_dir_v2, capsys):
        """Test that markdown output includes all expected metrics."""
        compare_reports(temp_test_dir, temp_test_dir_v2, output_format="markdown")

        captured = capsys.readouterr()
        output = captured.out

        # Should have metric names in tables
        assert "Requests/s" in output
        assert "Request Count" in output
        assert "Average Response Time" in output
        assert "95%" in output

    def test_markdown_output_includes_emojis(self, temp_test_dir, temp_test_dir_v2, capsys):
        """Test that markdown output includes emoji indicators."""
        compare_reports(temp_test_dir, temp_test_dir_v2, output_format="markdown", show_verdict=True)

        captured = capsys.readouterr()
        output = captured.out

        # Should have emoji indicators for verdicts
        assert "✅" in output or "❌" in output or "➖" in output

    def test_markdown_output_no_verdict(self, temp_test_dir, temp_test_dir_v2, capsys):
        """Test markdown output without verdict column."""
        compare_reports(temp_test_dir, temp_test_dir_v2, output_format="markdown", show_verdict=False)

        captured = capsys.readouterr()
        output = captured.out

        # Should NOT have Verdict column in tables
        lines = output.split('\n')
        header_lines = [l for l in lines if 'Metric' in l and '|' in l]
        assert len(header_lines) > 0
        for header in header_lines:
            assert "Verdict" not in header

    def test_markdown_output_no_color_codes(self, temp_test_dir, temp_test_dir_v2, capsys):
        """Test that markdown output does not contain ANSI color codes."""
        compare_reports(temp_test_dir, temp_test_dir_v2, output_format="markdown")

        captured = capsys.readouterr()
        output = captured.out

        # Should NOT have ANSI color codes
        assert "\033[32m" not in output
        assert "\033[31m" not in output
        assert "\033[0m" not in output

    def test_markdown_table_format(self, temp_test_dir, temp_test_dir_v2, capsys):
        """Test that markdown tables are properly formatted."""
        compare_reports(temp_test_dir, temp_test_dir_v2, output_format="markdown", show_verdict=True)

        captured = capsys.readouterr()
        output = captured.out
        lines = output.split('\n')

        # Find table lines
        table_lines = [l for l in lines if l.startswith('|') and 'Metric' in l]
        assert len(table_lines) > 0

        # Check that separator line follows header
        for i, line in enumerate(lines):
            if 'Metric' in line and line.startswith('|'):
                # Next line should be separator
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    assert '---' in next_line
                    assert next_line.startswith('|')

    def test_markdown_with_html_features(self, temp_dir_with_html, capsys):
        """Test markdown output includes HTML features section."""
        with tempfile.TemporaryDirectory() as other_dir:
            other = Path(other_dir)
            (other / "report.csv").write_text("""Type,Name,Request Count
GET,/api/test,100
,Aggregated,100
""")
            # Copy the HTML file
            import shutil
            for html_file in temp_dir_with_html.glob("*.html"):
                if html_file.name != "htmlpublisher-wrapper.html":
                    shutil.copy(html_file, other / html_file.name)

            compare_reports(temp_dir_with_html, other, output_format="markdown")

            captured = capsys.readouterr()
            output = captured.out

            # Should have HTML Features section
            assert "## HTML Features" in output
            assert "### Feature:" in output

    def test_markdown_output_values(self, temp_test_dir, temp_test_dir_v2, capsys):
        """Test that markdown output contains correct values."""
        compare_reports(temp_test_dir, temp_test_dir_v2, output_format="markdown")

        captured = capsys.readouterr()
        output = captured.out

        # Should contain values from both base and current
        assert "1000" in output  # base request count
        assert "1200" in output  # current request count


class TestMarkdownCompatibility:
    """Test that markdown output doesn't break existing functionality."""

    def test_json_still_works(self, temp_test_dir, temp_test_dir_v2, capsys):
        """Test that JSON output is not affected by markdown changes."""
        result = compare_reports(temp_test_dir, temp_test_dir_v2, output_format="json")
        assert result == 0

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "__Aggregated__" in data

    def test_normal_output_still_works(self, temp_test_dir, temp_test_dir_v2, capsys):
        """Test that normal human-readable output still works."""
        result = compare_reports(temp_test_dir, temp_test_dir_v2, output_format="text")
        assert result == 0

        captured = capsys.readouterr()
        output = captured.out

        # Should have section headers without markdown syntax
        assert "Aggregated" in output
        assert "# Locust" not in output  # No markdown headers

    def test_color_output_still_works(self, temp_test_dir, temp_test_dir_v2, capsys):
        """Test that colorized output still works."""
        result = compare_reports(temp_test_dir, temp_test_dir_v2, output_format="text", colorize=True)
        assert result == 0

        captured = capsys.readouterr()
        output = captured.out

        # Should have ANSI color codes
        assert "\033[32m" in output or "\033[31m" in output
