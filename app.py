"""
VOC Geospatial Visualization Portal
Main Streamlit Application
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Import custom modules
from src.data_loader import VOCDataLoader, load_and_preprocess_data
from src.interpolation import InterpolationEngine
from src.visualization import (
    create_interpolation_map,
    create_mapbox_visualization,
    create_simple_scatter_map,
    create_distribution_plot,
    create_statistics_cards,
    create_time_series_plot
)
import config

# Page configuration
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout=config.LAYOUT,
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    """Load custom CSS styling"""
    css_file = Path("assets/styles.css")
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()


@st.cache_data(show_spinner="Loading VOC data...")
def load_data():
    """Load and cache VOC data"""
    return load_and_preprocess_data()


@st.cache_data(show_spinner="Computing interpolation...")
def compute_interpolation(
    compound: str,
    method: str,
    cities: tuple,
    rounds: tuple,
    grid_res: int,
    agg_func: str,
    power: float,
    variogram: str,
    _gdf: pd.DataFrame  # Underscore prefix to skip hashing
):
    """Compute and cache interpolation results"""
    loader = VOCDataLoader()

    # Filter data
    filtered = _gdf[
        (_gdf['Compound'] == compound) &
        (_gdf['City'].isin(cities)) &
        (_gdf['Round'].isin(rounds))
    ].copy()

    if len(filtered) == 0:
        return None, None, None, None

    # Aggregate by census tract
    agg_data = loader.aggregate_by_tract(filtered, compound=None, agg_func=agg_func)

    if len(agg_data) < 3:
        return None, None, None, agg_data

    # Create interpolation engine with parameters
    kwargs = {}
    if method == 'idw':
        kwargs['power'] = power
    elif 'kriging' in method:
        kwargs['variogram_model'] = variogram

    engine = InterpolationEngine(method=method, **kwargs)

    # Perform interpolation
    try:
        XI, YI, ZI = engine.interpolate(
            agg_data['lon'].values,
            agg_data['lat'].values,
            agg_data['Adj_ppbV'].values,
            grid_resolution=grid_res
        )
        return XI, YI, ZI, agg_data
    except Exception as e:
        st.error(f"Interpolation failed: {e}")
        return None, None, None, agg_data


# Header
st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 2rem; border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                margin-bottom: 2rem; text-align: center;">
        <h1 style="color: white; font-weight: 700; font-size: 2.5rem; margin: 0;
                   text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);">
            🗺️ VOC Geospatial Visualization Portal
        </h1>
        <p style="color: rgba(255, 255, 255, 0.9); font-size: 1.2rem; margin-top: 0.5rem;">
            Interactive Spatial Analysis of Volatile Organic Compounds
        </p>
    </div>
""", unsafe_allow_html=True)

# Load data
try:
    with st.spinner("Loading data and census tract geometries..."):
        gdf, raw_df = load_data()

    loader = VOCDataLoader()
    compounds = loader.get_compounds(raw_df)
    cities = loader.get_cities(raw_df)
    rounds = loader.get_rounds(raw_df)

except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Make sure VOC_cleanTract.xlsx is in the data/ directory and all dependencies are installed.")
    st.stop()

# Sidebar controls
with st.sidebar:
    st.markdown("### 🎛️ Visualization Controls")

    # Compound selection
    selected_compound = st.selectbox(
        "Select Compound",
        options=compounds,
        index=0,
        help="Choose which VOC compound to visualize"
    )

    # Interpolation method
    selected_method = st.selectbox(
        "Interpolation Method",
        options=list(InterpolationEngine.METHODS.keys()),
        format_func=lambda x: InterpolationEngine.METHODS[x],
        index=0,
        help="Choose spatial interpolation algorithm"
    )

    # Advanced settings
    with st.expander("⚙️ Advanced Settings"):
        grid_resolution = st.slider(
            "Grid Resolution",
            min_value=config.MIN_GRID_RESOLUTION,
            max_value=config.MAX_GRID_RESOLUTION,
            value=config.DEFAULT_GRID_RESOLUTION,
            step=10,
            help="Higher resolution = smoother surface but slower"
        )

        agg_function = st.selectbox(
            "Aggregation Function",
            options=['mean', 'median', 'max', 'percentile_95'],
            index=0,
            help="How to combine multiple measurements per tract"
        )

        # Method-specific parameters
        if selected_method == 'idw':
            idw_power = st.slider(
                "IDW Power Parameter",
                min_value=1.0,
                max_value=5.0,
                value=2.0,
                step=0.5,
                help="Higher values = more weight to nearby points"
            )
        else:
            idw_power = 2.0

        if 'kriging' in selected_method:
            variogram_model = st.selectbox(
                "Variogram Model",
                options=['gaussian', 'exponential', 'spherical', 'linear'],
                index=0
            )
        else:
            variogram_model = 'gaussian'

        use_log_scale = st.checkbox(
            "Use Log Scale",
            value=False,
            help="Use logarithmic color scale for highly skewed data"
        )

        show_samples = st.checkbox(
            "Show Sensor Locations",
            value=True,
            help="Show sensor locations highlighted in red"
        )

        # Opacity/Transparency slider
        interpolation_opacity = st.slider(
            "Interpolation Transparency",
            min_value=0.0,
            max_value=1.0,
            value=0.6,
            step=0.05,
            help="Adjust transparency of interpolation surface (0=transparent, 1=opaque)"
        )

        # Basemap selection
        use_satellite = st.checkbox(
            "Use Satellite Basemap",
            value=True,
            help="Use satellite/map imagery as basemap"
        )

    # Data filters
    st.markdown("### 🔍 Data Filters")

    selected_cities = st.multiselect(
        "Cities",
        options=cities,
        default=cities,
        help="Filter by city"
    )

    selected_rounds = st.multiselect(
        "Measurement Rounds",
        options=rounds,
        default=rounds,
        help="Filter by measurement round"
    )

    # Date range filter
    min_date = gdf['Date_collect'].min().date()
    max_date = gdf['Date_collect'].max().date()

    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.info(f"""
    **Dataset Info:**
    - **Total Records**: {len(raw_df):,}
    - **Compounds**: {len(compounds)}
    - **Census Tracts**: {gdf['CensusTract'].nunique()}
    - **Cities**: {', '.join(cities)}
    - **Date Range**: {min_date} to {max_date}
    """)

# Main content area
if not selected_cities or not selected_rounds:
    st.warning("⚠️ Please select at least one city and one round from the sidebar filters.")
    st.stop()

# Compute interpolation
XI, YI, ZI, agg_data = compute_interpolation(
    compound=selected_compound,
    method=selected_method,
    cities=tuple(selected_cities),
    rounds=tuple(selected_rounds),
    grid_res=grid_resolution,
    agg_func=agg_function,
    power=idw_power,
    variogram=variogram_model,
    _gdf=gdf
)

if XI is None or agg_data is None or len(agg_data) == 0:
    st.error("❌ No data available for selected filters. Please adjust your selection.")
    st.stop()

# Get actual house/sensor locations
filtered_data = gdf[
    (gdf['Compound'] == selected_compound) &
    (gdf['City'].isin(selected_cities)) &
    (gdf['Round'].isin(selected_rounds))
]
house_data = loader.get_house_locations(filtered_data, compound=None, agg_func=agg_function)

# Create two columns for main display
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("### 🗺️ Interpolated Surface Map")

    if ZI is not None:
        # Use original working contour visualization with actual house/sensor locations
        fig = create_interpolation_map(
            XI=XI,
            YI=YI,
            ZI=ZI,
            sample_data=house_data if len(house_data) > 0 else agg_data,
            compound_name=selected_compound,
            method_name=InterpolationEngine.METHODS[selected_method],
            use_log_scale=use_log_scale,
            percentile_range=(config.PERCENTILE_MIN, config.PERCENTILE_MAX),
            show_samples=show_samples,
            opacity=interpolation_opacity
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
    else:
        # Fallback to scatter map
        st.warning("⚠️ Not enough points for interpolation. Showing sample locations only.")
        fig = create_simple_scatter_map(
            sample_data=agg_data,
            compound_name=selected_compound
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### 📊 Statistics")

    # Calculate statistics (filtered_data already defined above)
    stats = loader.get_statistics(filtered_data, selected_compound)
    stats_cards = create_statistics_cards(stats)

    # Display metrics
    st.metric("📈 Mean", f"{stats['mean']:.3f} ppbV")
    st.metric("📊 Median", f"{stats['median']:.3f} ppbV")
    st.metric("🔝 Max", f"{stats['max']:.3f} ppbV")
    st.metric("🔢 Samples", f"{stats['count']:,}")

    st.markdown("---")

    # Distribution plot
    st.markdown("#### Distribution")
    dist_fig = create_distribution_plot(filtered_data, selected_compound)
    st.plotly_chart(dist_fig, use_container_width=True)

# Bottom section - Additional visualizations
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📈 Time Series", "🔄 Method Comparison", "📋 Data Table"])

with tab1:
    st.markdown("### Temporal Trends")
    if len(rounds) > 1:
        time_fig = create_time_series_plot(filtered_data, selected_compound, group_by='Round')
        st.plotly_chart(time_fig, use_container_width=True)
    else:
        st.info("Time series requires multiple measurement rounds. Please select more rounds in the filters.")

with tab2:
    st.markdown("### Compare Interpolation Methods")

    comparison_methods = st.multiselect(
        "Select methods to compare (max 4)",
        options=list(InterpolationEngine.METHODS.keys()),
        default=[selected_method],
        format_func=lambda x: InterpolationEngine.METHODS[x],
        max_selections=4,
        key="comparison_methods"
    )

    if len(comparison_methods) > 0:
        cols = st.columns(min(len(comparison_methods), 2))

        for i, method in enumerate(comparison_methods):
            with cols[i % 2]:
                # Compute interpolation for this method
                XI_comp, YI_comp, ZI_comp, _ = compute_interpolation(
                    compound=selected_compound,
                    method=method,
                    cities=tuple(selected_cities),
                    rounds=tuple(selected_rounds),
                    grid_res=grid_resolution,
                    agg_func=agg_function,
                    power=idw_power,
                    variogram=variogram_model,
                    _gdf=gdf
                )

                if ZI_comp is not None:
                    # Use original working visualization
                    fig_comp = create_interpolation_map(
                        XI=XI_comp,
                        YI=YI_comp,
                        ZI=ZI_comp,
                        sample_data=agg_data,
                        compound_name=selected_compound,
                        method_name=InterpolationEngine.METHODS[method],
                        use_log_scale=use_log_scale,
                        percentile_range=(config.PERCENTILE_MIN, config.PERCENTILE_MAX),
                        show_samples=False,
                        opacity=interpolation_opacity
                    )
                    st.plotly_chart(fig_comp, use_container_width=True)

with tab3:
    st.markdown("### Aggregated Data by Census Tract")

    # Display aggregated data table
    display_df = agg_data[['CensusTract', 'lat', 'lon', 'Adj_ppbV']].copy()
    display_df.columns = ['Census Tract', 'Latitude', 'Longitude', f'{selected_compound} (ppbV)']
    display_df = display_df.sort_values(f'{selected_compound} (ppbV)', ascending=False).reset_index(drop=True)

    st.dataframe(
        display_df.style.format({
            'Latitude': '{:.4f}',
            'Longitude': '{:.4f}',
            f'{selected_compound} (ppbV)': '{:.3f}'
        }).background_gradient(subset=[f'{selected_compound} (ppbV)'], cmap='RdYlGn_r'),
        use_container_width=True,
        height=400
    )

    # Download button
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Data as CSV",
        data=csv,
        file_name=f"{selected_compound}_aggregated.csv",
        mime="text/csv"
    )

# Footer
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>VOC Geospatial Visualization Portal | Built with Streamlit & Plotly</p>
    </div>
""", unsafe_allow_html=True)
