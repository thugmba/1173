"""
Extract and run all Python cells from VIZ.qmd in a shared namespace,
reporting errors with cell number and line number.
"""
import re
import sys
import io
import traceback
import os

# Change to the Lectures directory so relative file paths work
os.chdir(os.path.join(os.path.dirname(__file__), "Lectures"))

QMD_PATH = "VIZ.qmd"

# ── Mock display only — keep real seaborn/plotly ─────────────────────────────
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.show = lambda *a, **kw: None

import numpy as np
import pandas as pd
import seaborn as sns

# Silence plotly renderer so it doesn't open a browser
try:
    import plotly.io as pio
    pio.renderers.default = 'json'   # silent renderer
except Exception:
    pass

# Patch seaborn/plotly show calls
try:
    import plotly.graph_objects as _go_mod
    _orig_show = _go_mod.Figure.show
    _go_mod.Figure.show = lambda self, *a, **kw: None
except Exception:
    pass

try:
    import plotly.express as _px_mod
except Exception:
    pass

# Patch fig.show for all plotly figures
try:
    import plotly.basedatatypes as _base
    _base.BaseFigure.show = lambda self, *a, **kw: None
except Exception:
    pass

# ── Parse cells ──────────────────────────────────────────────────────────────
with open(QMD_PATH, encoding='utf-8') as f:
    content = f.read()

cell_pattern = re.compile(r'```\{python\}(.*?)```', re.DOTALL)
cells = []
for m in cell_pattern.finditer(content):
    start_char = m.start()
    line_num = content[:start_char].count('\n') + 1
    cells.append((len(cells) + 1, line_num, m.group(1)))

print(f"Found {len(cells)} Python cells\n")

# ── Run cells ────────────────────────────────────────────────────────────────
ns = {
    '__builtins__': __builtins__,
    'plt': plt,
    'np': np,
    'pd': pd,
    'matplotlib': matplotlib,
    'sns': sns,
}

errors = []

for cell_num, line_num, code in cells:
    code = code.strip()
    if not code:
        continue

    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()

    try:
        exec(compile(code, f'<cell {cell_num}>', 'exec'), ns)
        plt.close('all')
    except Exception as e:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        tb = traceback.format_exc()
        errors.append({
            'cell': cell_num,
            'qmd_line': line_num,
            'error': type(e).__name__,
            'msg': str(e),
            'traceback': tb,
            'code': code,
        })
        print(f"CELL {cell_num:3d} (QMD line {line_num:5d}): {type(e).__name__}: {e}")
    else:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

print(f"\n{'='*60}")
print(f"Total cells: {len(cells)}  |  Errors: {len(errors)}")

if errors:
    print("\nERROR SUMMARY:")
    for e in errors:
        print(f"\n--- Cell {e['cell']} (QMD line {e['qmd_line']}) ---")
        print(f"{e['error']}: {e['msg']}")
        print("Code snippet:")
        print(e['code'][:400])
