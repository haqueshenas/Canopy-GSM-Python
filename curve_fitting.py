"""
Canopy GSM for Python
Version: 1.0.0 (development implementation)

Curve fitting interface for the GSM v2.1 reference workflow.

The GSM reference model is:

    y = a * exp(b * x)

The MATLAB v2.1 reference implementation uses:

    fit(x, y, 'exp1', fo)

with nonlinear least squares and the model:

    y = a * exp(b * x)

This Python implementation uses a profiled nonlinear least-squares
solution. For a fixed b, the optimal amplitude a is obtained
analytically. The remaining one-dimensional problem is then solved
numerically.

The implementation is designed for numerical stability and for
reproducible comparison against the MATLAB v2.1 golden reference.

MIT License
Copyright (c) 2026 Abbas Haghshenas
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize_scalar


@dataclass(frozen=True)
class ExpFitResult:
    a: float
    b: float
    rsquare: float
    rmse: float
    sse: float
    dfe: int
    x: np.ndarray
    y: np.ndarray
    y_fit: np.ndarray
    solver_success: bool
    solver_message: str


def _profile_exp_sse(
    x: np.ndarray,
    y: np.ndarray,
    b: float,
) -> tuple[float, float, np.ndarray]:
    """
    Evaluate the least-squares exponential model for a fixed b.

    Model:

        y = a * exp(b * x)

    For numerical stability, x is centered:

        x = x0 + t

    Therefore:

        y = c * exp(b * t)

    where:

        c = a * exp(b * x0)

    For a fixed b, the least-squares optimum for c is analytical.

    The exponential terms are scaled by their maximum exponent to
    avoid overflow/underflow during the optimization.

    Returns
    -------
    sse : float
        Sum of squared residuals.

    a : float
        Equivalent amplitude in the original model:

            y = a * exp(b*x)

    y_fit : ndarray
        Fitted values corresponding to the input x values.
    """
    x = np.asarray(x, dtype=np.float64).reshape(-1)
    y = np.asarray(y, dtype=np.float64).reshape(-1)

    if x.size == 0:
        return np.inf, np.nan, np.empty(0, dtype=np.float64)

    x0 = float(np.mean(x))
    t = x - x0

    b = float(b)

    q = b * t
    q_max = float(np.max(q))

    # Stable exponential weights:
    #
    # exp(q) = exp(q_max) * exp(q-q_max)
    #
    # Since q-q_max <= 0, the exponential cannot overflow.
    u = np.exp(np.clip(q - q_max, -745.0, 0.0))

    numerator = float(np.sum(y * u))
    denominator = float(np.sum(u * u))

    if (
        not np.isfinite(numerator)
        or not np.isfinite(denominator)
        or denominator <= 0.0
    ):
        return np.inf, np.nan, np.full_like(y, np.nan)

    # This is the amplitude corresponding to the scaled exponential:
    #
    # y_fit = scaled_amplitude * u
    #
    # where:
    #
    # u = exp(b*t - q_max)
    #
    scaled_amplitude = numerator / denominator

    if not np.isfinite(scaled_amplitude):
        return np.inf, np.nan, np.full_like(y, np.nan)

    y_fit = scaled_amplitude * u

    if not np.all(np.isfinite(y_fit)):
        return np.inf, np.nan, np.full_like(y, np.nan)

    residual = y - y_fit
    sse = float(np.sum(residual * residual))

    if not np.isfinite(sse):
        return np.inf, np.nan, np.full_like(y, np.nan)

    # Recover the original coefficient a.
    #
    # scaled_amplitude
    #     = c * exp(q_max)
    #
    # c
    #     = a * exp(b*x0)
    #
    # therefore:
    #
    # a = scaled_amplitude * exp(-q_max) * exp(-b*x0)
    #
    log_scale = -q_max - (b * x0)

    if log_scale > 709.0:
        a = float("inf")
    elif log_scale < -745.0:
        a = 0.0
    else:
        a = float(scaled_amplitude * np.exp(log_scale))

    if not np.isfinite(a):
        return np.inf, np.nan, np.full_like(y, np.nan)

    return sse, a, y_fit


def _find_b_bracket(
    x: np.ndarray,
    y: np.ndarray,
) -> tuple[float, float]:
    """
    Find a numerical bracket containing the minimum SSE with respect
    to b.

    The previous implementation used a single initial step of 0.01.
    That was unsafe because the MATLAB solution for GSM can lie
    between 0 and 0.01; for example:

        b = 0.008637760918...

    Therefore the present implementation first evaluates a dense
    coarse grid around the physically/numerically relevant region,
    identifies the lowest-SSE point, and then returns neighboring
    grid points as the local optimization bracket.

    The search is symmetric around zero and does not assume in advance
    that b must be positive.

    Returns
    -------
    b_lo, b_hi : float
        Lower and upper bounds surrounding the best coarse-grid point.
    """
    x = np.asarray(x, dtype=np.float64).reshape(-1)
    y = np.asarray(y, dtype=np.float64).reshape(-1)

    # GSM Green levels are 1..255. For this data scale, the MATLAB
    # exp1 solutions are small positive values, typically around
    # 0.005--0.02. The initial search therefore resolves this region
    # finely rather than jumping in 0.01 increments.
    coarse_b = np.linspace(-0.05, 0.05, 2001)

    sse_values = np.empty(coarse_b.size, dtype=np.float64)

    for i, b in enumerate(coarse_b):
        sse_values[i] = _profile_exp_sse(x, y, float(b))[0]

    finite = np.isfinite(sse_values)

    if not np.any(finite):
        raise RuntimeError(
            "Could not evaluate a finite exponential-fit SSE over "
            "the initial b search range."
        )

    # Replace non-finite values by +inf so they cannot be selected.
    safe_sse = np.where(
        finite,
        sse_values,
        np.inf,
    )

    best_index = int(np.argmin(safe_sse))

    # If the best point is internal, use its immediate neighbors.
    if 0 < best_index < coarse_b.size - 1:
        return (
            float(coarse_b[best_index - 1]),
            float(coarse_b[best_index + 1]),
        )

    # If the minimum appears at an edge, expand the search range.
    # This is deliberately conservative; it is not expected for the
    # current GSM reference images.
    if best_index == 0:
        return -0.10, float(coarse_b[1])

    return float(coarse_b[-2]), 0.10


def fit_exp1(x, y) -> ExpFitResult:
    """
    Fit the GSM reference exponential model:

        y = a * exp(b * x)

    after removing undefined observations.

    MATLAB v2.1 reference:

        fit(x, y, 'exp1', fo)

    with:

        StartPoint   = [1, 1]
        Algorithm    = 'Trust-Region'
        DiffMinChange = 1e-8
        DiffMaxChange = 0.1
        MaxFunEvals  = 600
        MaxIter      = 400
        TolFun       = 1e-6
        TolX         = 1e-6

    This function preserves the same scientific model and least-squares
    objective. The numerical implementation is profiled in b so that
    the optimization remains stable for Green-level x values extending
    to 255.
    """
    x_arr = np.asarray(x, dtype=np.float64).reshape(-1)
    y_arr = np.asarray(y, dtype=np.float64).reshape(-1)

    # MATLAB ExpFitting removes NaN values from Y and the corresponding
    # X observations.
    valid = np.isfinite(x_arr) & np.isfinite(y_arr)

    x_arr = x_arr[valid]
    y_arr = y_arr[valid]

    if x_arr.size < 3:
        raise ValueError(
            "Exponential fitting requires at least 3 valid observations."
        )

    # ------------------------------------------------------------
    # Step 1 — find a reliable local bracket for b
    # ------------------------------------------------------------
    b_lo, b_hi = _find_b_bracket(
        x_arr,
        y_arr,
    )

    if (
        not np.isfinite(b_lo)
        or not np.isfinite(b_hi)
        or b_lo >= b_hi
    ):
        raise RuntimeError(
            "Could not determine a valid search interval for "
            "exponential fitting."
        )

    # ------------------------------------------------------------
    # Step 2 — refine b by minimizing the profiled SSE
    # ------------------------------------------------------------
    result = minimize_scalar(
        lambda b: _profile_exp_sse(
            x_arr,
            y_arr,
            float(b),
        )[0],
        bounds=(b_lo, b_hi),
        method="bounded",
        options={
            "xatol": 1e-13,
            "maxiter": 1000,
        },
    )

    if not np.isfinite(result.x):
        raise RuntimeError(
            "Exponential fitting produced a non-finite b coefficient."
        )

    b = float(result.x)

    # ------------------------------------------------------------
    # Step 3 — calculate the final fitted amplitude and curve
    # ------------------------------------------------------------
    sse_profile, a, y_fit_profile = _profile_exp_sse(
        x_arr,
        y_arr,
        b,
    )

    if not np.isfinite(sse_profile):
        raise RuntimeError(
            "Exponential fitting produced a non-finite SSE."
        )

    if not np.isfinite(a):
        raise RuntimeError(
            "Exponential fitting produced a non-finite amplitude."
        )

    # Evaluate the model in the original parameterization.
    exponent = np.clip(
        b * x_arr,
        -745.0,
        709.0,
    )

    y_fit_original = a * np.exp(exponent)

    if np.all(np.isfinite(y_fit_original)):
        y_fit = y_fit_original
    else:
        y_fit = y_fit_profile

    # ------------------------------------------------------------
    # Step 4 — MATLAB-compatible goodness-of-fit statistics
    # ------------------------------------------------------------
    residual = y_arr - y_fit

    sse = float(np.sum(residual * residual))

    if not np.isfinite(sse):
        raise RuntimeError(
            "Exponential fitting produced a non-finite final SSE."
        )

    mean_y = float(np.mean(y_arr))

    sst = float(
        np.sum(
            (y_arr - mean_y) ** 2
        )
    )

    if sst > 0.0:
        rsquare = float(
            1.0 - sse / sst
        )
    else:
        rsquare = np.nan

    dfe = int(
        x_arr.size - 2
    )

    if dfe > 0:
        rmse = float(
            np.sqrt(
                sse / dfe
            )
        )
    else:
        rmse = np.nan

    return ExpFitResult(
        a=float(a),
        b=b,
        rsquare=rsquare,
        rmse=rmse,
        sse=sse,
        dfe=dfe,
        x=x_arr,
        y=y_arr,
        y_fit=y_fit,
        solver_success=bool(
            result.success
        ),
        solver_message=(
            "Profiled nonlinear least-squares exponential fit; "
            f"{result.message}"
        ),
    )
