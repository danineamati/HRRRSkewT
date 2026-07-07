from typing import Optional, Any
import numpy as np
import metpy.calc as mpcalc
import metpy.interpolate as mpinterpolate
from metpy.units import units

def calculate_inversion_layer(p: np.ndarray, T: np.ndarray, z: np.ndarray) -> dict:
    """Identify inversion layer where temperature increases with height."""
    print("Calculating inversion layers...")
    dT_by_dp = mpcalc.first_derivative(T, x=p)
    inversion_mask = dT_by_dp < 0

    inversion_layers = {
        "inversion_pressure": p[inversion_mask],
        "inversion_temperature": T[inversion_mask],
        "inversion_height": z[inversion_mask]
    }
    return inversion_layers


def report_inversion_layer(inversion_layers: dict, banner_num: int = 50) -> None:
    """Print the inversion layer results in a readable format."""
    if len(inversion_layers["inversion_pressure"]) == 0:
        print("No inversion layers detected.")
        return

    print("\n" + "=" * banner_num)
    print("       INVERSION LAYER REPORT")
    print("=" * banner_num)
    for i, (p_inv, T_inv, z_inv) in enumerate(zip(
        inversion_layers["inversion_pressure"],
        inversion_layers["inversion_temperature"],
        inversion_layers["inversion_height"]
    )):
        print(f"Inversion {i+1}:")
        print(f"  Pressure: {p_inv: .2f}")
        print(f"  Temperature: {T_inv.to('degC'): .2f}")
        print(f"  Height: {z_inv: .2f}")
    print("=" * banner_num + "\n")


def calculate_mixing_level(
    p: np.ndarray,
    T: np.ndarray,
    u: np.ndarray,
    v: np.ndarray,
    z: np.ndarray,
    metadata: dict,
    offset: Optional[Any] = 5.0 * units.delta_degC
) -> Optional[dict]:
    """
    Calculate the mixing height using the parcel method (dry adiabat intersection).

    Parameters:
        p, T, u, v: Profile arrays (with units)
        z: Height profile array (with units)
        metadata: Metadata dictionary containing surface conditions
        offset: Temperature offset to add to surface temperature

    Returns:
        Dictionary with mixing level parameters or None if no intersection is found.
    """
    print(f"Calculating mixing height with temperature offset: {offset}...")

    surf = metadata["surface"]
    sp = surf["sp"]
    t2m = surf["t2m"]

    # 1. Parcel profile (dry adiabat only)
    Tp = mpcalc.dry_lapse(p, t2m + offset, reference_pressure=sp)

    # 2. Find intersection with environmental temperature profile T
    # Use log_x=True because pressure is logarithmic in the atmosphere
    intersect_pt = mpcalc.find_intersections(p, Tp, T, log_x=True)

    if len(intersect_pt) == 0 or len(intersect_pt[0]) == 0:
        print("No mixing height intersection found within the profile.")
        return None

    # Take the first intersection above the surface (may or may not be
    # the highest pressure). Since p is sorted from low altitude (high P) to
    # high altitude (low P), find_intersections returns them in that order.
    mixing_p = intersect_pt[0][0]
    if len(intersect_pt[0]) > 1:
        print(f"Multiple intersections found at pressures: {intersect_pt[0]}")
        for p_val in intersect_pt[0]:
            if p_val > sp:
                mixing_p = p_val
                break

    # 3. Interpolate height, temperature, and wind at the intersection pressure
    mixing_z = mpinterpolate.interpolate_1d(mixing_p, p, z)
    mixing_t = mpinterpolate.interpolate_1d(mixing_p, p, T)
    mixing_u = mpinterpolate.interpolate_1d(mixing_p, p, u)
    mixing_v = mpinterpolate.interpolate_1d(mixing_p, p, v)

    mixing_speed = mpcalc.wind_speed(mixing_u, mixing_v)
    mixing_direction = mpcalc.wind_direction(mixing_u, mixing_v)

    return {
        "offset": offset,
        "pressure": mixing_p,
        "height": mixing_z[0],
        "temperature": mixing_t[0],
        "u": mixing_u[0],
        "v": mixing_v[0],
        "speed": mixing_speed[0],
        "direction": mixing_direction[0]
    }


def report_mixing_level(results: Optional[dict], banner_num: int = 50) -> None:
    """Print the mixing level results in a readable format."""
    if results is None:
        print("Mixing height could not be determined.")
        return

    print("\n" + "=" * banner_num)
    print("       MIXING HEIGHT REPORT")
    print("=" * banner_num)
    print(f"Parcel T_Offset: {results['offset']: .2f}")
    print(f"Pressure:        {results['pressure']: .2f}")
    print(f"Height:          {results['height']: .2f}")
    print(f"Temperature:     {results['temperature'].to('degC'): .2f}")
    print(f"Wind Speed:      {results['speed']: .2f}")
    print(f"Wind U:          {results['u']: .2f}")
    print(f"Wind V:          {results['v']: .2f}")
    print(f"Wind Direction:  {results['direction']: .1f}")
    print("=" * banner_num + "\n")
