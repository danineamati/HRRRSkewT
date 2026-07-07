from dataclasses import dataclass, field
from typing import Optional, Union
import tyro

from hrrrskewt.download import download_hrrr_data
from hrrrskewt.plot_cli_settings import (
    LimitsSettings,
    HeightAxisSettings,
    MixingHeightSettings,
    VisualSettings,
    IOSettings,
)

@dataclass
class Download:
    """Download HRRR data for a given location and time range."""
    latitude: float
    """Latitude of the target location."""
    longitude: float
    """Longitude of the target location."""
    start_time: str
    """Start date/time of the sounding, e.g., '2025-10-24T00:00'."""
    end_time: Optional[str] = None
    """End date/time of the sounding. Defaults to start_time."""
    forecast_hour: int = 0
    """Forecast lead time in hours (0 is Analysis)."""
    interval_hours: int = 1
    """Interval between soundings in hours."""
    save_dir: str = "./data_hrrr"
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
    rx_fire: bool = True
    """Whether to annotate the plot with variables relevant to prescribed fire."""

    limits: LimitsSettings = field(default_factory=LimitsSettings)
    """Plot limits configuration (standard, lower, full presets or custom overrides)."""
    height: HeightAxisSettings = field(default_factory=HeightAxisSettings)
    """Height axis rendering options."""
    mixing: MixingHeightSettings = field(default_factory=MixingHeightSettings)
    """Mixing height calculation parameters."""
    visuals: VisualSettings = field(default_factory=VisualSettings)
    """Advanced layout and styling options."""
    io: IOSettings = field(default_factory=IOSettings)
    """Input/Output and filename options."""

    def run(self) -> None:
        import os
        from hrrrskewt.xarray_io import load_hrrr_data, process_profile_data
        from hrrrskewt.calc import (
            calculate_inversion_layer,
            calculate_mixing_level,
            report_inversion_layer,
            report_mixing_level,
        )
        from hrrrskewt.plot import plot_skewt_hodograph
        from hrrrskewt.plot_cli_settings import create_plot_settings

        # 1. Load NetCDF dataset
        ds = load_hrrr_data(self.nc_file)

        # 2. Setup plotting settings
        settings = create_plot_settings(
            limits=self.limits,
            height=self.height,
            mixing=self.mixing,
            visuals=self.visuals,
            io=self.io,
            nc_file=self.nc_file
        )

        # 3. Extract the profile and surface data
        p, T, Td, u, v, metadata = process_profile_data(ds, settings=settings)

        # 4. Perform calculation of inversion and mixing heights if rx_fire is enabled
        inversion_layers = None
        mixing_results = None
        if self.rx_fire:
            inversion_layers = calculate_inversion_layer(p, T, metadata["profile_z"])
            report_inversion_layer(inversion_layers)

            mixing_results = calculate_mixing_level(
                p, T, u, v, metadata["profile_z"], metadata,
                offset=settings.mixing_height_temp_offset
            )
            report_mixing_level(mixing_results)

        # 5. Generate and save the plot
        plot_skewt_hodograph(
            p=p,
            T=T,
            Td=Td,
            u=u,
            v=v,
            metadata=metadata,
            settings=settings,
            mixing_results=mixing_results,
            inversion_layers=inversion_layers
        )


def main() -> None:
    # Use tyro to parse CLI arguments for the Union of commands
    command = tyro.cli(Union[Download, Plot])
    command.run()


if __name__ == "__main__":
    main()

