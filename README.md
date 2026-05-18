# Jupyter Bioacoustic Demo

Interactive demo notebooks showcasing the [jupyter-bioacoustic](https://github.com/SchmidtDSE/jupyter_bioacoustic) JupyterLab extension for annotating and reviewing bioacoustic audio clips.

![BioacousticAnnotator Interface](assets/app-review.png)

## Overview

This repository contains demonstration notebooks that show how to use `BioacousticAnnotator` for:

- **Annotation**: Assign species labels and mark time/frequency regions in audio clips
- **Review**: Validate AI model predictions with human expertise
- **Geo-Analysis**: Combine geographic data analysis with audio review workflows

## Features Demonstrated

- 📊 **Interactive Tables** — Browse, filter, and sort audio detections
- 🎵 **Spectrogram Player** — Visualize and play audio with zoom/pan controls
- 📝 **Configurable Forms** — YAML-driven annotation and review interfaces
- 🎯 **Annotation Tools** — Bounding boxes, time markers, and multibox selections
- 🗺️ **Geographic Analysis** — Select regions on interactive maps for focused review
- 📈 **Integrated Analysis** — Species distributions, accuracy metrics, and visualizations

## Quick Start

### Installation

```bash
# Install jupyter-bioacoustic
pip install jupyter-bioacoustic

# For demo notebooks with analysis tools
pip install ipyleaflet shapely seaborn requests
```

### Run the Demos

```bash
# Clone this repository
git clone https://github.com/your-org/jupyter-bioacoustic-demo.git
cd jupyter-bioacoustic-demo

# Start JupyterLab
jupyter lab

# Open simple-example.ipynb or geo-analysis-example.ipynb
```

## Demo Notebooks

### 1. Simple Example (`simple-example.ipynb`)

Basic workflows for annotation and review:

```python
from jupyter_bioacoustic import BioacousticAnnotator

# Annotation workflow
ba_annotate = BioacousticAnnotator(
    data_path='data/annotate-data.csv',
    config='config/annotate-simple.yaml',
    output='outputs/annotate-output.csv'
)
ba_annotate.open()

# Review workflow
ba_review = BioacousticAnnotator(
    data='data/review-data.csv',
    config='config/review-simple.yaml',
    output='outputs/review-output.csv'
)
ba_review.open()
```

### 2. Geographic Analysis (`geo-analysis-example.ipynb`)

Advanced workflow combining map-based data selection with audio review and analysis:

- Select regions of interest on an interactive map
- Review audio from selected areas
- Analyze species distributions and model accuracy
- Generate county-level visualizations

## Configuration

The demo uses YAML configuration files to define form layouts. The new `dynamic_forms` feature allows conditional form sections:

```yaml
# config/review-simple.yaml
form_config:
  - select:
      label: Is Valid
      column: is_valid
      items:
        - value: 'yes'
        - value: 'no'
          form: correction_form  # Triggers dynamic form

dynamic_forms:
  correction_form:
    - select:
        label: Corrected Species
        column: verified_common_name
        items:
          path: data/categories.csv
          value: common_name
```

## Data Sources

The demo supports multiple data sources:

- **Local files**: CSV, Parquet, JSONL
- **Remote files**: S3, GCS, HTTPS URLs
- **Databases**: SQL queries via DuckDB
- **APIs**: REST endpoints returning JSON

Audio can be loaded from:
- Single file for all clips
- Per-row file paths/URLs
- S3/GCS URIs with partial downloads

## Project Structure

```
jupyter-bioacoustic-demo/
├── simple-example.ipynb       # Basic annotation/review workflows
├── geo-analysis-example.ipynb # Geographic analysis with maps
├── config/                    # YAML configuration files
│   ├── annotate-simple.yaml
│   ├── review-simple.yaml
│   └── dev-config-geo-review.yaml
├── data/                      # Sample datasets
│   ├── annotate-data.csv
│   ├── review-data.csv
│   ├── dev-review.csv
│   └── categories-small.csv
├── audio/                     # Sample audio files
├── tools/                     # Analysis utilities
│   ├── MapHandler.py         # Interactive map selection
│   └── analysis.py           # Visualization functions
├── outputs/                   # Generated annotations
└── assets/                    # Images for documentation
```

## Key Differences from Previous Versions

This demo is updated for the latest `jupyter-bioacoustic` (v0.5.5+):

- **Class renamed**: `JupyterAudio` → `BioacousticAnnotator`
- **New form system**: `is_valid_form` → `dynamic_forms` for flexible conditional forms
- **Enhanced annotations**: New `spectrogram_annotations` field type
- **Better configuration**: Cleaner YAML structure with top-level parameters

## Documentation

- **Full Documentation**: [jupyter-bioacoustic Wiki](https://github.com/SchmidtDSE/jupyter_bioacoustic/wiki)
- **API Reference**: [BioacousticAnnotator API](https://github.com/SchmidtDSE/jupyter_bioacoustic/wiki/API-Reference)
- **Configuration Guide**: [All Parameters](https://github.com/SchmidtDSE/jupyter_bioacoustic/wiki/Configuration)
- **Form Builder**: [Configurable Forms](https://github.com/SchmidtDSE/jupyter_bioacoustic/wiki/Configurable-Forms)

## Requirements

- Python ≥ 3.9
- JupyterLab ≥ 4.0
- jupyter-bioacoustic ≥ 0.5.5
- numpy, pandas, matplotlib
- soundfile, pydub
- boto3 (for S3 support)

Optional for demos:
- ipyleaflet (geographic maps)
- shapely (polygon selection)
- seaborn (visualizations)
- requests (fetching county data)
- duckdb (SQL queries)

## Development

To modify or extend the demos:

```bash
# Install in development mode
pip install -e .

# Install additional dependencies
pip install ipyleaflet shapely seaborn requests duckdb
```

## Troubleshooting

### Map Widget Not Displaying

If you see "Error displaying widget" when trying to load the map:

1. **Using pixi** (recommended):
```bash
# Clean install
pixi run install-extensions
pixi run setup

# Restart JupyterLab
pixi run lab
```

2. **Using pip**:
```bash
# Ensure ipywidgets and ipyleaflet are properly installed
pip install --upgrade ipywidgets ipyleaflet
jupyter labextension list  # Check if jupyter-leaflet is listed

# If not listed, you may need to rebuild
jupyter lab build
```

3. **Browser issues**:
- Try refreshing the browser (Ctrl+Shift+R or Cmd+Shift+R)
- Clear browser cache
- Try a different browser

4. **Kernel issues**:
- Restart the kernel (Kernel → Restart Kernel)
- Reload the notebook

### Audio Not Loading

- Check that audio files exist in the `audio/` directory
- For S3 audio, ensure AWS credentials are configured
- Verify the audio path in the configuration matches your files

## Support

- **Issues**: [GitHub Issues](https://github.com/SchmidtDSE/jupyter_bioacoustic/issues)
- **Discussions**: [GitHub Discussions](https://github.com/SchmidtDSE/jupyter_bioacoustic/discussions)

## License

This demo repository is provided under the BSD 3-Clause License. See LICENSE file for details.

## Acknowledgments

Developed by the [Eric and Wendy Schmidt Center for Data Science and Environment](https://dse.berkeley.edu) at UC Berkeley.

The jupyter-bioacoustic tool supports bioacoustic research by bridging the gap between AI model outputs and human validation, keeping the entire workflow within the Jupyter ecosystem.