"""
Census Tract Geocoding Module
Downloads and processes US Census Bureau Tiger/Line shapefiles
"""

import geopandas as gpd
import requests
import zipfile
import io
from pathlib import Path
import pandas as pd
from typing import Dict, Tuple
import config


class CensusTractGeocoder:
    """
    Handles all census tract geocoding operations
    Downloads Tiger/Line shapefiles and creates spatial lookups
    """

    TIGER_BASE_URL = "https://www2.census.gov/geo/tiger/TIGER"

    def __init__(self, cache_dir: str = None):
        """
        Initialize geocoder with cache directory

        Args:
            cache_dir: Directory to cache downloaded shapefiles (default: config.DATA_DIR)
        """
        self.cache_dir = Path(cache_dir or config.DATA_DIR)
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        self.geojson_path = self.cache_dir / config.GEOJSON_FILE
        self.state_fips = config.STATE_FIPS
        self.county_fips = config.COUNTY_FIPS
        self.year = config.CENSUS_YEAR

    def get_tracts(self, force_download: bool = False) -> gpd.GeoDataFrame:
        """
        Get census tract geometries, downloading if necessary

        Args:
            force_download: Force re-download even if cached file exists

        Returns:
            GeoDataFrame with census tract geometries
        """
        if self.geojson_path.exists() and not force_download:
            print(f"Loading cached census tracts from {self.geojson_path}...")
            return gpd.read_file(self.geojson_path)

        print("Downloading census tract shapefiles...")
        gdf = self._download_tiger_tracts()

        # Filter to Jefferson County (GEOID starts with 48245)
        county_geoid_prefix = f"{self.state_fips}{self.county_fips}"
        gdf = gdf[gdf['GEOID'].str.startswith(county_geoid_prefix)].copy()

        print(f"Found {len(gdf)} census tracts in Jefferson County")

        # Add centroid coordinates
        centroids = gdf.geometry.centroid
        gdf['centroid_lon'] = centroids.x
        gdf['centroid_lat'] = centroids.y

        # Calculate area in square kilometers
        gdf_projected = gdf.to_crs('EPSG:3857')  # Web Mercator for area calculation
        gdf['area_sqkm'] = gdf_projected.geometry.area / 1e6

        # Save to cache (drop any extra geometry columns first)
        gdf.to_file(self.geojson_path, driver='GeoJSON')
        print(f"Cached {len(gdf)} census tracts to {self.geojson_path}")

        return gdf

    def _download_tiger_tracts(self) -> gpd.GeoDataFrame:
        """
        Download and extract Tiger/Line shapefiles

        Returns:
            GeoDataFrame with all tracts for the state
        """
        url = f"{self.TIGER_BASE_URL}{self.year}/TRACT/tl_{self.year}_{self.state_fips}_tract.zip"

        print(f"Downloading from {url}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Extract to temporary directory
        temp_dir = self.cache_dir / 'tiger_temp'
        temp_dir.mkdir(exist_ok=True, parents=True)

        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            zip_ref.extractall(temp_dir)

        # Load shapefile
        shapefile_path = temp_dir / f'tl_{self.year}_{self.state_fips}_tract.shp'
        gdf = gpd.read_file(shapefile_path)

        print(f"Loaded {len(gdf)} census tracts for Texas")

        return gdf

    def create_lookup_table(self, gdf: gpd.GeoDataFrame) -> Dict[int, Dict]:
        """
        Create fast lookup: CensusTract ID -> {lat, lon, geometry, area}

        Args:
            gdf: GeoDataFrame with census tracts

        Returns:
            Dictionary mapping tract ID to properties
        """
        lookup = {}
        for idx, row in gdf.iterrows():
            tract_id = int(row['GEOID'])
            lookup[tract_id] = {
                'lat': row['centroid_lat'],
                'lon': row['centroid_lon'],
                'geometry': row['geometry'],
                'name': row.get('NAMELSAD', f'Tract {tract_id}'),
                'area_sqkm': row['area_sqkm']
            }
        return lookup

    def get_tract_bounds(self, gdf: gpd.GeoDataFrame) -> Tuple[float, float, float, float]:
        """
        Get bounding box for all tracts

        Args:
            gdf: GeoDataFrame with census tracts

        Returns:
            Tuple of (min_lon, min_lat, max_lon, max_lat)
        """
        bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
        return bounds[0], bounds[1], bounds[2], bounds[3]

    def get_center(self, gdf: gpd.GeoDataFrame) -> Tuple[float, float]:
        """
        Get geographic center of all tracts

        Args:
            gdf: GeoDataFrame with census tracts

        Returns:
            Tuple of (center_lat, center_lon)
        """
        min_lon, min_lat, max_lon, max_lat = self.get_tract_bounds(gdf)
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        return center_lat, center_lon


def test_geocoder():
    """
    Test function to verify geocoder works correctly
    """
    print("Testing CensusTractGeocoder...")
    geocoder = CensusTractGeocoder()

    # Get tracts
    gdf = geocoder.get_tracts()
    print(f"\nLoaded {len(gdf)} tracts")
    print(f"Columns: {list(gdf.columns)}")
    print(f"\nFirst tract:")
    print(gdf.iloc[0][['GEOID', 'NAMELSAD', 'centroid_lat', 'centroid_lon', 'area_sqkm']])

    # Test lookup table
    lookup = geocoder.create_lookup_table(gdf)
    print(f"\nCreated lookup table with {len(lookup)} entries")

    # Test bounds and center
    center_lat, center_lon = geocoder.get_center(gdf)
    print(f"\nGeographic center: ({center_lat:.4f}, {center_lon:.4f})")

    print("\nGeocoder test successful!")


if __name__ == "__main__":
    test_geocoder()
