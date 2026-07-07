import os
from dataclasses import dataclass
from typing import Any, Tuple, Optional

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.ticker import NullFormatter, MultipleLocator, FuncFormatter

import metpy.calc as mpcalc
import metpy.interpolate as mpinterpolate
import metpy.constants as mpconst
from metpy.plots import SkewT, Hodograph
from metpy.units import units

from hrrrskewt.plot_cli_settings import SkewTPlotSettings

def add_debug_patches(fig: plt.Figure, settings: SkewTPlotSettings) -> None:
    """Add colored rectangles to debug subplot placement."""
    print("Adding debug patches...")
    fig.patches.append(
        patches.Rectangle(
            (settings.skewt_rect[0], settings.skewt_rect[1]),
            settings.skewt_rect[2],
            settings.skewt_rect[3],
            transform=fig.transFigure,
            edgecolor="r",
            facecolor="none",
            zorder=10,
            linewidth=2,
        )
    )
    fig.patches.append(
        patches.Rectangle(
            (settings.hodo_rect[0], settings.hodo_rect[1]),
            settings.hodo_rect[2],
            settings.hodo_rect[3],
            transform=fig.transFigure,
            edgecolor="b",
            facecolor="none",
            zorder=10,
            linewidth=2,
        )
    )
    fig.patches.append(
        patches.Rectangle(
            (settings.hodo_cb_rect[0], settings.hodo_cb_rect[1]),
            settings.hodo_cb_rect[2],
            settings.hodo_cb_rect[3],
            transform=fig.transFigure,
            edgecolor="g",
            facecolor="none",
            zorder=10,
            linewidth=2,
        )
    )


def draw_inversion_layer(
    skew: SkewT,
    p: np.ndarray,
    inversion_layers: dict,
    settings: SkewTPlotSettings
) -> None:
    """Plot the inversion layers on the Skew-T as a band of red."""
    if len(inversion_layers["inversion_pressure"]) == 0:
        return

    label_added = False
    print("Plotting inversion layers...")
    for p_inv in inversion_layers["inversion_pressure"]:
        p_below = p[p < p_inv]
        p_above = p[p > p_inv]

        if len(p_below) == 0 or len(p_above) == 0:
            continue

        p_lower = p_below[0]
        p_upper = p_above[-1]

        skew.ax.fill_betweenx(
            [p_lower, p_upper],
            -1000,
            1000,
            color="red",
            alpha=0.2,
            zorder=0,
            label="Inversion Layer" if not label_added else None
        )
        label_added = True


def draw_mixing_height(
    skew: SkewT,
    p: np.ndarray,
    metadata: dict,
    results: dict
) -> None:
    """Draw the parcel trajectory and mark the mixing height."""
    if results is None:
        return

    print("Drawing mixing height and parcel trajectory...")
    surf = metadata["surface"]

    if p[0] < surf["sp"]:
        p_full = np.concatenate(([surf["sp"]], p))
    else:
        p_full = p
    
    parcel_path = mpcalc.dry_lapse(p_full, surf["t2m"] + results["offset"],
                                   reference_pressure=surf["sp"])

    mask_higher_p = p_full >= results["pressure"]
    lowest_avail_p_idx = np.argmin(p_full[mask_higher_p])
    if lowest_avail_p_idx < len(p_full) - 1:
        next_p = p_full[lowest_avail_p_idx + 1]
        mask = p_full >= next_p
    else:
        mask = mask_higher_p

    skew.plot(p_full[mask], parcel_path[mask].to("degC"), color="black",
              linestyle="--", linewidth=1.5, label="Parcel Path (Dry)")

    skew.plot(results["pressure"], results["temperature"].to("degC"),
              marker="o", markersize=10, color="black",
              label="Mixing Height", linestyle="none")


def draw_surface_conditions(
    skew: SkewT,
    metadata: dict,
    settings: SkewTPlotSettings
) -> None:
    """Draw surface T and Td points on the Skew-T."""
    print("Drawing surface conditions...")
    surf = metadata["surface"]

    skew.plot(
        surf["sp"],
        surf["t2m"].to("degC"),
        marker=settings.surface_marker,
        markersize=settings.surface_marker_size,
        color=settings.surface_marker_color_t,
        label="Temperature [2m]",
        linestyle="none",
    )

    skew.plot(
        surf["sp"],
        surf["d2m"].to("degC"),
        marker=settings.surface_marker,
        markersize=settings.surface_marker_size,
        color=settings.surface_marker_color_td,
        label="Dewpoint [2m]",
        linestyle="none",
    )


def draw_sp(skew: SkewT, metadata: dict) -> None:
    """Draw a dotted black horizontal line indicating the surface pressure."""
    print("Drawing surface pressure line...")
    surf = metadata["surface"]
    sp = surf["sp"]
    skew.ax.axhline(
        sp,
        color="black",
        linestyle=":",
        linewidth=1.5,
        label="Surface Pressure",
        zorder=1
    )


def draw_height_axis(
    skew: SkewT,
    p: np.ndarray,
    z: np.ndarray,
    settings: SkewTPlotSettings
) -> Any:
    """Add a secondary y-axis for height using MetPy for transformations."""
    print(f"Drawing height axis ({settings.height_type})...")

    HEIGHT_OFFSET = 10.0 if settings.height_units == "km" else 10000.0

    p_mag = p.magnitude
    z_mag = z.magnitude
    if settings.height_units == "km":
        z_mag = z_mag / 1000.0

    idx_p = np.argsort(p_mag)
    p_xp = p_mag[idx_p]
    z_fp = z_mag[idx_p]

    def p_to_z(p_vals):
        p_vals = np.atleast_1d(p_vals)
        valid = p_vals > 0
        res = np.full_like(p_vals, np.nan, dtype=np.float64)

        if np.any(valid):
            log_p = np.log(p_vals[valid])
            log_p_xp = np.log(p_xp)
            z_raw = np.interp(log_p, log_p_xp, z_fp)

            h_unit = units.km if settings.height_units == "km" else units.meters

            idx_low = (p_vals[valid] > p_xp[-1])
            if np.any(idx_low):
                z_anchor = z_fp[-1] * h_unit
                p_anchor = p_xp[-1] * units.hPa
                h_anchor_std = mpcalc.pressure_to_height_std(p_anchor)

                target_p = p_vals[valid][idx_low] * units.hPa
                h_std = mpcalc.pressure_to_height_std(target_p)
                h = z_anchor + (h_std - h_anchor_std)
                z_raw[idx_low] = h.to(h_unit).magnitude

            idx_high = (p_vals[valid] < p_xp[0])
            if np.any(idx_high):
                z_anchor = z_fp[0] * h_unit
                p_anchor = p_xp[0] * units.hPa
                h_anchor_std = mpcalc.pressure_to_height_std(p_anchor)

                target_p = p_vals[valid][idx_high] * units.hPa
                h_std = mpcalc.pressure_to_height_std(target_p)
                h = z_anchor + (h_std - h_anchor_std)
                z_raw[idx_high] = h.to(h_unit).magnitude

            res[valid] = z_raw + HEIGHT_OFFSET

        return res

    def z_to_p(z_vals_with_offset):
        z_vals_with_offset = np.atleast_1d(z_vals_with_offset)
        z_vals = z_vals_with_offset - HEIGHT_OFFSET
        res = np.full_like(z_vals, np.nan, dtype=np.float64)

        z_xp_rev = z_fp[::-1]
        log_p_fp_rev = np.log(p_xp)[::-1]

        if np.any(np.diff(z_xp_rev) <= 0):
            sort_idx = np.argsort(z_xp_rev)
            z_xp_rev = z_xp_rev[sort_idx]
            log_p_fp_rev = log_p_fp_rev[sort_idx]

        log_p = np.interp(z_vals, z_xp_rev, log_p_fp_rev)
        h_unit = units.km if settings.height_units == "km" else units.meters

        idx_low = (z_vals < z_xp_rev[0])
        if np.any(idx_low):
            p_anchor = p_xp[-1] * units.hPa
            z_anchor = z_fp[-1] * h_unit
            h_anchor_std = mpcalc.pressure_to_height_std(p_anchor)

            target_z = z_vals[idx_low] * h_unit
            h_std = target_z - z_anchor + h_anchor_std
            p_val = mpcalc.height_to_pressure_std(h_std)
            log_p[idx_low] = np.log(p_val.to(units.hPa).magnitude)

        idx_high = (z_vals > z_xp_rev[-1])
        if np.any(idx_high):
            p_anchor = p_xp[0] * units.hPa
            z_anchor = z_fp[0] * h_unit
            h_anchor_std = mpcalc.pressure_to_height_std(p_anchor)

            target_z = z_vals[idx_high] * h_unit
            h_std = target_z - z_anchor + h_anchor_std
            p_val = mpcalc.height_to_pressure_std(h_std)
            log_p[idx_high] = np.log(p_val.to(units.hPa).magnitude)

        res = np.exp(log_p)
        return res

    ax2 = skew.ax.secondary_yaxis(
        settings.height_axis_location, functions=(p_to_z, z_to_p)
    )

    unit_label = "km" if settings.height_units == "km" else "m"
    height_label = "MSL Altitude" if settings.height_type == "msl" else "Geopotential Height"
    ax2.set_ylabel(f"{height_label} ({unit_label})")

    if settings.height_axis_location == "left":
        ax2.spines["left"].set_position(("outward", settings.height_axis_left_offset))

    def height_formatter(x, pos):
        val = x - HEIGHT_OFFSET
        if val == int(val):
            return f"{int(val)}"
        return f"{val:g}"

    ax2.yaxis.set_major_formatter(FuncFormatter(height_formatter))
    ax2.yaxis.set_minor_formatter(NullFormatter())

    from matplotlib.ticker import FixedLocator
    if settings.extrapolate_height_axis:
        ax2.yaxis.set_major_locator(MultipleLocator(settings.height_tick_interval))
        ax2.yaxis.set_minor_locator(MultipleLocator(settings.height_tick_interval / 2))
    else:
        min_h = (np.ceil(np.nanmin(z_mag) / settings.height_tick_interval) * settings.height_tick_interval) + HEIGHT_OFFSET
        max_h = (np.floor(np.nanmax(z_mag) / settings.height_tick_interval) * settings.height_tick_interval) + HEIGHT_OFFSET
        ticks = np.arange(min_h, max_h + settings.height_tick_interval, settings.height_tick_interval)
        ax2.yaxis.set_major_locator(FixedLocator(ticks))

        minor_ticks = np.arange(min_h, max_h + settings.height_tick_interval, settings.height_tick_interval / 2)
        ax2.yaxis.set_minor_locator(FixedLocator(minor_ticks))

    # Draw manual gridlines workaround
    p_limits = [settings.p_min.magnitude, settings.p_max.magnitude]
    z_at_limits = p_to_z(p_limits)

    if settings.extrapolate_height_axis:
        min_h = np.floor(np.nanmin(z_at_limits) / settings.height_tick_interval) * settings.height_tick_interval
        max_h = np.ceil(np.nanmax(z_at_limits) / settings.height_tick_interval) * settings.height_tick_interval
    else:
        min_h = (np.ceil(np.nanmin(z_mag) / settings.height_tick_interval) * settings.height_tick_interval) + HEIGHT_OFFSET
        max_h = (np.floor(np.nanmax(z_mag) / settings.height_tick_interval) * settings.height_tick_interval) + HEIGHT_OFFSET

    h_ticks = np.arange(min_h, max_h + settings.height_tick_interval, settings.height_tick_interval)

    for h in h_ticks:
        p_val_arr = z_to_p(h)
        p_val = p_val_arr[0]

        if not np.isnan(p_val) and p_val >= 10:
            skew.ax.axhline(p_val, color='pink', linestyle='--', alpha=0.5, zorder=1)

    return ax2


def draw_skewt(
    fig: plt.Figure,
    p: np.ndarray,
    T: np.ndarray,
    Td: np.ndarray,
    u: np.ndarray,
    v: np.ndarray,
    metadata: dict,
    settings: SkewTPlotSettings
) -> SkewT:
    """Draw the Skew-T plot component."""
    print("Drawing Skew-T...")
    skew = SkewT(fig, rotation=settings.skew_rotation, rect=settings.skewt_rect)
    skew.ax.set_anchor("NE")

    skew.plot(p, T.to("degC"), "r", marker=".", linewidth=2, label="Temperature")
    skew.plot(p, Td.to("degC"), "g", marker=".", linewidth=2, label="Dewpoint")

    skew.ax.set_ylabel("Pressure (hPa)")
    skew.ax.set_xlabel("Temperature (°C)")

    curr_x_ticks = skew.ax.get_xticks()
    new_x_ticks = np.arange(
        np.min(curr_x_ticks), np.max(curr_x_ticks) + 1, settings.temp_resolution
    )
    skew.ax.set_xticks(new_x_ticks)

    new_y_ticks = np.arange(
        settings.p_min.magnitude, settings.p_max.magnitude + 1, settings.p_resolution
    )
    skew.ax.set_yticks(new_y_ticks)

    interval = np.where(p >= settings.p_min)[0][::settings.barbs_interval]
    skew.plot_barbs(p[interval], u[interval], v[interval],
                    xloc=1 - settings.bard_offset)

    new_x_ticks_units = new_x_ticks * units.degC
    skew.plot_dry_adiabats(
        t0=new_x_ticks_units,
        label="Dry Adiabats",
        colors=settings.dry_adiabat_color,
        alpha=settings.adiabat_alpha,
        linestyle=settings.adiabat_linestyle,
    )
    skew.plot_moist_adiabats(
        t0=new_x_ticks_units,
        label="Moist Adiabats",
        colors=settings.moist_adiabat_color,
        alpha=settings.adiabat_alpha,
        linestyle=settings.adiabat_linestyle,
    )
    skew.plot_mixing_lines(
        label="Mixing Ratio Lines", alpha=settings.mixing_ratio_alpha
    )

    skew.ax.set_ylim(settings.p_max, settings.p_min)
    skew.ax.set_xlim(settings.t_min, settings.t_max)

    if settings.show_height_axis:
        draw_height_axis(skew, p, metadata["profile_z"], settings)

    valid_time_str = np.datetime_as_string(metadata["valid_time"], unit="m")
    skew.ax.set_title(
        f"HRRR Skew-T Profile\n"
        f"Analysis at: {valid_time_str}\n"
        f"Lat: {metadata['lat']:.4f} and Lon: {metadata['lon']:.4f}\n",
        loc="left",
    )

    if not settings.legend_outside:
        skew.ax.legend(loc=settings.legend_loc)

    return skew


def draw_hodograph(
    p: np.ndarray,
    u: np.ndarray,
    v: np.ndarray,
    settings: SkewTPlotSettings
) -> Any:
    """Draw the Hodograph and its colorbar."""
    print("Drawing Hodograph...")
    ax_hod = plt.axes(settings.hodo_rect)
    ax_hod.set_anchor("N")
    h = Hodograph(ax_hod, component_range=settings.wind_max)
    h.add_grid(increment=5)

    lc = h.plot_colormapped(
        u.to("m/s").magnitude, v.to("m/s").magnitude, p, cmap="copper_r", linewidth=3
    )
    ax_hod.set_xlabel("u (m/s)")
    ax_hod.set_ylabel("v (m/s)")

    cax = plt.axes(settings.hodo_cb_rect)
    plt.colorbar(
        lc, cax=cax, orientation="horizontal", label="Pressure (hPa)", pad=0.05
    )
    return ax_hod


def plot_skewt_hodograph(
    p: np.ndarray,
    T: np.ndarray,
    Td: np.ndarray,
    u: np.ndarray,
    v: np.ndarray,
    metadata: dict,
    settings: Optional[SkewTPlotSettings] = None,
    mixing_results: Optional[dict] = None,
    inversion_layers: Optional[dict] = None
) -> str:
    """
    Main orchestration function to create and save the Skew-T / Hodograph plot.
    """
    if settings is None:
        print("Notification: Using default SkewTPlotSettings.")
        settings = SkewTPlotSettings()

    print("Generating full Skew-T/Hodograph plot...")
    fig = plt.figure(figsize=settings.figsize)

    if settings.show_debug_rects:
        add_debug_patches(fig, settings)

    # Draw components
    skew = draw_skewt(fig, p, T, Td, u, v, metadata, settings)
    draw_surface_conditions(skew, metadata, settings)
    draw_sp(skew, metadata)
    draw_hodograph(p, u, v, settings)

    if mixing_results is not None:
        draw_mixing_height(skew, p, metadata, mixing_results)

    if inversion_layers is not None:
        draw_inversion_layer(skew, p, inversion_layers, settings)

    if settings.legend_outside:
        print("Placing legend outside in bottom right of figure...")
        fig.legend(loc="lower right", bbox_to_anchor=settings.legend_anchor)

    save_dir = settings.save_dir if settings else "./skewt_spot"
    os.makedirs(save_dir, exist_ok=True)
    filename = (settings.save_filename if settings else None) or "hrrr_skewt.png"
    save_path = os.path.join(save_dir, filename)
    plt.savefig(save_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Skew-T plot saved to: {save_path}")
    
    return save_path
