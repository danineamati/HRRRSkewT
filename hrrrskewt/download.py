import os

import pandas as pd
import xarray as xr
from herbie.fast import FastHerbie

# Regex to capture all required profile and surface variables:
# - Profile: TMP, DPT, UGRD, VGRD, HGT at isobaric levels (e.g., 1000 mb, 850 mb)
# - Surface/Near-surface:
#   - TMP:surface, PRES:surface, HGT:surface (topography)
#   - TMP:2 m above ground, DPT:2 m above ground
#   - UGRD:10 m above ground, VGRD:10 m above ground
SKEWT_VARS_RE = (
    r":(?:TMP|DPT|UGRD|VGRD|HGT|PRES):"
    r"(?:(?:[0-9]+ mb)|(?:surface)|(?:[2,10] m above ground))"
)


def parse_date_inputs(
    start_time: str, end_time: str | None = None, interval_hours: int = 1
) -> pd.DatetimeIndex:
    """
    Parse start and end times to generate a range of target dates.

    Parameters:
        start_time: Start date/time of the sounding, e.g., "2025-10-24T00:00".
        end_time: End date/time of the sounding. If None, set to start_time.
        interval_hours: Time interval in hours for multiple soundings date range.

    Returns:
        A pandas DatetimeIndex of the target dates.
    """
    if end_time is None:
        end_time = start_time

    return pd.date_range(start_time, end_time, freq=f"{interval_hours}h")


def retrieve_hrrr_data(
    dates: pd.DatetimeIndex, forecast_hour: int = 0, product: str = "prs"
) -> xr.Dataset:
    """
    Query and retrieve HRRR data using FastHerbie for the specified dates
    and forecast hour.

    Parameters:
        dates: DatetimeIndex of dates to download.
        forecast_hour: Forecast lead time in hours (0 is Analysis).
        product: HRRR product name, e.g. 'prs' or 'nat'.

    Returns:
        An xarray Dataset containing the HRRR data for the selected variables.
    """
    fxx = [forecast_hour]

    print("--- FastHerbie Setup ---")
    print(f"Dates: {dates.strftime('%Y-%m-%d %H:%M').tolist()}")
    print(f"Forecast Hours: {fxx}")
    print(f"Searching for variables with regex: {SKEWT_VARS_RE}")

    print(f"Attempting to use HRRR '{product}' product for full vertical resolution...")
    fh = FastHerbie(dates, model="hrrr", fxx=fxx, product=product)

    ds_out = fh.xarray(SKEWT_VARS_RE, remove_grib=False)
    print("Found the data.")

    if isinstance(ds_out, list):
        print(f"fh.xarray returned a list of {len(ds_out)} datasets. Merging...")
        ds = xr.merge(ds_out, compat="override")
    else:
        ds = ds_out

    print("Dataset successfully loaded into memory.")
    return ds


def extract_point_data(ds: xr.Dataset, latitude: float, longitude: float) -> xr.Dataset:
    """
    Extract data from the HRRR dataset for the point nearest to the target coordinates.

    Parameters:
        ds: The input HRRR xarray Dataset.
        latitude: Latitude of the target location.
        longitude: Longitude of the target location.

    Returns:
        An xarray Dataset containing point data.
    """
    print("\n--- Extracting Point Data ---")
    print(f"Target Lat/Lon: ({latitude}, {longitude})")

    points_df = pd.DataFrame({"latitude": [latitude], "longitude": [longitude]})

    return ds.herbie.pick_points(points_df, method="nearest")


def save_point_data(
    ds_point: xr.Dataset,
    latitude: float,
    longitude: float,
    start_time: str,
    forecast_hour: int = 0,
    product: str = "prs",
    save_dir: str = "./data_hrrr",
) -> str:
    """
    Save the point dataset as a NetCDF file.

    Parameters:
        ds_point: The point dataset to save.
        latitude: Latitude of the target location.
        longitude: Longitude of the target location.
        start_time: Start date/time string, used to name the output file.
        forecast_hour: Forecast lead time in hours.
        product: HRRR product name.
        save_dir: Directory where the output NetCDF file should be saved.

    Returns:
        The file path to the saved NetCDF file.
    """
    os.makedirs(save_dir, exist_ok=True)

    dt = pd.to_datetime(start_time)
    start_str = dt.strftime("%Y%m%d_%H%M")

    lat_str = f"{latitude:.3f}".replace(".", "p")
    lon_str = f"{longitude:.3f}".replace(".", "p")

    # Add attributes to dataset before saving
    ds_point.attrs["forecast_hour"] = forecast_hour
    ds_point.attrs["product"] = product

    fxx_str = f"f{forecast_hour:02d}"
    filename = f"hrrr_skewt_{lat_str}_{lon_str}_{start_str}_{product}_{fxx_str}.nc"
    save_path = os.path.join(save_dir, filename)

    print("\n--- Saving Point Data to NetCDF ---")
    print(f"Saving point dataset to: {save_path}")
    ds_point.to_netcdf(save_path)
    print("Save complete.")

    return save_path


def download_hrrr_data(
    latitude: float,
    longitude: float,
    start_time: str,
    end_time: str | None = None,
    forecast_hour: int = 0,
    interval_hours: int = 1,
    product: str = "prs",
    save_dir: str = "./data_hrrr",
) -> str:
    """
    Download HRRR meteorological data for a specific coordinate point
    and save as a NetCDF file.

    Parameters:
        latitude: Latitude of the target location.
        longitude: Longitude of the target location.
        start_time: Start date/time of the sounding, e.g., "2025-10-24T00:00".
        end_time: End date/time of the sounding. If None, set to start_time.
        forecast_hour: Forecast lead time in hours (0 is Analysis).
        interval_hours: Time interval in hours for multiple soundings date range.
        product: HRRR product name.
        save_dir: Directory where the output NetCDF file should be saved.

    Returns:
        The file path to the saved NetCDF file.
    """
    # 1. Parse date inputs
    dates = parse_date_inputs(start_time, end_time, interval_hours)

    # 2. Query and retrieve data
    ds = retrieve_hrrr_data(dates, forecast_hour, product)

    # 3. Extract nearest point
    ds_point = extract_point_data(ds, latitude, longitude)

    # 4. Save to NetCDF
    save_path = save_point_data(
        ds_point, latitude, longitude, start_time, forecast_hour, product, save_dir
    )

    return save_path
