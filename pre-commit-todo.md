# Pre-commit Issues TODO

This document tracks all the changes needed to pass pre-commit hooks.

## Summary

- **Ruff**: 91 issues across Python files
- **Pyright**: Multiple type checking issues
- **Markdownlint**: 71+ markdown formatting issues
- **Other hooks**: All passing ✅

---

## 1. Ruff Issues (Python Linting & Formatting)

### tools/config-utils/cli.py

**Issues to fix:**

1. Line 34: Remove unused variable `current_depth`

   ```python
   # REMOVE: current_depth = len(parent_key.split(sep)) if parent_key else 0
   ```

2. Lines 95, 256, 364: Replace `open()` with `Path.open()`
   - Import `from pathlib import Path`
   - Replace `open(file_path)` with `Path(file_path).open()`
   - Replace `open(output_path, 'w')` with `Path(output_path).open('w')`

3. Line 130: Function `perform_set_operation` is too complex
   - PLR0912: Too many branches (24 > 12)
   - PLR0915: Too many statements (53 > 50)
   - **Action**: Consider refactoring into smaller functions

4. Lines 183, 184: Use set comprehensions instead of generators

   ```python
   # CHANGE FROM:
   items1 = set((k, make_hashable(v)) for k, v in flat1.items())
   # TO:
   items1 = {(k, make_hashable(v)) for k, v in flat1.items()}
   ```

5. Lines 228, 306, 394: Line too long (>100 chars)
   - Line 228: Docstring for `main()` - split across lines
   - Line 306: Error message - split string concatenation
   - Line 394: Help text - split across lines

6. Lines 246, 294: Unused function argument `format`
   - Either use the parameter or prefix with underscore: `_format`

### tools/config-utils/tests/test_set_operations.py

**Issues to fix:**

1. Lines 52, 65, 101, 107, 147, 159, 184, 191, 229, 236, 272, 279, 315, 322, 348, 354: Replace `open()` with `Path.open()`
   - Import `from pathlib import Path`
   - Replace all instances of `open(temp_file, 'w')` pattern

### tools/locust-compare/compare_runs.py

**Issues to fix:**

1. Lines 51, 231, 248, 272, 329, 378, 409, 426, 434: Replace `open()` with `Path.open()`
   - Import `from pathlib import Path`
   - Replace `open()` calls with `Path().open()`

2. Line 79: Function `extract_from_html` is too complex
   - PLR0912: Too many branches (15 > 12)
   - **Action**: Consider extracting parsing logic into helper functions

3. Line 166: Function `load_report` is too complex
   - PLR0912: Too many branches (18 > 12)
   - **Action**: Split file type handling into separate functions

4. Lines 208, 214, 221: Replace `os.path` with `pathlib`
   - PTH118: `os.path.join()` → use `/` operator with Path
   - PTH119: `os.path.basename()` → use `Path.name`
   - PTH123: `os.path.dirname()` → use `Path.parent`

5. Line 319: Ambiguous variable name `l` (E741)
   - Rename to something descriptive like `line` or `item`

6. Line 521: Line too long
   - Split the line

### tools/locust-compare/tests/*.py

**Multiple test files with PTH123 violations:**

- `conftest.py`: Lines 14, 27, 28, 29, 30, 52, 56, 60, 64, 75, 79, 91, 93
- `test_compare_reports.py`: Lines 6, 14
- `test_html_extraction.py`: Lines 11, 24, 37, 46, 62, 78, 92, 109, 124
- `test_html_feature_map.py`: Line 6
- `test_load_report.py`: Lines 11, 27, 43, 59, 75, 96, 115, 144, 171
- `test_markdown_output.py`: Lines 11, 22
- `test_metrics.py`: Line 6
- `test_row.py`: Line 6
- `test_utils.py`: Lines 7, 17, 29, 39, 45, 56, 68, 80, 92, 104, 116, 123, 132
- `test_zip_support.py`: Lines 17, 36, 61, 86, 113, 138, 165, 191, 217, 241, 262

**Action**: Replace all `open()` with `Path().open()` in test files

### tools/wt-worktree/wt/*.py

**Issues to fix:**

- `cli.py`: Lines 15, 22 - PTH123 violations
- `config.py`: Lines 14, 102, 127, 205 - PTH123 violations; Line 14 - PTH118 violation
- `git.py`: Lines 47, 73, 91, 94 - PTH119 violations
- `prompts.py`: Line 86 - PTH123 violation
- `shell.py`: Lines 129, 130 - PTH118 violations
- `worktree.py`: Lines 72, 84, 89, 103, 107, 121, 151, 158, 176 - PTH119 violations; Line 166 - PTH118 violation

**Action**: Replace `os.path` functions with `pathlib.Path` equivalents

### tools/wt-worktree/tests/*.py

**Issues to fix:**

- `conftest.py`: Line 31 - PTH123 violation
- `test_cli.py`: Lines 133, 193, 252, 300, 327, 349, 414, 506, 652 - PTH123 violations
- `test_config.py`: Lines 12, 32, 51, 95, 132, 182, 202, 244, 284, 330 - PTH123 violations
- `test_git.py`: Lines 17, 25, 50, 61, 87 - PTH123 violations
- `test_worktree.py`: Lines 149, 165, 186, 236, 289, 363, 418, 569, 673 - PTH123 violations

**Action**: Replace all `open()` with `Path().open()`

---

## 2. Pyright Issues (Type Checking)

### General approach

1. Add missing type hints to function signatures
2. Import `from typing import` necessary types (Dict, List, Optional, Any, etc.)
3. Fix type mismatches
4. Handle Optional/None cases properly

**Files with type issues:**

- All Python files in `tools/config-utils/`, `tools/locust-compare/`, and `tools/wt-worktree/`

**Recommended approach:**

- Run `prek run pyright` after fixing ruff issues
- Fix type errors incrementally, file by file
- Start with main modules before test files

---

## 3. Markdownlint Issues

### README.md (root)

- Line 12: Line too long (83 > 80)
- **Action**: Split long lines or add `.markdownlint.json` to relax line length

### Agents.md

- Lines 70, 74, 82: Line too long
- **Action**: Reformat or configure longer line length for docs

### tools/config-utils/README.md

**Issues:**

- MD024: Multiple duplicate headings ("Options", "Examples")
- MD013: Multiple line length violations
- MD040: Missing language specifiers on fenced code blocks

**Actions:**

1. Make headings unique (e.g., "Options" → "Command Options", "Subcommand Options")
2. Split long lines or relax line length
3. Add language to code blocks: ` ```bash ` or ` ```yaml `

### tools/locust-compare/README.md

**Issues:**

- MD013: Line length violations (lines 3, 10, 23, 107, 154, 166, 167, 172, 189)
- MD040: Missing code block languages (lines 76, 140, 151, 177)
- MD033: Inline HTML on line 107

**Actions:**

1. Split long lines
2. Add ` ```bash ` or ` ```python ` to code blocks
3. Replace inline HTML `<img>` with markdown image syntax

### tools/wt-worktree/README.md

**Issues:**

- MD013: Line length violations (lines 3, 7, 73, 75, 140)
- MD040: Missing code block languages (lines 165, 224)

**Actions:**

1. Split long lines
2. Add ` ```bash ` to code blocks

### tools/wt-worktree/PRD.md

**Issues:**

- MD013: Line length violations
- MD036: Emphasis used instead of heading (multiple lines)

**Actions:**

1. Convert emphasized text to proper headings
2. Split long lines

### tools/wt-worktree/notes.md

**Issues:**

- MD013: Multiple line length violations
- MD040: Missing code block language (line 31)

**Actions:**

1. Split long lines
2. Add ` ```bash ` to code block

---

## 4. Configuration Options

### Option 1: Fix all issues (Recommended for production)

Work through each section above systematically.

### Option 2: Relax some rules

Add to `pyproject.toml`:

```toml
[tool.ruff.lint]
ignore = [
    # ... existing ignores ...
    "PTH123",  # Allow open() instead of Path.open()
    "PLR0912", # Allow complex branches
    "PLR0915", # Allow many statements
]
```

Create `.markdownlint.json`:

```json
{
  "MD013": { "line_length": 120 },
  "MD033": false,
  "MD024": false,
  "MD036": false
}
```

### Option 3: Disable specific hooks temporarily

Comment out hooks in `.pre-commit-config.yaml` while fixing issues incrementally.

---

## Recommended Fix Order

1. **Start with auto-fixable issues**:

   ```bash
   prek run ruff --all-files
   prek run ruff-format --all-files
   ```

2. **Fix manual ruff issues** (unused variables, pathlib migration)
   - Estimated effort: 2-3 hours
   - Files: ~30 Python files

3. **Fix markdown issues**
   - Estimated effort: 1-2 hours
   - Or relax rules with `.markdownlint.json`

4. **Fix type checking issues** (most complex)
   - Estimated effort: 3-4 hours
   - Or temporarily disable pyright hook

5. **Re-run all hooks**:

   ```bash
   prek run --all-files
   ```

---

## Quick Win: Minimal Changes to Pass

If you want to pass pre-commit quickly without major refactoring:

1. Add to `pyproject.toml` ignores:

   ```toml
   "PTH123", "PTH118", "PTH119",  # Allow os.path and open()
   "PLR0912", "PLR0915",           # Allow complex functions
   "E741",                         # Allow short variable names
   "ARG001",                       # Allow unused arguments
   "C401",                         # Allow generators
   ```

2. Create `.markdownlint.json` with relaxed rules

3. Temporarily comment out pyright hook in `.pre-commit-config.yaml`

This will leave only critical issues (like unused variables and line length) to fix manually.
