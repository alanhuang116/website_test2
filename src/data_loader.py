"""
Data Loading and Processing Module
Loads VOC data and merges with census tract geometries
"""

import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path
from typing import Tuple, List, Optional
import config
from src.geocoding import CensusTractGeocoder


class VOCDataLoader:
    """
    Handles loading and processing of VOC monitoring data
    """

    def __init__(self, data_dir: str = None):
        """
        Initialize data loader

        Args:
            data_dir: Directory containing data files (default: config.DATA_DIR)
        """
        self.data_dir = Path(data_dir or config.DATA_DIR)
        self.excel_path = self.data_dir / config.EXCEL_FILE
        self.geocoder = CensusTractGeocoder(cache_dir=str(self.data_dir))

    def load_data(self) -> pd.DataFrame:
        """
        Load VOC data from Excel file

        Returns:
            DataFrame with VOC measurements
        """
        print(f"Loading VOC data from {self.excel_path}...")
        df = pd.read_excel(self.excel_path)
        print(f"Loaded {len(df)} records")
        print(f"Columns: {list(df.columns)}")
        return df

    def merge_with_geometries(self, df: pd.DataFrame) -> gpd.GeoDataFrame:
        """
        Merge VOC data with census tract geometries

        Args:
            df: DataFrame with VOC data

        Returns:
            GeoDataFrame with spatial information
        """
        print("Merging with census tract geometries...")

        # Get census tract geometries
        tracts_gdf = self.geocoder.get_tracts()

        # Convert CensusTract to string for matching
        df['CensusTract_str'] = df['CensusTract'].astype(str)
        tracts_gdf['GEOID_str'] = tracts_gdf['GEOID'].astype(str)

        # Merge data with geometries
        merged = df.merge(
            tracts_gdf[['GEOID_str', 'geometry', 'centroid_lat', 'centroid_lon', 'area_sqkm', 'NAMELSAD']],
            left_on='CensusTract_str',
            right_on='GEOID_str',
            how='left'
        )

        # Convert to GeoDataFrame
        gdf = gpd.GeoDataFrame(merged, geometry='geometry')

        # Rename columns for convenience
        gdf['lat'] = gdf['centroid_lat']
        gdf['lon'] = gdf['centroid_lon']
        gdf['tract_name'] = gdf['NAMELSAD']

        print(f"Merged {len(gdf)} records with geometries")
        print(f"Unique census tracts: {gdf['CensusTract'].nunique()}")

        return gdf

    def aggregate_by_tract(
        self,
        df: pd.DataFrame,
        compound: Optional[str] = None,
        agg_func: str = 'mean'
    ) -> pd.DataFrame:
        """
        Aggregate multiple measurements per census tract

        Args:
            df: DataFrame with VOC data
            compound: Optional compound to filter for
            agg_func: Aggregation function ('mean', 'median', 'max', 'percentile_95')

        Returns:
            DataFrame aggregated by census tract
        """
        # Filter by compound if specified
        if compound:
            df = df[df['Compound'] == compound].copy()

        # Define aggregation based on function
        if agg_func == 'percentile_95':
            agg_data = df.groupby(['CensusTract', 'lat', 'lon']).agg({
                'Adj_ppbV': lambda x: np.percentile(x, 95)
            }).reset_index()
        else:
            agg_data = df.groupby(['CensusTract', 'lat', 'lon']).agg({
                'Adj_ppbV': agg_func
            }).reset_index()

        return agg_data

    def get_house_locations(
        self,
        df: pd.DataFrame,
        compound: Optional[str] = None,
        agg_func: str = 'mean'
    ) -> pd.DataFrame:
        """
        Get actual house/sensor locations with measurements

        Args:
            df: DataFrame with VOC data
            compound: Optional compound to filter for
            agg_func: Aggregation function for multiple measurements per house

        Returns:
            DataFrame with house locations
        """
        # Filter by compound if specified
        if compound:
            df = df[df['Compound'] == compound].copy()

        # Aggregate by HouseID (actual sensor locations)
        if agg_func == 'percentile_95':
            house_data = df.groupby(['HouseID', 'CensusTract', 'lat', 'lon', 'City']).agg({
                'Adj_ppbV': lambda x: np.percentile(x, 95)
            }).reset_index()
        else:
            house_data = df.groupby(['HouseID', 'CensusTract', 'lat', 'lon', 'City']).agg({
                'Adj_ppbV': agg_func
            }).reset_index()

        return house_data

    def get_compounds(self, df: pd.DataFrame) -> List[str]:
        """
        Get list of unique compounds

        Args:
            df: DataFrame with VOC data

        Returns:
            Sorted list of compound names
        """
        return sorted(df['Compound'].unique())

    def get_cities(self, df: pd.DataFrame) -> List[str]:
        """
        Get list of unique cities

        Args:
            df: DataFrame with VOC data

        Returns:
            Sorted list of city names
        """
        return sorted(df['City'].unique())

    def get_rounds(self, df: pd.DataFrame) -> List[int]:
        """
        Get list of unique rounds

        Args:
            df: DataFrame with VOC data

        Returns:
            Sorted list of round numbers
        """
        return sorted(df['Round'].unique())

    def filter_data(
        self,
        df: pd.DataFrame,
        compounds: Optional[List[str]] = None,
        cities: Optional[List[str]] = None,
        rounds: Optional[List[int]] = None,
        date_range: Optional[Tuple] = None
    ) -> pd.DataFrame:
        """
        Filter data based on various criteria

        Args:
            df: DataFrame with VOC data
            compounds: List of compounds to include
            cities: List of cities to include
            rounds: List of rounds to include
            date_range: Tuple of (start_date, end_date)

        Returns:
            Filtered DataFrame
        """
        filtered = df.copy()

        if compounds:
            filtered = filtered[filtered['Compound'].isin(compounds)]

        if cities:
            filtered = filtered[filtered['City'].isin(cities)]

        if rounds:
            filtered = filtered[filtered['Round'].isin(rounds)]

        if date_range:
            start_date, end_date = date_range
            filtered = filtered[
                (filtered['Date_collect'] >= pd.to_datetime(start_date)) &
                (filtered['Date_collect'] <= pd.to_datetime(end_date))
            ]

        return filtered

    def get_statistics(self, df: pd.DataFrame, compound: str) -> dict:
        """
        Calculate summary statistics for a compound

        Args:
            df: DataFrame with VOC data
            compound: Compound name

        Returns:
            Dictionary with statistics
        """
        compound_data = df[df['Compound'] == compound]['Adj_ppbV']

        return {
            'count': len(compound_data),
            'mean': compound_data.mean(),
            'median': compound_data.median(),
            'std': compound_data.std(),
            'min': compound_data.min(),
            'max': compound_data.max(),
            'percentile_25': compound_data.quantile(0.25),
            'percentile_75': compound_data.quantile(0.75),
            'percentile_95': compound_data.quantile(0.95)
        }


def load_and_preprocess_data(use_cache: bool = True) -> Tuple[gpd.GeoDataFrame, pd.DataFrame]:
    """
    Main function to load and preprocess all data
    This function can be cached with @st.cache_data in Streamlit

    Args:
        use_cache: Whether to use cached census tract data

    Returns:
        Tuple of (GeoDataFrame with merged data, DataFrame with raw data)
    """
    loader = VOCDataLoader()

    # Load raw data
    df = loader.load_data()

    # Merge with geometries
    gdf = loader.merge_with_geometries(df)

    print("Data loading and preprocessing complete!")
    print(f"   Total records: {len(gdf)}")
    print(f"   Unique compounds: {gdf['Compound'].nunique()}")
    print(f"   Unique census tracts: {gdf['CensusTract'].nunique()}")
    print(f"   Date range: {gdf['Date_collect'].min()} to {gdf['Date_collect'].max()}")

    return gdf, df


def test_data_loader():
    """
    Test function to verify data loader works correctly
    """
    print("Testing VOCDataLoader...")

    loader = VOCDataLoader()

    # Load data
    df = loader.load_data()
    print(f"\nLoaded {len(df)} records")

    # Get unique values
    compounds = loader.get_compounds(df)
    print(f"\nFound {len(compounds)} unique compounds")
    print(f"First 5 compounds: {compounds[:5]}")

    cities = loader.get_cities(df)
    print(f"\nCities: {cities}")

    rounds = loader.get_rounds(df)
    print(f"Rounds: {rounds}")

    # Merge with geometries
    gdf = loader.merge_with_geometries(df)
    print(f"\nMerged data has {len(gdf)} records")
    print(f"Has lat/lon: {('lat' in gdf.columns) and ('lon' in gdf.columns)}")

    # Test aggregation
    first_compound = compounds[0]
    agg_data = loader.aggregate_by_tract(gdf, compound=first_compound, agg_func='mean')
    print(f"\nAggregated data for {first_compound}: {len(agg_data)} tracts")

    # Test statistics
    stats = loader.get_statistics(df, first_compound)
    print(f"\nStatistics for {first_compound}:")
    for key, value in stats.items():
        print(f"  {key}: {value:.4f}")

    print("\nData loader test successful!")


if __name__ == "__main__":
    test_data_loader()
