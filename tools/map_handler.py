"""MapHandler — interactive point selection on an ipyleaflet map."""

import pandas as pd
from IPython.display import display
from ipyleaflet import GeoJSON, DrawControl


class MapHandler:
    """Adds points, region click, and draw tools to an ipyleaflet Map.

    Usage::

        from ipyleaflet import Map
        from tools import MapHandler

        m = Map(center=(37.5, -119.5), zoom=6, layout={'height': '600px'})
        handler = MapHandler(df, region_data=ca_counties, region_column='county')
        handler.add_to(m)
        display(m, handler.output)

        # after interacting:
        handler.selected
    """

    def __init__(
        self,
        data: pd.DataFrame,
        region_data: dict | None = None,
        region_column: str = 'county',
        region_name_key: str = 'NAME',
        lat_column: str = 'lat',
        lon_column: str = 'lon',
        color_column: str | None = None,
        point_color: str = '#89b4fa',
        point_radius: int = 4,
        polygon_tool: bool = False
    ):
        """
        Parameters
        ----------
        data : DataFrame
            Must contain ``lat_column`` and ``lon_column``.
        region_data : dict, optional
            GeoJSON FeatureCollection for clickable regions (e.g. counties).
        region_column : str
            Column in ``data`` to match against clicked region name.
        region_name_key : str
            Property key in the GeoJSON features that holds the region name.
        lat_column, lon_column : str
            Column names for coordinates.
        color_column : str, optional
            Column to assign a unique color per value (e.g. ``'common_name'``).
            Overrides ``point_color`` when set.
        point_color : str
            Default CSS color for map markers (used when ``color_column`` is None).
        point_radius : int
            Pixel radius for map markers.
        polygon_tool : bool
            if true add polygon_tool
        """
        self._df = data
        self._lat = lat_column
        self._lon = lon_column
        self._region_col = region_column
        self._region_name_key = region_name_key
        self.selected: pd.DataFrame | None = None
        self._last_label = ''

        if polygon_tool:
            print('loading shapely...')
            from shapely.geometry import Point, shape
            self._shapely_pt = Point
            self._shapely_shape = shape


        # Build color map
        self._color_map: dict[str, str] = {}
        if color_column and color_column in self._df.columns:
            palette = [
                '#89b4fa', '#a6e3a1', '#f38ba8', '#fab387', '#cba6f7',
                '#89dceb', '#f9e2af', '#94e2d5', '#eba0ac', '#74c7ec',
                '#b4befe', '#a6adc8', '#f5c2e7', '#bac2de', '#f2cdcd',
            ]
            for i, val in enumerate(self._df[color_column].unique()):
                self._color_map[val] = palette[i % len(palette)]

        # Points as single GeoJSON layer
        self._point_color = point_color
        self._point_radius = point_radius
        self._color_column = color_column
        self._points_layer = self._build_points_layer(self._df)

        # Region layer
        self.region_layer: GeoJSON | None = None
        if region_data is not None:
            self.region_layer = GeoJSON(
                data=region_data,
                style={'color': '#6c7086', 'weight': 1, 'fillOpacity': 0.03},
                hover_style={'color': '#a6e3a1', 'weight': 2, 'fillOpacity': 0.15},
                name='Regions',
            )
            self.region_layer.on_click(self._on_region_click)

        # Draw layer — rectangle + polygon
        self.draw_layer = DrawControl(
            rectangle={'shapeOptions': {'color': '#f38ba8', 'weight': 2}},
            polygon={'shapeOptions': {'color': '#cba6f7', 'weight': 2}},
            polyline={}, circle={}, circlemarker={}, marker={},
        )
        self.draw_layer.on_draw(self._on_draw)

    def add_to(self, m) -> None:
        """Add all layers (points, regions, draw) to the map."""
        m.add(self._points_layer)
        if self.region_layer is not None:
            m.add(self.region_layer)
        m.add(self.draw_layer)

    def describe(self, group_col: str, value_col: str):
        """Print summary and stats for ``value_col`` grouped by ``group_col``."""
        if self.selected is None or len(self.selected) == 0:
            print("No selection yet — click a county, draw a rectangle, or draw a polygon")
            return
        print(f"{self._last_label} — {len(self.selected)} points")
        display(
            self.selected[[group_col, value_col]]
            .groupby(group_col)
            .describe()
        )

    #
    # INTERNAL
    #
    def _build_points_layer(self, df: pd.DataFrame) -> GeoJSON:
        """Build a single GeoJSON layer from a DataFrame."""
        features = []
        for _, row in df.iterrows():
            c = self._point_color
            if self._color_map and self._color_column:
                c = self._color_map.get(row.get(self._color_column), c)
            features.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [float(row[self._lon]), float(row[self._lat])],
                },
                'properties': {'style': {'color': c, 'radius': self._point_radius}},
            })
        return GeoJSON(
            data={'type': 'FeatureCollection', 'features': features},
            point_style={
                'radius': self._point_radius,
                'fillOpacity': 0.7,
                'weight': 1,
            },
            style_callback=_point_style_callback,
            name='Points',
        )

    def _on_region_click(self, feature, **kwargs):
        name = feature['properties'].get(self._region_name_key, '')
        filtered = self._df[self._df[self._region_col].str.lower() == name.lower()]
        self.selected = filtered
        self._last_label = f"Region: {name}"

    def _on_draw(self, _control, action, geo_json):
        if action != 'created':
            return
        geom = geo_json['geometry']
        geo_type = geom.get('type', '')

        if geo_type == 'Polygon':
            poly = self._shapely_shape(geom)
            mask = self._df.apply(
                lambda r: poly.contains(self._shapely_pt(r[self._lon], r[self._lat])), axis=1
            )
            filtered = self._df[mask]
            label = 'Polygon'
        else:
            return

        self.selected = filtered
        self._last_label = f"{label} selection"


def _point_style_callback(feature: dict) -> dict:
    """Extract per-feature style for the GeoJSON point layer."""
    props = feature.get('properties', {}).get('style', {})
    return {
        'color': props.get('color', '#89b4fa'),
        'fillColor': props.get('color', '#89b4fa'),
        'radius': props.get('radius', 4),
        'fillOpacity': 0.7,
        'weight': 1,
    }
