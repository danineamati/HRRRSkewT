import os
from typing import Optional
import pandas as pd
import xarray as xr
from herbie.fast import FastHerbie

# Regex to capture all required profile and surface variables:
# - Profile: TMP, DPT, UGRD, VGRD, HGT at isobaric levels (e.g., 1000 mb, 850 mb)
# - Surface/Near-surface:
#   - TMP:surface, PRES:surface, HGT:surface (topography)
#   - TMP:2 m above ground, DPT:2 m above ground
#   - UGRD:10 m above ground, VGRD:10 m above ground
SKEWT_VARS_RE = r":(?:TMP|DPT|UGRD|VGRD|HGT|PRES):(?:(?:[0-9]+ mb)|(?:surface)|(?:[2,10] m above ground))"

def download_hrrr_data(
    latitude: float,
    longitude: float,
    start_time: str,
    end_time: Optional[str] = None,
    forecast_hour: int = 0,
    interval_hours: int = 1,
    save_dir: str = "./data_hrrr"
) -> str:
    """
    Download HRRR meteorological data for a specific coordinate point and save as a NetCDF file.
    
    Parameters:
        latitude: Latitude of the target location.
        longitude: Longitude of the target location.
        start_time: Start date/time of the sounding, e.g., "2025-10-24T00:00".
        end_time: End date/time of the sounding. If None, set to start_time.
        forecast_hour: Forecast lead time in hours (0 is Analysis).
        interval_hours: Time interval in hours for multiple soundings date range.
        save_dir: Directory where the output NetCDF file should be saved.
        
    Returns:
        The file path to the saved NetCDF file.
    """
    # 1. Parse date inputs
    if end_time is None:
        end_time = start_time
        
    dates = pd.date_range(start_time, end_time, freq=f"{interval_hours}h")
    fxx = [forecast_hour]
    
    print("--- FastHerbie Setup ---")
    print(f"Dates: {dates.strftime('%Y-%m-%d %H:%M').tolist()}")
    print(f"Forecast Hours: {fxx}")
    print(f"Searching for variables with regex: {SKEWT_VARS_RE}")
    
    # 2. Query and retrieve data
    print("Attempting to use HRRR 'prs' product for full vertical resolution...")
    fh = FastHerbie(dates, model="hrrr", fxx=fxx, product="prs")
    
    ds_out = fh.xarray(SKEWT_VARS_RE, remove_grib=False)
    
    if isinstance(ds_out, list):
        print(f"fh.xarray returned a list of {len(ds_out)} datasets. Merging...")
        ds = xr.merge(ds_out, compat="override")
    else:
        ds = ds_out
        
    print("Dataset successfully loaded into memory.")
    
    # 3. Extract nearest point
    print("\n--- Extracting Point Data ---")
    print(f"Target Lat/Lon: ({latitude}, {longitude})")
    
    points_df = pd.DataFrame({
        "latitude": [latitude],
        "longitude": [longitude]
    })
    
    ds_point = ds.herbie.pick_points(points_df, method="nearest")
    
    # 4. Save to NetCDF
    os.makedirs(save_dir, exist_ok=True)
    
    dt = pd.to_datetime(start_time)
    start_str = dt.strftime("%Y%m%d_%H%M")
    
    lat_str = f"{latitude:.3f}".replace(".", "p")
    lon_str = f"{longitude:.3f}".replace(".", "p")
    
    filename = f"hrrr_skewt_{lat_str}_{lon_str}_{start_str}.nc"
    save_path = os.path.join(save_dir, filename)
    
    print(f"\n--- Saving Point Data to NetCDF ---")
    print(f"Saving point dataset to: {save_path}")
    ds_point.to_netcdf(save_path)
    print("Save complete.")
    
    return save_path
