"""
Visualization Components Module
Creates interactive maps and charts using Plotly
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Optional, Tuple
import config


def create_interpolation_map(
    XI: np.ndarray,
    YI: np.ndarray,
    ZI: np.ndarray,
    sample_data: pd.DataFrame,
    compound_name: str,
    method_name: str,
    use_log_scale: bool = False,
    percentile_range: Tuple[float, float] = (5, 95),
    show_samples: bool = True,
    show_contours: bool = True,
    opacity: float = 0.6
) -> go.Figure:
    """
    Create beautiful interpolated surface map with Plotly

    Args:
        XI, YI: Grid coordinates (meshgrid)
        ZI: Interpolated values
        sample_data: DataFrame with sample points (must have 'lat', 'lon', 'Adj_ppbV', 'CensusTract')
        compound_name: Name of the compound being visualized
        method_name: Name of interpolation method
        use_log_scale: Whether to use log scale for colors
        percentile_range: Tuple of (min, max) percentiles for color scale
        show_samples: Whether to show sample points
        show_contours: Whether to show contour lines

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    # Calculate robust color scale bounds using percentiles
    valid_ZI = ZI[~np.isnan(ZI)]
    if len(valid_ZI) > 0:
        vmin = np.percentile(valid_ZI, percentile_range[0])
        vmax = np.percentile(valid_ZI, percentile_range[1])
    else:
        vmin, vmax = 0, 1

    # Apply log scale if requested
    if use_log_scale and vmin > 0:
        ZI_display = np.log10(ZI + 1e-10)  # Add small value to avoid log(0)
        vmin_display = np.log10(vmin)
        vmax_display = np.log10(vmax)
        colorbar_title = f"{compound_name}<br>log₁₀(ppbV)"
    else:
        ZI_display = ZI
        vmin_display = vmin
        vmax_display = vmax
        colorbar_title = f"{compound_name}<br>(ppbV)"

    # Add interpolated surface as contour with opacity control
    fig.add_trace(go.Contour(
        x=XI[0],
        y=YI[:, 0],
        z=ZI_display,
        colorscale='RdYlGn_r',  # Red (high) - Yellow - Green (low)
        opacity=opacity,  # User-controlled transparency
        colorbar=dict(
            title=dict(
                text=colorbar_title,
                font=dict(size=12, family='Inter, sans-serif')
            ),
            thickness=20,
            len=0.7,
            x=1.02
        ),
        contours=dict(
            showlabels=show_contours,
            labelfont=dict(size=10, color='black', family='Inter, sans-serif'),
            coloring='heatmap'
        ),
        hovertemplate='Lat: %{y:.4f}<br>Lon: %{x:.4f}<br>Value: %{z:.3f}<extra></extra>',
        name='Interpolated Surface',
        zmin=vmin_display,
        zmax=vmax_display
    ))

    # Add sample points - highlighted in RED for sensor locations
    if show_samples and len(sample_data) > 0:
        # Check if we have house-level data or tract-level data
        if 'HouseID' in sample_data.columns:
            hover_text = sample_data['HouseID']
            hover_template = (
                '<b>SENSOR: %{text}</b><br>' +
                '<b>Value:</b> %{customdata:.3f} ppbV<br>' +
                '<b>Lat:</b> %{y:.4f}<br>' +
                '<b>Lon:</b> %{x:.4f}<extra></extra>'
            )
        else:
            hover_text = sample_data['CensusTract']
            hover_template = (
                '<b>SENSOR</b><br>' +
                '<b>Tract:</b> %{text}<br>' +
                '<b>Value:</b> %{customdata:.3f} ppbV<br>' +
                '<b>Lat:</b> %{y:.4f}<br>' +
                '<b>Lon:</b> %{x:.4f}<extra></extra>'
            )

        fig.add_trace(go.Scatter(
            x=sample_data['lon'],
            y=sample_data['lat'],
            mode='markers',
            marker=dict(
                size=12,  # Larger size for visibility
                color='red',  # Red color for sensor locations
                symbol='circle',
                line=dict(width=2, color='white'),  # White outline for contrast
                opacity=1.0  # Fully opaque sensors
            ),
            text=hover_text,
            customdata=sample_data['Adj_ppbV'],
            hovertemplate=hover_template,
            name='Sensors'
        ))

    # Calculate center and bounds
    center_lat = sample_data['lat'].mean()
    center_lon = sample_data['lon'].mean()

    # Layout with modern styling
    fig.update_layout(
        title=dict(
            text=f"{compound_name} - {method_name}",
            font=dict(size=20, family='Inter, sans-serif', color='#2c3e50'),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title='Longitude',
            showgrid=True,
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title='Latitude',
            showgrid=True,
            gridcolor='lightgray',
            scaleanchor='x',
            scaleratio=1
        ),
        height=700,
        margin=dict(l=60, r=100, t=50, b=60),
        paper_bgcolor='rgba(255,255,255,1)',
        plot_bgcolor='rgba(255,255,255,1)',
        font=dict(family='Inter, sans-serif'),
        showlegend=True,
        legend=dict(
            x=0.01,
            y=0.99,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(0,0,0,0.2)',
            borderwidth=1
        )
    )

    return fig


def create_mapbox_visualization(
    XI: np.ndarray,
    YI: np.ndarray,
    ZI: np.ndarray,
    house_data: pd.DataFrame,
    sample_data: pd.DataFrame,
    compound_name: str,
    method_name: str,
    use_log_scale: bool = False,
    percentile_range: Tuple[float, float] = (5, 95),
    show_samples: bool = True,
    opacity: float = 0.6
) -> go.Figure:
    """
    Create interpolated surface map with SATELLITE imagery basemap

    Args:
        XI, YI: Grid coordinates (meshgrid)
        ZI: Interpolated values
        sample_data: DataFrame with sample points
        compound_name: Name of compound
        method_name: Interpolation method name
        use_log_scale: Use log scale for colors
        percentile_range: Color scale percentile range
        show_samples: Show sensor locations
        opacity: Transparency of interpolation surface (0-1)

    Returns:
        Plotly Figure with satellite basemap
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    # Calculate robust color scale bounds
    valid_ZI = ZI[~np.isnan(ZI)]
    if len(valid_ZI) > 0:
        vmin = np.percentile(valid_ZI, percentile_range[0])
        vmax = np.percentile(valid_ZI, percentile_range[1])
    else:
        vmin, vmax = 0, 1

    # Apply log scale if requested
    if use_log_scale and vmin > 0:
        ZI_display = np.log10(ZI + 1e-10)
        vmin_display = np.log10(vmin)
        vmax_display = np.log10(vmax)
        colorbar_title = f"{compound_name}<br>log₁₀(ppbV)"
    else:
        ZI_display = ZI
        vmin_display = vmin
        vmax_display = vmax
        colorbar_title = f"{compound_name}<br>(ppbV)"

    # Create figure
    fig = go.Figure()

    # Add interpolated density surface - use larger radius to minimize zoom changes
    fig.add_trace(go.Densitymapbox(
        lat=YI.flatten(),
        lon=XI.flatten(),
        z=ZI_display.flatten(),
        radius=30,  # Larger radius = less zoom sensitivity
        colorscale='RdYlGn_r',
        opacity=opacity,
        zmin=vmin_display,
        zmax=vmax_display,
        colorbar=dict(
            title=dict(text=colorbar_title, font=dict(size=12)),
            thickness=20,
            len=0.7
        ),
        hovertemplate='Lat: %{lat:.4f}<br>Lon: %{lon:.4f}<br>Value: %{z:.3f}<extra></extra>',
        name='Interpolation',
        showscale=True
    ))

    # Add RED sensor location markers - use house_data if available, else sample_data
    sensor_data = house_data if 'HouseID' in house_data.columns and len(house_data) > 0 else sample_data

    if show_samples and len(sensor_data) > 0:
        # Determine if we have house-level data or tract-level data
        if 'HouseID' in sensor_data.columns:
            hover_text = sensor_data['HouseID']
            hover_template = (
                '<b>SENSOR: %{text}</b><br>' +
                '<b>City:</b> %{customdata[0]}<br>' +
                '<b>Value:</b> %{customdata[1]:.3f} ppbV<br>' +
                '<b>Tract:</b> %{customdata[2]}<extra></extra>'
            )
            custom_data = sensor_data[['City', 'Adj_ppbV', 'CensusTract']].values
        else:
            hover_text = sensor_data['CensusTract']
            hover_template = (
                '<b>SENSOR</b><br>' +
                '<b>Tract:</b> %{text}<br>' +
                '<b>Value:</b> %{customdata:.3f} ppbV<extra></extra>'
            )
            custom_data = sensor_data['Adj_ppbV']

        fig.add_trace(go.Scattermapbox(
            lat=sensor_data['lat'],
            lon=sensor_data['lon'],
            mode='markers',
            marker=dict(
                size=14,
                color='red',
                opacity=1.0,
                symbol='circle'
            ),
            text=hover_text,
            customdata=custom_data,
            hovertemplate=hover_template,
            name='Sensors'
        ))

    # Calculate center
    center_lat = sample_data['lat'].mean()
    center_lon = sample_data['lon'].mean()

    # Update layout with SATELLITE basemap
    fig.update_layout(
        title=dict(
            text=f"{compound_name} - {method_name}",
            font=dict(size=20, family='Inter, sans-serif', color='#2c3e50'),
            x=0.5,
            xanchor='center'
        ),
        mapbox=dict(
            style='open-street-map',  # Using OSM, can switch to satellite if mapbox token available
            center=dict(lat=center_lat, lon=center_lon),
            zoom=10
        ),
        height=700,
        margin=dict(l=0, r=100, t=50, b=0),
        showlegend=True,
        legend=dict(
            x=0.01,
            y=0.99,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(0,0,0,0.2)',
            borderwidth=1
        )
    )

    return fig


def create_simple_scatter_map(
    sample_data: pd.DataFrame,
    compound_name: str,
    percentile_range: Tuple[float, float] = (5, 95)
) -> go.Figure:
    """
    Create simple scatter map without interpolation

    Args:
        sample_data: DataFrame with sample points
        compound_name: Name of compound
        percentile_range: Color scale percentile range

    Returns:
        Plotly Figure
    """
    vmin = sample_data['Adj_ppbV'].quantile(percentile_range[0] / 100)
    vmax = sample_data['Adj_ppbV'].quantile(percentile_range[1] / 100)

    fig = go.Figure()

    fig.add_trace(go.Scattergeo(
        lat=sample_data['lat'],
        lon=sample_data['lon'],
        mode='markers',
        marker=dict(
            size=12,
            color=sample_data['Adj_ppbV'],
            colorscale='RdYlGn_r',
            showscale=True,
            colorbar=dict(
                title=f"{compound_name}<br>(ppbV)",
                thickness=20,
                len=0.7
            ),
            line=dict(width=1, color='white'),
            cmin=vmin,
            cmax=vmax
        ),
        text=sample_data['CensusTract'],
        customdata=sample_data['Adj_ppbV'],
        hovertemplate=(
            '<b>Census Tract:</b> %{text}<br>' +
            '<b>Value:</b> %{customdata:.3f} ppbV<br>' +
            '<b>Lat:</b> %{lat:.4f}<br>' +
            '<b>Lon:</b> %{lon:.4f}<extra></extra>'
        ),
        name='Samples'
    ))

    center_lat = sample_data['lat'].mean()
    center_lon = sample_data['lon'].mean()

    fig.update_layout(
        title=f"{compound_name} - Sample Locations",
        geo=dict(
            scope='usa',
            projection_type='mercator',
            showland=True,
            landcolor='rgb(243, 243, 243)',
            center=dict(lat=center_lat, lon=center_lon)
        ),
        height=600,
        margin=dict(l=0, r=100, t=50, b=0)
    )

    return fig


def create_distribution_plot(data: pd.DataFrame, compound_name: str) -> go.Figure:
    """
    Create distribution histogram/violin plot

    Args:
        data: DataFrame with Adj_ppbV values
        compound_name: Name of compound

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    # Violin plot
    fig.add_trace(go.Violin(
        y=data['Adj_ppbV'],
        box_visible=True,
        meanline_visible=True,
        fillcolor='#667eea',
        opacity=0.6,
        line_color='#764ba2',
        name=compound_name
    ))

    fig.update_layout(
        title=dict(
            text="Concentration Distribution",
            font=dict(size=14, family='Inter, sans-serif')
        ),
        yaxis_title="Concentration (ppbV)",
        height=300,
        margin=dict(l=40, r=20, t=40, b=40),
        font=dict(family='Inter, sans-serif'),
        showlegend=False,
        paper_bgcolor='rgba(255,255,255,1)',
        plot_bgcolor='rgba(250,250,250,1)',
        yaxis=dict(
            gridcolor='rgba(200,200,200,0.3)',
            showgrid=True
        )
    )

    return fig


def create_histogram(data: pd.DataFrame, compound_name: str) -> go.Figure:
    """
    Create histogram of concentration values

    Args:
        data: DataFrame with Adj_ppbV values
        compound_name: Name of compound

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=data['Adj_ppbV'],
        nbinsx=30,
        marker=dict(
            color='#667eea',
            line=dict(color='white', width=1)
        ),
        name=compound_name
    ))

    fig.update_layout(
        title=f"Distribution of {compound_name}",
        xaxis_title="Concentration (ppbV)",
        yaxis_title="Frequency",
        height=300,
        margin=dict(l=40, r=20, t=40, b=40),
        font=dict(family='Inter, sans-serif'),
        showlegend=False,
        paper_bgcolor='rgba(255,255,255,1)',
        plot_bgcolor='rgba(250,250,250,1)'
    )

    return fig


def create_statistics_cards(stats: dict) -> dict:
    """
    Prepare statistics for display as metric cards

    Args:
        stats: Dictionary of statistics from data_loader.get_statistics()

    Returns:
        Dictionary formatted for display
    """
    return {
        'Count': f"{stats['count']:,}",
        'Mean': f"{stats['mean']:.3f}",
        'Median': f"{stats['median']:.3f}",
        'Std Dev': f"{stats['std']:.3f}",
        'Min': f"{stats['min']:.3f}",
        'Max': f"{stats['max']:.3f}",
        '95th %ile': f"{stats['percentile_95']:.3f}"
    }


def create_time_series_plot(
    data: pd.DataFrame,
    compound_name: str,
    group_by: str = 'Round'
) -> go.Figure:
    """
    Create time series or trend plot

    Args:
        data: DataFrame with time/round data
        compound_name: Name of compound
        group_by: Column to group by ('Round' or 'Date_collect')

    Returns:
        Plotly Figure
    """
    # Aggregate by time period
    if group_by == 'Round':
        grouped = data.groupby('Round').agg({
            'Adj_ppbV': ['mean', 'std', 'count']
        }).reset_index()
        grouped.columns = ['Round', 'Mean', 'Std', 'Count']
        x_col = 'Round'
        x_title = "Measurement Round"
    else:
        grouped = data.groupby('Date_collect').agg({
            'Adj_ppbV': ['mean', 'std', 'count']
        }).reset_index()
        grouped.columns = ['Date', 'Mean', 'Std', 'Count']
        x_col = 'Date'
        x_title = "Date"

    fig = go.Figure()

    # Add mean line
    fig.add_trace(go.Scatter(
        x=grouped[x_col],
        y=grouped['Mean'],
        mode='lines+markers',
        name='Mean',
        line=dict(color='#667eea', width=3),
        marker=dict(size=10)
    ))

    # Add error band (±1 std)
    fig.add_trace(go.Scatter(
        x=grouped[x_col],
        y=grouped['Mean'] + grouped['Std'],
        mode='lines',
        name='±1 Std',
        line=dict(width=0),
        showlegend=False
    ))

    fig.add_trace(go.Scatter(
        x=grouped[x_col],
        y=grouped['Mean'] - grouped['Std'],
        mode='lines',
        name='±1 Std',
        line=dict(width=0),
        fillcolor='rgba(102, 126, 234, 0.2)',
        fill='tonexty',
        showlegend=True
    ))

    fig.update_layout(
        title=f"{compound_name} - Temporal Trend",
        xaxis_title=x_title,
        yaxis_title="Concentration (ppbV)",
        height=350,
        margin=dict(l=40, r=20, t=40, b=40),
        font=dict(family='Inter, sans-serif'),
        hovermode='x unified',
        paper_bgcolor='rgba(255,255,255,1)',
        plot_bgcolor='rgba(250,250,250,1)'
    )

    return fig


if __name__ == "__main__":
    print("Visualization module loaded successfully!")
    print(f"Available functions:")
    print("  - create_interpolation_map()")
    print("  - create_simple_scatter_map()")
    print("  - create_distribution_plot()")
    print("  - create_histogram()")
    print("  - create_time_series_plot()")
