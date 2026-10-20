"""Analysis charts and maps for bioacoustic review data."""

import io
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from IPython.display import display, Image
#
# CONSTANTS
#
FONT_SCALE = 0.95
TITLE_SIZE = 14
SUBTITLE_SIZE = 12
LABEL_SIZE = 10
ANNOTATION_SIZE = 9
ANNOTATION_COLOR = '#555'
DPI = 150

HIST_FIGSIZE = (12, 5)
HIST_PALETTE = 'viridis'

GRID_FIGSIZE = (11, 7)
DIVERSITY_PALETTE_LOW = 'Oranges'
DIVERSITY_PALETTE_HIGH = 'Blues'

sns.set_theme(style='whitegrid', palette='muted', font_scale=FONT_SCALE)


#
# MAIN
#
def species_histogram(df: pd.DataFrame, title: str = 'Detections by species',
                      column: str = 'common_name', max_species: int = 25, figsize=None):
    """Horizontal bar chart of counts by species, sorted most to least."""
    figsize = figsize or HIST_FIGSIZE
    counts = df[column].value_counts().reset_index()
    counts.columns = [column, 'count']
    counts = counts.sort_values('count', ascending=True)[-max_species:]
    fig, ax = plt.subplots(figsize=figsize)
    sns.barplot(data=counts, y=column, x='count', hue=column, ax=ax, orient='h',
                palette=HIST_PALETTE, edgecolor='none', legend=False)
    ax.set_xlabel('Count', fontsize=LABEL_SIZE)
    ax.set_ylabel('')
    ax.set_title(title.upper(), fontsize=TITLE_SIZE)
    ax.tick_params(labelsize=LABEL_SIZE)
    for i, v in enumerate(counts['count']):
        ax.text(v + 0.5, i, str(v), va='center',
                fontsize=ANNOTATION_SIZE, color=ANNOTATION_COLOR)
    sns.despine(left=True)
    _show(fig)


def county_distributions(input_df: pd.DataFrame, output_df: pd.DataFrame,
                         species_column: str = 'common_name',
                         county_column: str = 'county',
                         n: int = 10, figsize=None):
    """2x2 grid: top = most/least diverse counties, bottom = most/least accurate."""
    figsize = figsize or GRID_FIGSIZE

    # ── Diversity: species with count > 1 per county ──────────
    diversity = (
        input_df.groupby(county_column)[species_column]
        .apply(lambda s: (s.value_counts() > 1).sum())
        .rename('n_species')
        .reset_index()
        .sort_values('n_species')
    )
    div_least = diversity.head(n).copy()
    div_most = diversity.tail(n).iloc[::-1].copy()

    totals = input_df.groupby(county_column).size().rename('total')
    for d in [div_least, div_most]:
        d['total'] = d[county_column].map(totals)
        d['label'] = d.apply(
            lambda r: f"{r[county_column]} ({int(r['total'])} detections)", axis=1)

    # ── Accuracy ──────────────────────────────────────────────
    # Ensure time columns are numeric for merging
    output_df_for_merge = output_df.copy()
    output_df_for_merge['start_time'] = pd.to_numeric(output_df_for_merge['start_time'], errors='coerce')
    output_df_for_merge['end_time'] = pd.to_numeric(output_df_for_merge['end_time'], errors='coerce')

    merged = input_df.merge(
        output_df_for_merge[['start_time', 'end_time', 'is_valid']],
        on=['start_time', 'end_time'],
        how='inner',
    )
    merged['correct'] = (merged['is_valid'] == 'yes').astype(int)

    acc_stats = merged.groupby(county_column).agg(
        reviewed=('correct', 'count'),
        correct=('correct', 'sum'),
    )
    acc_stats['accuracy'] = acc_stats['correct'] / acc_stats['reviewed']
    acc_stats = acc_stats[acc_stats['reviewed'] >= 3].sort_values('accuracy').reset_index()

    acc_least = acc_stats.head(n).copy()
    acc_most = acc_stats.tail(n).iloc[::-1].copy()

    for d in [acc_least, acc_most]:
        d['label'] = d.apply(
            lambda r: f"{r[county_column]} ({int(r['reviewed'])} reviewed)", axis=1)

    # ── Plot 2x2 ──────────────────────────────────────────────
    fig, axes = plt.subplots(2, 2, figsize=figsize)

    def _bar(ax, data, x_col, title, palette, fmt, xlim=None):
        sns.barplot(data=data, y='label', x=x_col, hue='label', ax=ax, orient='h',
                    palette=palette, edgecolor='none', legend=False)
        ax.set_xlabel('')
        ax.set_ylabel('')
        ax.set_title(title.upper(), fontsize=SUBTITLE_SIZE)
        ax.tick_params(labelsize=LABEL_SIZE)
        if xlim:
            ax.set_xlim(xlim)
        for i, (_, r) in enumerate(data.iterrows()):
            ax.text(r[x_col] + (xlim[1] * 0.01 if xlim else 0.3), i,
                    fmt(r[x_col]), va='center',
                    fontsize=ANNOTATION_SIZE, color=ANNOTATION_COLOR)
        sns.despine(left=True, ax=ax)

    _bar(axes[0, 0], div_most, 'n_species',
         f'{n} most diverse counties', DIVERSITY_PALETTE_HIGH,
         lambda v: str(int(v)))
    _bar(axes[0, 1], div_least, 'n_species',
         f'{n} least diverse counties', DIVERSITY_PALETTE_LOW,
         lambda v: str(int(v)))
    _bar(axes[1, 0], acc_most, 'accuracy',
         f'{n} most accurate counties',
         sns.color_palette('Greens_r', n_colors=n),
         lambda v: f'{v*100:.0f}%', xlim=(0, 1.05))
    _bar(axes[1, 1], acc_least, 'accuracy',
         f'{n} least accurate counties',
         sns.color_palette('Reds_r', n_colors=n),
         lambda v: f'{v*100:.0f}%', xlim=(0, 1.05))

    axes[1, 0].xaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f'{x*100:.0f}%'))
    axes[1, 1].xaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f'{x*100:.0f}%'))
    axes[1, 0].tick_params(labelsize=LABEL_SIZE)
    axes[1, 1].tick_params(labelsize=LABEL_SIZE)

    _show(fig)


# ── Map ───────────────────────────────────────────────────────

def county_species_map(m, input_df: pd.DataFrame, county_geojson: dict,
                       species_column: str = 'common_name',
                       county_column: str = 'county',
                       region_name_key: str = 'NAME'):
    """Add a choropleth layer to an ipyleaflet Map coloring counties by dominant species."""
    from ipyleaflet import GeoJSON, WidgetControl
    from ipywidgets import Output, HTML

    # Compute dominant species per county
    county_stats = {}
    for county, grp in input_df.groupby(county_column):
        total = len(grp)
        top = grp[species_column].value_counts()
        dominant = top.index[0]
        count = top.iloc[0]
        pct = count / total * 100
        county_stats[county.lower()] = {
            'dominant': dominant, 'count': count, 'total': total, 'pct': pct,
        }

    # Assign colors by species
    all_dominant = sorted(set(s['dominant'] for s in county_stats.values()))
    palette = sns.color_palette('husl', n_colors=len(all_dominant))
    species_colors = {
        sp: '#{:02x}{:02x}{:02x}'.format(int(c[0]*255), int(c[1]*255), int(c[2]*255))
        for sp, c in zip(all_dominant, palette)
    }

    # Build styled GeoJSON
    features = []
    for feat in county_geojson['features']:
        name = feat['properties'].get(region_name_key, '')
        stats = county_stats.get(name.lower())
        if not stats:
            continue
        new_feat = dict(feat)
        new_feat['properties'] = dict(feat['properties'])
        new_feat['properties']['_dominant'] = stats['dominant']
        new_feat['properties']['_count'] = stats['count']
        new_feat['properties']['_total'] = stats['total']
        new_feat['properties']['_pct'] = f"{stats['pct']:.0f}%"
        new_feat['properties']['_color'] = species_colors[stats['dominant']]
        features.append(new_feat)

    styled_geojson = {"type": "FeatureCollection", "features": features}

    def style_fn(feature):
        return {
            'color': '#45475a',
            'weight': 1,
            'fillColor': feature['properties'].get('_color', '#6c7086'),
            'fillOpacity': 0.5,
        }

    layer = GeoJSON(
        data=styled_geojson,
        style_callback=style_fn,
        hover_style={'weight': 3, 'fillOpacity': 0.7},
        name='Species by county',
    )

    info = Output()

    def on_hover(feature, **kwargs):
        props = feature['properties']
        name = props.get(region_name_key, '?')
        dom = props.get('_dominant', '?')
        cnt = props.get('_count', '?')
        tot = props.get('_total', '?')
        pct = props.get('_pct', '?')
        with info:
            info.clear_output()
            print(f"{name}: {dom} — {cnt}/{tot} ({pct})")

    layer.on_hover(on_hover)
    m.add(layer)

    # Legend as a map control (top-right)
    legend_html = (
        '<div style="'
        'background:rgba(255,255,255,0.9);padding:8px 10px;'
        'border-radius:4px;font-size:11px;line-height:1.6;'
        'max-height:300px;overflow-y:auto;'
        'box-shadow:0 1px 4px rgba(0,0,0,0.2);'
        '">'
        '<div style="font-weight:600;margin-bottom:4px;">Dominant species</div>'
    )
    for sp, color in species_colors.items():
        legend_html += (
            f'<div style="display:flex;align-items:center;gap:5px;">'
            f'<span style="display:inline-block;width:10px;height:10px;'
            f'border-radius:2px;background:{color};flex-shrink:0;"></span>'
            f'<span>{sp}</span></div>'
        )
    legend_html += '</div>'

    legend_widget = HTML(value=legend_html)
    legend_control = WidgetControl(widget=legend_widget, position='topright')
    m.add(legend_control)

    return layer, info


def county_accuracy_map(m, input_df: pd.DataFrame, output_df: pd.DataFrame,
                        county_geojson: dict,
                        county_column: str = 'county',
                        region_name_key: str = 'NAME',
                        min_reviews: int = 3,
                        cmap_name: str = 'RdYlGn'):
    """Add a choropleth layer coloring counties by review accuracy (red=low, green=high)."""
    from ipyleaflet import GeoJSON, WidgetControl
    from ipywidgets import Output, HTML
    # import matplotlib.cm as cm
    import matplotlib as mpl
    import matplotlib.colors as mcolors

    # Compute per-county accuracy
    # Ensure time columns are numeric for merging
    output_df_for_merge = output_df.copy()
    output_df_for_merge['start_time'] = pd.to_numeric(output_df_for_merge['start_time'], errors='coerce')
    output_df_for_merge['end_time'] = pd.to_numeric(output_df_for_merge['end_time'], errors='coerce')

    merged = input_df.merge(
        output_df_for_merge[['start_time', 'end_time', 'is_valid']],
        on=['start_time', 'end_time'],
        how='inner',
    )
    merged['correct'] = (merged['is_valid'] == 'yes').astype(int)

    acc_stats = merged.groupby(county_column).agg(
        reviewed=('correct', 'count'),
        correct=('correct', 'sum'),
    )
    acc_stats['accuracy'] = acc_stats['correct'] / acc_stats['reviewed']
    acc_stats = acc_stats[acc_stats['reviewed'] >= min_reviews]

    county_acc = {c.lower(): {'accuracy': row['accuracy'], 'reviewed': int(row['reviewed']),
                              'correct': int(row['correct'])}
                  for c, row in acc_stats.iterrows()}

    # Color mapping
    # colormap = cm.get_cmap(cmap_name)
    colormap = mpl.colormaps[cmap_name]
    norm = mcolors.Normalize(vmin=0, vmax=1)

    def acc_to_hex(acc):
        rgba = colormap(norm(acc))
        return '#{:02x}{:02x}{:02x}'.format(int(rgba[0]*255), int(rgba[1]*255), int(rgba[2]*255))

    # Build styled GeoJSON
    features = []
    for feat in county_geojson['features']:
        name = feat['properties'].get(region_name_key, '')
        stats = county_acc.get(name.lower())
        if not stats:
            continue
        new_feat = dict(feat)
        new_feat['properties'] = dict(feat['properties'])
        new_feat['properties']['_accuracy'] = float(stats['accuracy'])
        new_feat['properties']['_reviewed'] = int(stats['reviewed'])
        new_feat['properties']['_correct'] = int(stats['correct'])
        new_feat['properties']['_color'] = acc_to_hex(stats['accuracy'])
        features.append(new_feat)

    styled_geojson = {"type": "FeatureCollection", "features": features}

    def style_fn(feature):
        return {
            'color': '#45475a',
            'weight': 1,
            'fillColor': feature['properties'].get('_color', '#6c7086'),
            'fillOpacity': 0.6,
        }

    layer = GeoJSON(
        data=styled_geojson,
        style_callback=style_fn,
        hover_style={'weight': 3, 'fillOpacity': 0.8},
        name='Accuracy by county',
    )

    info = Output()

    def on_hover(feature, **kwargs):
        props = feature['properties']
        name = props.get(region_name_key, '?')
        acc = props.get('_accuracy', 0)
        rev = props.get('_reviewed', 0)
        cor = props.get('_correct', 0)
        with info:
            info.clear_output()
            print(f"{name}: {acc*100:.0f}% accuracy ({cor}/{rev} correct)")

    layer.on_hover(on_hover)
    m.add(layer)

    # Gradient legend — 10% steps from lowest bucket to 100%
    min_acc = min(s['accuracy'] for s in county_acc.values()) if county_acc else 0
    start_pct = int(min_acc * 10) * 10  # round down to nearest 10%
    gradient_items = ''
    for pct in range(start_pct, 101, 10):
        v = pct / 100
        c = acc_to_hex(v)
        gradient_items += (
            f'<div style="display:flex;align-items:center;gap:5px;">'
            f'<span style="display:inline-block;width:10px;height:10px;'
            f'border-radius:2px;background:{c};flex-shrink:0;"></span>'
            f'<span>{pct}%</span></div>'
        )

    legend_html = (
        '<div style="'
        'background:rgba(255,255,255,0.9);padding:8px 10px;'
        'border-radius:4px;font-size:11px;line-height:1.6;'
        'box-shadow:0 1px 4px rgba(0,0,0,0.2);'
        '">'
        '<div style="font-weight:600;margin-bottom:4px;">Accuracy</div>'
        f'{gradient_items}'
        '</div>'
    )

    legend_widget = HTML(value=legend_html)
    legend_control = WidgetControl(widget=legend_widget, position='topright')
    m.add(legend_control)

    return layer, info


#
# INTERNAL
#
def _show(fig):
    """Display a matplotlib figure."""
    fig.tight_layout()
    plt.show()