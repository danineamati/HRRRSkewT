from dataclasses import dataclass
from typing import Optional, Union
import tyro

from hrrrskewt.download import download_hrrr_data

@dataclass
class Download:
    """Download HRRR data for a given location and time range."""
    latitude: float
    """Latitude of the target location."""
    longitude: float
    """Longitude of the target location."""
    start_time: str
    """Start date/time of the sounding, e.g., '2025-10-24T00:00:00'."""
    end_time: Optional[str] = None
    """End date/time of the sounding. Defaults to start_time."""
    forecast_hour: int = 0
    """Forecast lead time in hours (0 is Analysis)."""
    interval_hours: int = 1
    """Interval between soundings in hours."""
    save_dir: str = "./hrrr_netcdf"
    """Directory to save the NetCDF file."""

    def run(self) -> None:
        download_hrrr_data(
            latitude=self.latitude,
            longitude=self.longitude,
            start_time=self.start_time,
            end_time=self.end_time,
            forecast_hour=self.forecast_hour,
            interval_hours=self.interval_hours,
            save_dir=self.save_dir
        )

@dataclass
class Plot:
    """Generate a SkewT plot from downloaded HRRR NetCDF data."""
    nc_file: str
    """Path to the downloaded HRRR NetCDF file."""
    save_dir: str = "./skewt_spot"
    """Directory to save the generated plot."""
    rx_fire: bool = True
    """Whether to annotate the plot with variables relevant to prescribed fire."""

    def run(self) -> None:
        # Placeholder for plotting logic
        print(f"Plotting {self.nc_file} (rx-fire={self.rx_fire})...")
        print("Plot command is not fully implemented yet.")

def main() -> None:
    # Use tyro to parse CLI arguments for the Union of commands
    command = tyro.cli(Union[Download, Plot])
    command.run()

if __name__ == "__main__":
    main()
