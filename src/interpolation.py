"""
Interpolation Engine Module
Implements multiple spatial interpolation methods
"""

import numpy as np
from scipy.interpolate import Rbf, griddata
from typing import Tuple, Optional
import warnings

# Try to import kriging, but make it optional
try:
    from pykrige.ok import OrdinaryKriging
    from pykrige.uk import UniversalKriging
    KRIGING_AVAILABLE = True
except ImportError:
    KRIGING_AVAILABLE = False
    warnings.warn("PyKrige not available. Kriging methods will be disabled.")


class InterpolationEngine:
    """
    Unified interface for multiple spatial interpolation methods
    """

    # Available interpolation methods with descriptions
    METHODS = {
        'idw': 'Inverse Distance Weighting',
        'linear': 'Linear Interpolation',
        'cubic': 'Cubic Interpolation',
        'nearest': 'Nearest Neighbor',
        'rbf_multiquadric': 'RBF (Multiquadric)',
        'rbf_gaussian': 'RBF (Gaussian)',
        'rbf_thin_plate': 'RBF (Thin Plate Spline)',
        'rbf_linear': 'RBF (Linear)',
    }

    # Add kriging methods if available
    if KRIGING_AVAILABLE:
        METHODS.update({
            'kriging_ordinary': 'Ordinary Kriging',
            'kriging_universal': 'Universal Kriging',
        })

    def __init__(self, method: str = 'idw', **kwargs):
        """
        Initialize interpolation engine

        Args:
            method: Interpolation method to use
            **kwargs: Method-specific parameters
                - power: IDW power parameter (default: 2)
                - smoothing: IDW smoothing factor (default: 0)
                - variogram_model: Kriging variogram ('gaussian', 'exponential', 'spherical', 'linear')
                - rbf_smooth: RBF smoothing parameter (default: 0)
        """
        if method not in self.METHODS:
            raise ValueError(f"Unknown method: {method}. Available: {list(self.METHODS.keys())}")

        if method.startswith('kriging') and not KRIGING_AVAILABLE:
            raise ValueError("Kriging methods require PyKrige. Please install it first.")

        self.method = method
        self.kwargs = kwargs

        # Set default parameters
        self.power = kwargs.get('power', 2.0)
        self.smoothing = kwargs.get('smoothing', 0.0)
        self.variogram_model = kwargs.get('variogram_model', 'gaussian')
        self.rbf_smooth = kwargs.get('rbf_smooth', 0)

    def interpolate(
        self,
        x: np.ndarray,
        y: np.ndarray,
        z: np.ndarray,
        grid_resolution: int = 100,
        bounds: Optional[Tuple[float, float, float, float]] = None
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Perform spatial interpolation on scattered points

        Args:
            x: X-coordinates (longitude)
            y: Y-coordinates (latitude)
            z: Values to interpolate (Adj_ppbV)
            grid_resolution: Number of grid points per dimension
            bounds: Optional (min_x, min_y, max_x, max_y). If None, computed from data

        Returns:
            Tuple of (XI, YI, ZI) - interpolated grid coordinates and values
        """
        # Handle edge cases
        if len(x) < 3:
            raise ValueError("Need at least 3 points for interpolation")

        # Remove any NaN values
        valid_mask = ~(np.isnan(x) | np.isnan(y) | np.isnan(z))
        x = x[valid_mask]
        y = y[valid_mask]
        z = z[valid_mask]

        # Compute bounds if not provided
        if bounds is None:
            min_x, max_x = x.min(), x.max()
            min_y, max_y = y.min(), y.max()

            # Add 5% padding
            x_padding = (max_x - min_x) * 0.05
            y_padding = (max_y - min_y) * 0.05

            min_x -= x_padding
            max_x += x_padding
            min_y -= y_padding
            max_y += y_padding
        else:
            min_x, min_y, max_x, max_y = bounds

        # Create regular grid
        xi = np.linspace(min_x, max_x, grid_resolution)
        yi = np.linspace(min_y, max_y, grid_resolution)
        XI, YI = np.meshgrid(xi, yi)

        # Perform interpolation based on method
        if self.method == 'idw':
            ZI = self._idw(x, y, z, XI, YI)
        elif self.method.startswith('kriging'):
            ZI = self._kriging(x, y, z, xi, yi)
        elif self.method.startswith('rbf'):
            ZI = self._rbf(x, y, z, XI, YI)
        elif self.method in ['linear', 'cubic', 'nearest']:
            ZI = griddata((x, y), z, (XI, YI), method=self.method)
        else:
            raise ValueError(f"Unknown interpolation method: {self.method}")

        return XI, YI, ZI

    def _idw(
        self,
        x: np.ndarray,
        y: np.ndarray,
        z: np.ndarray,
        XI: np.ndarray,
        YI: np.ndarray
    ) -> np.ndarray:
        """
        Inverse Distance Weighting interpolation

        Args:
            x, y: Source point coordinates
            z: Source values
            XI, YI: Target grid coordinates

        Returns:
            Interpolated values on grid
        """
        ZI = np.zeros_like(XI)

        for i in range(XI.shape[0]):
            for j in range(XI.shape[1]):
                # Calculate distances from grid point to all source points
                distances = np.sqrt((x - XI[i, j])**2 + (y - YI[i, j])**2)

                # Add smoothing to avoid division by zero
                distances = distances + self.smoothing

                # Check if grid point coincides with a source point
                if np.any(distances < 1e-10):
                    # Use the value of the nearest source point
                    min_idx = np.argmin(distances)
                    ZI[i, j] = z[min_idx]
                else:
                    # Calculate weights
                    weights = 1.0 / (distances ** self.power)
                    # Weighted average
                    ZI[i, j] = np.sum(weights * z) / np.sum(weights)

        return ZI

    def _kriging(
        self,
        x: np.ndarray,
        y: np.ndarray,
        z: np.ndarray,
        xi: np.ndarray,
        yi: np.ndarray
    ) -> np.ndarray:
        """
        Kriging interpolation using PyKrige

        Args:
            x, y: Source point coordinates
            z: Source values
            xi, yi: Target grid coordinates (1D arrays)

        Returns:
            Interpolated values on grid
        """
        if not KRIGING_AVAILABLE:
            raise RuntimeError("PyKrige is not available")

        try:
            if self.method == 'kriging_ordinary':
                OK = OrdinaryKriging(
                    x, y, z,
                    variogram_model=self.variogram_model,
                    verbose=False,
                    enable_plotting=False
                )
                ZI, ss = OK.execute('grid', xi, yi)
            else:  # universal kriging
                UK = UniversalKriging(
                    x, y, z,
                    variogram_model=self.variogram_model,
                    verbose=False,
                    enable_plotting=False
                )
                ZI, ss = UK.execute('grid', xi, yi)

            return ZI

        except Exception as e:
            # Fallback to IDW if kriging fails
            warnings.warn(f"Kriging failed: {e}. Falling back to IDW.")
            XI, YI = np.meshgrid(xi, yi)
            return self._idw(x, y, z, XI, YI)

    def _rbf(
        self,
        x: np.ndarray,
        y: np.ndarray,
        z: np.ndarray,
        XI: np.ndarray,
        YI: np.ndarray
    ) -> np.ndarray:
        """
        Radial Basis Function interpolation

        Args:
            x, y: Source point coordinates
            z: Source values
            XI, YI: Target grid coordinates

        Returns:
            Interpolated values on grid
        """
        # Extract RBF function type from method name
        function_map = {
            'rbf_multiquadric': 'multiquadric',
            'rbf_gaussian': 'gaussian',
            'rbf_thin_plate': 'thin_plate',
            'rbf_linear': 'linear'
        }

        function = function_map.get(self.method, 'multiquadric')

        try:
            rbf_interp = Rbf(x, y, z, function=function, smooth=self.rbf_smooth)
            ZI = rbf_interp(XI, YI)
            return ZI
        except Exception as e:
            # Fallback to IDW if RBF fails
            warnings.warn(f"RBF interpolation failed: {e}. Falling back to IDW.")
            return self._idw(x, y, z, XI, YI)


def mask_extrapolation_regions(
    XI: np.ndarray,
    YI: np.ndarray,
    ZI: np.ndarray,
    sample_points: np.ndarray,
    max_distance: float = 0.05
) -> np.ndarray:
    """
    Mask interpolated regions too far from sample points

    Args:
        XI, YI: Grid coordinates
        ZI: Interpolated values
        sample_points: Array of (x, y) sample coordinates
        max_distance: Maximum distance from samples (in coordinate units)

    Returns:
        Masked interpolation values (NaN for distant regions)
    """
    from scipy.spatial.distance import cdist

    # Flatten grid
    grid_points = np.c_[XI.ravel(), YI.ravel()]

    # Calculate distance to nearest sample
    distances = cdist(grid_points, sample_points)
    min_distances = distances.min(axis=1).reshape(XI.shape)

    # Mask areas beyond threshold
    ZI_masked = np.where(min_distances < max_distance, ZI, np.nan)

    return ZI_masked


def test_interpolation():
    """
    Test function to verify interpolation works correctly
    """
    print("Testing InterpolationEngine...")

    # Create sample data
    np.random.seed(42)
    n_points = 20
    x = np.random.uniform(-95, -94, n_points)
    y = np.random.uniform(29.5, 30.5, n_points)
    z = np.sin(x * 10) + np.cos(y * 10) + np.random.normal(0, 0.1, n_points)

    print(f"\nGenerated {n_points} sample points")
    print(f"X range: {x.min():.4f} to {x.max():.4f}")
    print(f"Y range: {y.min():.4f} to {y.max():.4f}")
    print(f"Z range: {z.min():.4f} to {z.max():.4f}")

    # Test each method
    for method in InterpolationEngine.METHODS.keys():
        try:
            print(f"\nTesting {method}...")
            engine = InterpolationEngine(method=method)
            XI, YI, ZI = engine.interpolate(x, y, z, grid_resolution=50)

            print(f"  ✅ {method}: Grid shape {ZI.shape}, values [{ZI.min():.3f}, {ZI.max():.3f}]")
        except Exception as e:
            print(f"  ❌ {method}: {e}")

    print("\n✅ Interpolation engine test complete!")


if __name__ == "__main__":
    test_interpolation()
