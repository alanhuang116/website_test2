"""
Configuration settings for VOC Geospatial Portal
"""

# Census Data Configuration
STATE_FIPS = "48"  # Texas
COUNTY_FIPS = "245"  # Jefferson County
CENSUS_YEAR = 2024

# File Paths
DATA_DIR = "data"
EXCEL_FILE = "VOC_cleanTract.xlsx"
GEOJSON_FILE = "census_tracts.geojson"

# Map Configuration
DEFAULT_GRID_RESOLUTION = 100
MIN_GRID_RESOLUTION = 50
MAX_GRID_RESOLUTION = 200

# Color Scale Configuration
PERCENTILE_MIN = 5
PERCENTILE_MAX = 95

# UI Configuration
APP_TITLE = "VOC Geospatial Visualization Portal"
APP_ICON = "🗺️"
LAYOUT = "wide"
