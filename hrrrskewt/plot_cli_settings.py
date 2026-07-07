import os
from dataclasses import dataclass
from typing import Any, Literal

from metpy.units import units


@dataclass
class SkewTPlotSettings:
    """Configuration class for Skew-T and Hodograph plotting."""

    # Subplot placements [left, bottom, width, height]
    skewt_rect: tuple[float, float, float, float] = (0.1, 0.1, 0.48, 0.6)
    hodo_rect: tuple[float, float, float, float] = (0.7, 0.5, 0.2, 0.2)
    hodo_cb_rect: tuple[float, float, float, float] = (0.7, 0.4, 0.2, 0.02)

    # Plot limits and parameters
    p_min: Any = 100 * units.hPa
    p_max: Any = 1050 * units.hPa
    t_min: Any = -30 * units.degC
    t_max: Any = 30 * units.degC

    wind_max: Any = 25 * units.meters / units.second
    skew_rotation: int = 45
    figsize: tuple[int, int] = (9, 9)

    # Barb plotting
    barbs_interval: int = 1  # Plot every nth barb to reduce clutter
    bard_offset: float = 0

    # Adiabat styles and alphas
    adiabat_alpha: float = 0.2
    adiabat_linestyle: str = "-"

    dry_adiabat_color: str = "darkorange"
    moist_adiabat_color: str = "navy"

    mixing_ratio_alpha: float = 0.2
    mixing_ratio_linestyle: str = ":"

    # Axes resolution for plotting lines
    temp_resolution: int = 5
    p_resolution: int = 100

    # Surface markers
    surface_marker: str = "o"
    surface_marker_size: int = 8
    surface_marker_color_t: str = "darkred"
    surface_marker_color_td: str = "darkgreen"

    # Height axis
    show_height_axis: bool = True

    height_units: str = "km"  # 'm' or 'km'
    height_tick_interval: int = 2  # in meters or km

    height_axis_location: str = "left"  # 'left' or 'right'
    height_axis_left_offset: int = 60  # Only used if height_axis_location is 'left'
    extrapolate_height_axis: bool = True
    height_type: str = "geopotential"  # 'msl' (geometric height) or 'geopotential'

    # Mixing Height calculation
    mixing_height_temp_offset: float = (
        5.0 * units.delta_degC
    )  # (offset from surface temperature)

    # Legend
    legend_loc: str = "upper left"
    legend_outside: bool = True  # If True, place in bottom right of figure
    legend_anchor: tuple = (0.9, 0.05)  # For outside legend placement

    # Saving
    save_dir: str = "./skewt_spot"
    save_filename: str | None = None

    # Debugging
    show_debug_rects: bool = False


@dataclass
class LimitsSettings:
    """Plot pressure and temperature boundaries."""

    preset: Literal["standard", "lower", "full"] = "standard"
    """Preset selection: 'standard', 'lower' (boundary layer focus),
    or 'full' (stratosphere focus)."""
    p_min: float | None = None
    """Custom minimum pressure limit in hPa (overrides preset)."""
    p_max: float | None = None
    """Custom maximum pressure limit in hPa (overrides preset)."""
    t_min: float | None = None
    """Custom minimum temperature limit in °C (overrides preset)."""
    t_max: float | None = None
    """Custom maximum temperature limit in °C (overrides preset)."""
    wind_max: float | None = None
    """Custom maximum wind speed display limit on the hodograph in m/s (default: 25.0)."""

    def resolve(self) -> tuple[float, float, float, float]:
        """Resolve preset and overrides to return (p_min, p_max, t_min, t_max)."""
        preset_lower = self.preset.lower()
        if preset_lower == "lower":
            p_min, p_max, t_min, t_max = 650.0, 1050.0, 6.0, 22.0
        elif preset_lower == "full":
            p_min, p_max, t_min, t_max = 10.0, 1400.0, -60.0, 50.0
        else:  # "standard"
            p_min, p_max, t_min, t_max = 100.0, 1050.0, -30.0, 30.0

        if self.p_min is not None:
            p_min = self.p_min
        if self.p_max is not None:
            p_max = self.p_max
        if self.t_min is not None:
            t_min = self.t_min
        if self.t_max is not None:
            t_max = self.t_max

        return p_min, p_max, t_min, t_max


@dataclass
class HeightAxisSettings:
    """Height axis rendering options."""

    show: bool = True
    """Whether to show the secondary height axis."""
    type: Literal["geopotential", "msl"] = "geopotential"
    """Type of height calculation: 'geopotential' or 'msl'."""
    units: Literal["km", "m"] = "km"
    """Height units: 'km' or 'm'."""
    tick_interval: float = 2.0
    """Interval between ticks on the height axis."""
    location: Literal["left", "right"] = "left"
    """Axis location: 'left' or 'right'."""
    left_offset: int = 60
    """Horizontal offset in points when location is 'left'."""
    extrapolate: bool = True
    """Whether to extrapolate height tick marks beyond data bounds."""


@dataclass
class MixingHeightSettings:
    """Mixing height computation parameters."""

    temp_offset: float = 5.0
    """Temperature offset from surface temperature in delta °C/K for parcel lift."""


@dataclass
class VisualSettings:
    """Advanced visual layout and line styles configuration."""

    figsize: tuple[int, int] = (9, 9)
    """Width and height of the generated figure in inches."""
    skew_rotation: int = 45
    """Rotation angle for the Skew-T grid in degrees."""
    barbs_interval: int = 1
    """Plot wind barbs every N levels (higher numbers reduce clutter)."""
    barb_offset: float = 0.0
    """Horizontal offset for wind barbs (fraction of x-axis range)."""
    adiabat_alpha: float = 0.2
    """Opacity for dry and moist adiabats (0 to 1)."""
    adiabat_linestyle: str = "-"
    """Line style for adiabats (e.g. '-', '--', ':')."""
    dry_adiabat_color: str = "darkorange"
    """Matplotlib color name/hex for dry adiabats."""
    moist_adiabat_color: str = "navy"
    """Matplotlib color name/hex for moist adiabats."""
    mixing_ratio_alpha: float = 0.2
    """Opacity for mixing ratio lines (0 to 1)."""
    mixing_ratio_linestyle: str = ":"
    """Line style for mixing ratio lines."""
    temp_resolution: int = 5
    """Interval for temperature gridlines in °C."""
    p_resolution: int = 100
    """Interval for pressure gridlines in hPa."""
    surface_marker: str = "o"
    """Marker shape for surface/2m conditions."""
    surface_marker_size: int = 8
    """Size of the surface markers."""
    surface_marker_color_t: str = "darkred"
    """Color for surface temperature marker."""
    surface_marker_color_td: str = "darkgreen"
    """Color for surface dewpoint marker."""
    legend_loc: str = "upper left"
    """Legend location inside the plot (if legend-outside is False)."""
    legend_outside: bool = True
    """Whether to place the legend outside the subplot in the bottom right."""
    legend_anchor: tuple[float, float] = (0.9, 0.05)
    """Legend bounding box anchor coordinate when legend-outside is True."""
    show_debug_rects: bool = False
    """Draw red/blue outline rectangles around subplots for layout debugging."""


@dataclass
class IOSettings:
    """Input/Output and filename options."""

    save_dir: str = "./skewt_spot"
    """Directory to save the generated plot."""
    save_filename: str | None = None
    """Optional name for the output image file (overrides all autogeneration)."""
    suffix: str | None = None
    """Optional suffix to append to the autogenerated filename, e.g. '_custom_label'."""
    include_preset_suffix: bool = True
    """Whether to automatically append the limits preset name
    (e.g. '_lower', '_full') as a suffix."""


def create_plot_settings(
    limits: LimitsSettings,
    height: HeightAxisSettings,
    mixing: MixingHeightSettings,
    visuals: VisualSettings,
    io: IOSettings,
    nc_file: str,
) -> SkewTPlotSettings:
    """Convert CLI-friendly dataclasses to the units-aware SkewTPlotSettings."""
    p_min_val, p_max_val, t_min_val, t_max_val = limits.resolve()

    # 1. Resolve save filename
    target_save_filename = io.save_filename
    if target_save_filename is None:
        base_name = os.path.basename(nc_file)
        if base_name.endswith(".nc"):
            base_name_no_ext = base_name[:-3]
        else:
            base_name_no_ext = base_name

        filename_parts = [base_name_no_ext]
        if io.include_preset_suffix:
            filename_parts.append(f"_{limits.preset}")
        if io.suffix:
            filename_parts.append(io.suffix)

        target_save_filename = "".join(filename_parts) + ".png"

    settings = SkewTPlotSettings(
        skewt_rect=(0.1, 0.1, 0.48, 0.6),
        hodo_rect=(0.7, 0.5, 0.2, 0.2),
        hodo_cb_rect=(0.7, 0.4, 0.2, 0.02),
        p_min=p_min_val * units.hPa,
        p_max=p_max_val * units.hPa,
        t_min=t_min_val * units.degC,
        t_max=t_max_val * units.degC,
        wind_max=(limits.wind_max if limits.wind_max is not None else 25.0)
        * units.meters
        / units.second,
        skew_rotation=visuals.skew_rotation,
        figsize=visuals.figsize,
        barbs_interval=visuals.barbs_interval,
        bard_offset=visuals.barb_offset,
        adiabat_alpha=visuals.adiabat_alpha,
        adiabat_linestyle=visuals.adiabat_linestyle,
        dry_adiabat_color=visuals.dry_adiabat_color,
        moist_adiabat_color=visuals.moist_adiabat_color,
        mixing_ratio_alpha=visuals.mixing_ratio_alpha,
        mixing_ratio_linestyle=visuals.mixing_ratio_linestyle,
        temp_resolution=visuals.temp_resolution,
        p_resolution=visuals.p_resolution,
        surface_marker=visuals.surface_marker,
        surface_marker_size=visuals.surface_marker_size,
        surface_marker_color_t=visuals.surface_marker_color_t,
        surface_marker_color_td=visuals.surface_marker_color_td,
        show_height_axis=height.show,
        height_units=height.units,
        height_tick_interval=height.tick_interval,
        height_axis_location=height.location,
        height_axis_left_offset=height.left_offset,
        extrapolate_height_axis=height.extrapolate,
        height_type=height.type,
        mixing_height_temp_offset=mixing.temp_offset * units.delta_degC,
        legend_loc=visuals.legend_loc,
        legend_outside=visuals.legend_outside,
        legend_anchor=visuals.legend_anchor,
        save_dir=io.save_dir,
        save_filename=target_save_filename,
        show_debug_rects=visuals.show_debug_rects,
    )
    return settings
