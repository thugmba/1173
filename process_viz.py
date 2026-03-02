#!/usr/bin/env python3
"""
process_viz.py
Add expected output after Python code blocks in VIZ.md (Main Contents sections only).
Also update numbered sample filenames to YourName_ convention.
"""

import re
import sys
import io
import os
import types
import traceback
import copy

# ===========================================================
# CHART TYPE DETECTION
# ===========================================================

def chart_type_from_code(code):
    if 'sns.heatmap(' in code:
        return 'Heatmap'
    if 'sns.pairplot(' in code:
        return 'Pair plot'
    if 'sns.clustermap(' in code:
        return 'Cluster heatmap'
    if 'sns.jointplot(' in code:
        return 'Joint plot'
    if 'sns.lmplot(' in code:
        return 'Regression plot'
    if 'sns.violinplot(' in code:
        return 'Violin plot'
    if 'sns.boxplot(' in code:
        return 'Box plot'
    if 'sns.barplot(' in code:
        return 'Bar plot'
    if 'sns.lineplot(' in code:
        return 'Line plot'
    if 'sns.scatterplot(' in code:
        return 'Scatter plot'
    if 'sns.histplot(' in code or 'sns.distplot(' in code or 'sns.kdeplot(' in code:
        return 'Distribution plot'
    if 'sns.countplot(' in code:
        return 'Count plot'
    if 'sns.stripplot(' in code or 'sns.swarmplot(' in code:
        return 'Strip plot'
    if 'sns.regplot(' in code:
        return 'Regression scatter plot'
    if 'sns.FacetGrid(' in code or 'sns.catplot(' in code:
        return 'Faceted plot'
    if 'px.sunburst(' in code:
        return 'Interactive sunburst chart'
    if 'px.treemap(' in code:
        return 'Interactive treemap'
    if 'px.pie(' in code:
        return 'Interactive pie chart'
    if 'px.bar(' in code:
        return 'Interactive bar chart'
    if 'px.line(' in code:
        return 'Interactive line chart'
    if 'px.scatter(' in code:
        return 'Interactive scatter plot'
    if 'px.box(' in code:
        return 'Interactive box plot'
    if 'px.histogram(' in code:
        return 'Interactive histogram'
    if 'px.area(' in code:
        return 'Interactive area chart'
    if 'px.funnel(' in code:
        return 'Interactive funnel chart'
    if 'px.scatter_3d(' in code:
        return 'Interactive 3D scatter plot'
    if 'go.Figure(' in code or 'go.Bar(' in code or 'go.Scatter(' in code:
        return 'Interactive Plotly chart'
    if 'ax.pie(' in code or 'plt.pie(' in code:
        return 'Pie chart'
    if 'ax.fill_between(' in code:
        return 'Area chart'
    if 'ax.barh(' in code:
        return 'Horizontal bar chart'
    if 'ax.bar(' in code or 'plt.bar(' in code:
        return 'Bar chart'
    if 'ax.hist(' in code or 'plt.hist(' in code:
        return 'Histogram'
    if 'ax.boxplot(' in code:
        return 'Box plot'
    if 'ax.scatter(' in code or 'plt.scatter(' in code:
        return 'Scatter plot'
    if 'ax.plot(' in code or 'plt.plot(' in code:
        return 'Line chart'
    if 'plt.subplots(' in code or 'plt.figure(' in code:
        return 'Chart'
    return 'Chart'


def extract_chart_meta(code):
    title = ''
    xlabel = ''
    ylabel = ''
    suptitle = ''

    m = re.search(r'set_title\(["\']([^"\']+)["\']', code)
    if m:
        title = m.group(1)

    m = re.search(r'suptitle\(["\']([^"\']+)["\']', code)
    if m:
        suptitle = m.group(1)

    m = re.search(r'set_xlabel\(["\']([^"\']+)["\']', code)
    if m:
        xlabel = m.group(1)

    m = re.search(r'set_ylabel\(["\']([^"\']+)["\']', code)
    if m:
        ylabel = m.group(1)

    # Plotly title
    if not title:
        m = re.search(r'title\s*=\s*["\']([^"\']+)["\']', code)
        if m:
            title = m.group(1)

    # Plotly axis labels
    if not xlabel:
        m = re.search(r'x\s*=\s*["\']([^"\']+)["\']', code)
        if m:
            xlabel = m.group(1)
    if not ylabel:
        m = re.search(r'y\s*=\s*["\']([^"\']+)["\']', code)
        if m:
            ylabel = m.group(1)

    return title or suptitle, xlabel, ylabel


def count_subplots(code):
    m = re.search(r'plt\.subplots\((\d+)\s*,\s*(\d+)', code)
    if m:
        return int(m.group(1)), int(m.group(2))
    return 1, 1


def generate_chart_description(code):
    ctype = chart_type_from_code(code)
    title, xlabel, ylabel = extract_chart_meta(code)
    nrows, ncols = count_subplots(code)

    parts = []
    if title:
        parts.append(f'"{title}"')
    if nrows * ncols > 1:
        parts.append(f'{nrows}×{ncols} subplot grid')
    if xlabel:
        parts.append(f'x: {xlabel}')
    if ylabel:
        parts.append(f'y: {ylabel}')

    desc = f'*[{ctype}'
    if parts:
        desc += ': ' + ', '.join(parts)
    desc += ']*'
    return desc


# ===========================================================
# MOCK CHART CLASSES (attr-safe)
# ===========================================================

class Noop:
    """Silently absorbs any attribute access or call."""
    def __call__(self, *a, **k):
        return self
    def __getattr__(self, name):
        return self
    def __iter__(self):
        return iter([])
    def __len__(self):
        return 0
    def __bool__(self):
        return True
    def __enter__(self):
        return self
    def __exit__(self, *a):
        pass
    def show(self):
        pass
    def write_html(self, *a, **k):
        pass
    def write_image(self, *a, **k):
        pass
    def update_layout(self, *a, **k):
        return self
    def add_trace(self, *a, **k):
        return self


class MockAxes(Noop):
    def twinx(self):
        return MockAxes()
    def twiny(self):
        return MockAxes()


class MockFig(Noop):
    def add_subplot(self, *a, **k):
        return MockAxes()
    def add_axes(self, *a, **k):
        return MockAxes()


_MOCK_PLT = None
_MOCK_SNS = None
_MOCK_PX = None
_MOCK_GO = None


def build_mock_plt():
    m = types.ModuleType('matplotlib.pyplot')

    def subplots(nrows=1, ncols=1, **k):
        if nrows == 1 and ncols == 1:
            return MockFig(), MockAxes()
        elif nrows == 1:
            return MockFig(), [MockAxes() for _ in range(ncols)]
        elif ncols == 1:
            return MockFig(), [MockAxes() for _ in range(nrows)]
        else:
            return MockFig(), [[MockAxes() for _ in range(ncols)] for _ in range(nrows)]

    m.subplots = subplots
    m.figure = lambda *a, **k: MockFig()
    m.show = lambda: None
    m.savefig = lambda *a, **k: None
    m.tight_layout = lambda *a, **k: None
    m.subplots_adjust = lambda *a, **k: None
    m.suptitle = lambda *a, **k: None
    m.plot = lambda *a, **k: []
    m.scatter = lambda *a, **k: []
    m.bar = lambda *a, **k: []
    m.barh = lambda *a, **k: []
    m.hist = lambda *a, **k: ([], [], [])
    m.pie = lambda *a, **k: ([], [])
    m.grid = lambda *a, **k: None
    m.legend = lambda *a, **k: None
    m.title = lambda *a, **k: None
    m.xlabel = lambda *a, **k: None
    m.ylabel = lambda *a, **k: None
    m.xticks = lambda *a, **k: None
    m.yticks = lambda *a, **k: None
    m.tick_params = lambda *a, **k: None
    m.colorbar = lambda *a, **k: Noop()
    m.annotate = lambda *a, **k: None
    m.text = lambda *a, **k: None
    m.axhline = lambda *a, **k: None
    m.axvline = lambda *a, **k: None
    m.fill_between = lambda *a, **k: None
    m.rcParams = {}

    class _style:
        @staticmethod
        def use(*a, **k): pass
        available = []
    m.style = _style

    class _cm:
        Blues = 'Blues'
        Reds = 'Reds'
        YlOrRd = 'YlOrRd'
        RdYlGn = 'RdYlGn'
        coolwarm = 'coolwarm'
        viridis = 'viridis'
        plasma = 'plasma'
        RdBu = 'RdBu'
        def get_cmap(self, *a, **k): return Noop()
    m.cm = _cm()

    class _colors:
        pass
    m.colors = _colors()

    return m


def build_mock_mpl():
    mpl = types.ModuleType('matplotlib')
    mpl.pyplot = build_mock_plt()
    mpl.rcParams = {}
    mpl.cm = mpl.pyplot.cm
    mpl.colors = mpl.pyplot.colors

    patches = types.ModuleType('matplotlib.patches')
    patches.FancyArrowPatch = Noop
    patches.Rectangle = Noop
    patches.Circle = Noop
    patches.Arrow = Noop
    mpl.patches = patches

    gridspec = types.ModuleType('matplotlib.gridspec')
    gridspec.GridSpec = Noop
    gridspec.GridSpecFromSubplotSpec = Noop
    mpl.gridspec = gridspec

    ticker = types.ModuleType('matplotlib.ticker')
    ticker.FuncFormatter = Noop
    ticker.PercentFormatter = Noop
    ticker.MultipleLocator = Noop
    mpl.ticker = ticker

    lines = types.ModuleType('matplotlib.lines')
    lines.Line2D = Noop
    mpl.lines = lines

    return mpl


def build_mock_sns():
    m = types.ModuleType('seaborn')
    for fn in [
        'set_style', 'set_theme', 'set_palette', 'set',
        'lineplot', 'barplot', 'histplot', 'distplot', 'kdeplot',
        'heatmap', 'pairplot', 'boxplot', 'violinplot', 'scatterplot',
        'countplot', 'stripplot', 'swarmplot', 'regplot', 'residplot',
        'lmplot', 'jointplot', 'clustermap', 'catplot', 'FacetGrid',
        'pointplot', 'rugplot', 'ecdfplot',
    ]:
        setattr(m, fn, lambda *a, **k: Noop())
    m.color_palette = lambda *a, **k: ['#1f77b4'] * 10
    m.axes_style = lambda *a, **k: {}
    return m


def build_mock_plotly():
    px = types.ModuleType('plotly.express')
    for fn in [
        'line', 'bar', 'scatter', 'pie', 'box', 'histogram',
        'area', 'funnel', 'sunburst', 'treemap', 'choropleth',
        'scatter_3d', 'scatter_geo', 'density_heatmap', 'strip',
        'violin', 'ecdf', 'imshow', 'parallel_coordinates',
        'parallel_categories',
    ]:
        setattr(px, fn, lambda *a, **k: Noop())
    px.colors = Noop()

    go = types.ModuleType('plotly.graph_objects')
    for cls_name in [
        'Figure', 'Bar', 'Scatter', 'Pie', 'Line', 'Histogram',
        'Box', 'Heatmap', 'Waterfall', 'Indicator', 'Candlestick',
        'Scatter3d', 'Surface', 'Funnel', 'Sankey', 'Sunburst',
        'Treemap', 'Layout', 'XAxis', 'YAxis',
    ]:
        setattr(go, cls_name, Noop)

    subplots_mod = types.ModuleType('plotly.subplots')
    subplots_mod.make_subplots = lambda *a, **k: Noop()

    plotly_mod = types.ModuleType('plotly')
    plotly_mod.express = px
    plotly_mod.graph_objects = go
    plotly_mod.subplots = subplots_mod

    return plotly_mod, px, go, subplots_mod


def build_mock_dash():
    dash = types.ModuleType('dash')
    dash.Dash = Noop
    dash.html = types.ModuleType('dash.html')
    dash.dcc = types.ModuleType('dash.dcc')
    dash.html.Div = Noop
    dash.html.H1 = Noop
    dash.dcc.Graph = Noop
    dash.dcc.Dropdown = Noop
    dash.Input = Noop
    dash.Output = Noop
    dash.callback = lambda *a, **k: (lambda f: f)
    return dash


def install_mocks():
    mpl = build_mock_mpl()
    plt = mpl.pyplot
    sns = build_mock_sns()
    plotly_mod, px, go, subplots_mod = build_mock_plotly()
    dash = build_mock_dash()

    sys.modules['matplotlib'] = mpl
    sys.modules['matplotlib.pyplot'] = plt
    sys.modules['matplotlib.patches'] = mpl.patches
    sys.modules['matplotlib.gridspec'] = mpl.gridspec
    sys.modules['matplotlib.ticker'] = mpl.ticker
    sys.modules['matplotlib.lines'] = mpl.lines
    sys.modules['matplotlib.cm'] = types.ModuleType('matplotlib.cm')
    sys.modules['matplotlib.colors'] = types.ModuleType('matplotlib.colors')
    sys.modules['seaborn'] = sns
    sys.modules['plotly'] = plotly_mod
    sys.modules['plotly.express'] = px
    sys.modules['plotly.graph_objects'] = go
    sys.modules['plotly.subplots'] = subplots_mod
    sys.modules['dash'] = dash
    sys.modules['dash.html'] = dash.html
    sys.modules['dash.dcc'] = dash.dcc

    return {'plt': plt, 'sns': sns, 'px': px, 'go': go}


# ===========================================================
# CODE EXECUTION
# ===========================================================

def make_namespace(base_bindings):
    import builtins
    ns = {'__builtins__': vars(builtins)}
    ns.update(base_bindings)
    return ns


def execute_code(code, namespace):
    """Execute code, capturing stdout. Returns (output_str, error_str)."""
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        exec(compile(code, '<block>', 'exec'), namespace)
        out = sys.stdout.getvalue().rstrip()
        sys.stdout = old_stdout
        return out, None
    except Exception as e:
        out = sys.stdout.getvalue().rstrip()
        sys.stdout = old_stdout
        return out, str(e)


def is_viz_code(code):
    viz_kw = [
        'plt.show()', 'plt.savefig', 'plt.plot(', 'plt.scatter(', 'plt.bar(',
        'plt.figure(', 'plt.subplots(', 'plt.hist(', 'plt.pie(',
        'ax.plot(', 'ax.scatter(', 'ax.bar(', 'ax.barh(', 'ax.hist(',
        'ax.pie(', 'ax.boxplot(', 'ax.fill_between(', 'ax.set_title(',
        'sns.', 'px.line(', 'px.bar(', 'px.scatter(', 'px.pie(',
        'px.box(', 'px.histogram(', 'px.sunburst(', 'px.treemap(',
        'px.area(', 'px.funnel(', 'px.scatter_3d(',
        'go.Figure(', 'go.Bar(', 'go.Scatter(', 'fig.show()',
        'fig.write_html(', 'fig.update_layout(', 'make_subplots(',
    ]
    return any(kw in code for kw in viz_kw)


def has_print_output(code):
    return 'print(' in code


def is_notebook_expression(code):
    """Check if the last meaningful line is a standalone expression (notebook/REPL style).
    These produce visible output in Jupyter but not in scripts.
    """
    lines = [l.rstrip() for l in code.split('\n')
             if l.strip() and not l.strip().startswith('#')]
    if not lines:
        return False
    last = lines[-1].strip()
    # Assignment lines, control flow, imports, defs → not an expression
    skip_prefixes = ('import ', 'from ', 'def ', 'class ', 'if ', 'elif ', 'else:',
                     'for ', 'while ', 'try:', 'except', 'finally:', 'return ',
                     'raise ', 'with ', 'pass', 'break', 'continue', '@')
    if any(last.startswith(p) for p in skip_prefixes):
        return False
    # Assignment (contains = but not ==, !=, <=, >=)
    import re
    if re.search(r'(?<![=!<>])=(?!=)', last.split('#')[0]):
        return False
    # Must be a call or attribute access
    expr_patterns = [
        r'^\w[\w.]*\(',        # function/method call
        r'^\w[\w.]*$',         # variable reference
        r'^\w[\w.]*\[',        # subscript
    ]
    return any(re.match(p, last) for p in expr_patterns)


def execute_notebook_style(code, namespace):
    """Execute code; for last expression-line wrap in print() to capture output."""
    import re
    lines = code.split('\n')
    non_blank = [(i, l) for i, l in enumerate(lines) if l.strip() and not l.strip().startswith('#')]
    if not non_blank:
        return None, None

    last_i, last_line = non_blank[-1]
    last = last_line.strip()

    # Check if last line is a dataframe/series exploration call
    explore_patterns = [
        r'\bdf\b.*\.(head|tail|info|describe|sample|value_counts|groupby|sort_values|nunique|isnull)\(',
        r'\b\w+\.(head|tail|info|describe|value_counts)\(',
        r'\bdf\b\.(shape|columns|dtypes|index)',
        r'\b\w+\.(shape|columns|dtypes)',
    ]
    is_explore = any(re.search(p, last) for p in explore_patterns)

    if not is_explore:
        return None, None

    # Strip inline comment from last_line before wrapping
    import re as _re
    last_code_only = _re.split(r'\s*#', last_line.lstrip(), maxsplit=1)[0].rstrip()
    indent = len(last_line) - len(last_line.lstrip())

    # For .info() — it prints directly; others need print()
    if '.info(' in last_code_only:
        out, err = execute_code(code, namespace)
        return out if out else None, err
    else:
        modified_lines = list(lines)
        modified_lines[last_i] = ' ' * indent + 'print(' + last_code_only.strip() + ')'
        modified_code = '\n'.join(modified_lines)
        out, err = execute_code(modified_code, namespace)
        return out if out else None, err


def already_has_output(lines, close_idx):
    """Check if the lines after the closing ``` already contain output."""
    j = close_idx + 1
    while j < len(lines) and not lines[j].strip():
        j += 1
    if j >= len(lines):
        return False
    nxt = lines[j].strip()
    return (
        nxt.startswith('**Output') or
        nxt.startswith('**DataFrame Output') or
        ('Output:' in nxt and nxt.startswith('**')) or
        # Already a raw code block immediately following (i.e., output table)
        (nxt.startswith('```') and j == close_idx + 1)
    )


# ===========================================================
# FILENAME UPDATES
# ===========================================================

def update_sample_filenames(content):
    """Rename numbered sample files in Main Contents to YourName_ convention."""
    replacements = {
        '`01_First_Program_Hello.py`': '`YourName_Hello.py`',
        '`02_Package_Test_Verification.py`': '`YourName_Verification.py`',
        # Add more if discovered
    }
    for old, new in replacements.items():
        content = content.replace(old, new)
    # Also update references inside code comments / strings
    content = content.replace(
        "01_First_Program_Hello.py",
        "YourName_Hello.py"
    )
    content = content.replace(
        "02_Package_Test_Verification.py",
        "YourName_Verification.py"
    )
    return content


# ===========================================================
# MAIN PROCESSING
# ===========================================================

def process_file(input_path, output_path):
    print(f"Reading {input_path} ...")
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Step 1: Update filenames
    content = update_sample_filenames(content)

    # Step 2: Install mocks and build base namespace
    base_bindings = install_mocks()

    lines = content.split('\n')
    result = []
    i = 0

    in_main_contents = False
    # Cumulative namespace resets at each section boundary
    section_ns = make_namespace(base_bindings)
    added = 0

    while i < len(lines):
        line = lines[i]

        # Track section context
        if '### Main Contents' in line:
            in_main_contents = True
            section_ns = make_namespace(base_bindings)  # fresh per section
        elif line.startswith('### Lab Session'):
            in_main_contents = False
        # Also reset at new ## Section headings (new topic)
        elif line.startswith('## Section ') or line.startswith('# Module '):
            section_ns = make_namespace(base_bindings)

        result.append(line)

        # Detect start of Python code block
        if line.strip() == '```python':
            # Collect code lines
            code_lines = []
            j = i + 1
            while j < len(lines) and lines[j].strip() != '```':
                code_lines.append(lines[j])
                result.append(lines[j])
                j += 1

            # Append closing ```
            if j < len(lines):
                result.append(lines[j])  # '```'

            code = '\n'.join(code_lines)
            annotate = in_main_contents and not already_has_output(lines, j)

            if annotate:
                if is_viz_code(code):
                    execute_code(code, section_ns)  # update namespace
                    desc = generate_chart_description(code)
                    result.append('')
                    result.append('**Output:**')
                    result.append('')
                    result.append(desc)
                    added += 1

                elif has_print_output(code):
                    out, err = execute_code(code, section_ns)
                    if out:
                        result.append('')
                        result.append('**Output:**')
                        result.append('```')
                        result.extend(out.split('\n'))
                        result.append('```')
                        added += 1

                else:
                    # Check for notebook-style expression (df.head(), df.info(), etc.)
                    nb_out, nb_err = execute_notebook_style(code, section_ns)
                    if nb_out:
                        result.append('')
                        result.append('**Output:**')
                        result.append('```')
                        result.extend(nb_out.split('\n'))
                        result.append('```')
                        added += 1
                    else:
                        execute_code(code, section_ns)
            else:
                # Already annotated — still execute to keep namespace current
                execute_code(code, section_ns)

            i = j + 1
            continue

        i += 1

    modified = '\n'.join(result)

    print(f"Writing {output_path} ...")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(modified)

    print(f"Done. Added output annotations to {added} code blocks.")


if __name__ == '__main__':
    base = r'e:\Data\Gdrive\Work\Teaching\Courses\1173_Data_Visualization\1173\Lectures'
    input_file = os.path.join(base, 'VIZ.md')
    output_file = os.path.join(base, 'VIZ.md')
    process_file(input_file, output_file)
