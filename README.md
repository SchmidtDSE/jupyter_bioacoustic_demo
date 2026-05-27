# Jupyter Bioacoustic Demo

Interactive demo notebooks for the [jupyter-bioacoustic](https://github.com/SchmidtDSE/jupyter_bioacoustic) JupyterLab extension.

- **Site**: [schmidtdse.github.io/jupyter_bioacoustic](https://schmidtdse.github.io/jupyter_bioacoustic/)
- **Wiki**: [GitHub Wiki](https://github.com/SchmidtDSE/jupyter_bioacoustic/wiki)

![BioacousticAnnotator Interface](assets/demo-geo.png)

## Overview

These notebooks demonstrate how to use `BioacousticAnnotator` for:

- **Annotation**: Assign species labels and mark time/frequency regions in audio clips
- **Review**: Validate AI model predictions with human expertise
- **Geo-Analysis**: Combine geographic data selection with audio review and downstream analysis

## Quick Start

### Using Pixi (recommended)

[Pixi](https://pixi.sh) manages all dependencies automatically from the `pyproject.toml`:

```bash
git clone https://github.com/SchmidtDSE/jupyter_bioacoustic_demo.git
cd jupyter_bioacoustic_demo
pixi run jba lab
```

This installs `jupyter-bioacoustic`, `ipyleaflet`, `shapely`, `seaborn`, and all other dependencies, then launches JupyterLab with the required `iopub_data_rate_limit` setting.

> Spectrograms are sent as base64 images over Jupyter's IOPub channel, which can exceed the default rate limit. The `iopub_data_rate_limit` flag (or `pixi run lab`) prevents throttling.

## Demo Notebooks

### Simple Example (`simple-example.ipynb`)

Two workflows in one notebook:

**Annotation** &mdash; uses a project file to load data, config, and output paths together:

```python
ba = BioacousticAnnotator(
    project='annotator_config/projects/simple_annotator.yaml',
    annotator_name='brookie',
    annotate_date=20260515
)
ba.open()
```

**Review** &mdash; loads parameters directly:

```python
ba = BioacousticAnnotator(
    data='data/review-data.csv',
    config='config/review-simple.yaml',
    output='outputs/review-output.csv',
    reviewer_name='brookie',
    review_date=20260414
)
ba.open()
```

### Geographic Analysis (`geo-analysis-example.ipynb`)

End-to-end workflow that stays inside the Jupyter ecosystem:

1. Load model predictions and county boundaries
2. Select regions on an interactive map (click counties or draw polygons)
3. Review selected clips with `BioacousticAnnotator`
4. Analyze species distributions and model accuracy
5. Generate county-level choropleth maps

## Configuration

The demo uses two configuration patterns:

**Project files** combine data, config, and output into a single reference:

```yaml
# annotator_config/projects/simple_annotator.yaml
project_name: Simple Annotator
config: annotator_config/config/simple_annotator.yaml
data:
  path: data/annotate-data.csv
```

**Config files** define audio, display, and form parameters:

```yaml
# config/review-simple.yaml
audio: audio_path
ident_column: common_name
display_columns: ["confidence", "county"]

form_config:
    select:
        label: Is Valid
        column: is_valid
        items:
            - label: 'yes'
              value: 'yes'
            - label: 'no'
              value: 'no'
              form: correction_form
    dynamic_forms:
        correction_form:
            - select:
                  label: verified name
                  column: verified_common_name
                  items:
                      path: data/categories-small.csv
                      value: common_name
    submission_buttons:
        submit:
            label: Verify
```

See the [Configuration wiki](https://github.com/SchmidtDSE/jupyter_bioacoustic/wiki/Configuration) and [Configurable Forms wiki](https://github.com/SchmidtDSE/jupyter_bioacoustic/wiki/Configurable-Forms) for all available parameters.

## Project Structure

```
jupyter_bioacoustic_demo/
├── simple-example.ipynb              # Annotation and review workflows
├── geo-analysis-example.ipynb        # Geographic analysis with maps
├── annotator_config/                 # Config builder layout
│   ├── config/                       #   annotator configs
│   ├── forms/                        #   form configs
│   └── projects/                     #   project files
├── config/                           # Standalone config files
│   ├── annotate-simple.yaml
│   ├── review-simple.yaml
│   └── forms/                        #   form configs for standalone configs
├── data/                             # Sample datasets and category lists
├── audio/                            # Sample FLAC audio files
├── tools/                            # Analysis utilities
│   ├── map_handler.py                #   Interactive map selection
│   └── analysis.py                   #   Visualization and stats functions
├── scripts/                          # Data generation scripts
├── outputs/                          # Generated annotation CSVs
├── assets/                           # Documentation images
├── pyproject.toml                    # Pixi config and dependencies
└── requirements.txt                  # pip fallback dependencies
```

## Troubleshooting

### Audio Not Loading

- Verify audio files exist in `audio/` (or that S3 URIs are accessible)
- For S3 audio, ensure AWS credentials are configured
- Check that the `audio` field in your config matches the actual file paths

### Map Widget Not Displaying

- **Pixi**: dependencies are handled automatically. Restart with `pixi run lab`
- **pip**: ensure `ipywidgets` and `ipyleaflet` are installed, then restart JupyterLab
- Try a hard refresh (`Ctrl+Shift+R` / `Cmd+Shift+R`)

## Documentation

- [Full Documentation (MyST)](https://schmidtdse.github.io/jupyter_bioacoustic/)
- [GitHub Wiki](https://github.com/SchmidtDSE/jupyter_bioacoustic/wiki)
- [API Reference](https://github.com/SchmidtDSE/jupyter_bioacoustic/wiki/API-Reference)
- [Configuration](https://github.com/SchmidtDSE/jupyter_bioacoustic/wiki/Configuration)
- [Configurable Forms](https://github.com/SchmidtDSE/jupyter_bioacoustic/wiki/Configurable-Forms)

## License

BSD 3-Clause. See LICENSE for details.

Developed by the [Eric and Wendy Schmidt Center for Data Science and Environment](https://dse.berkeley.edu) at UC Berkeley.
