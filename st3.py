"""
Canopy GSM for Python
Version: 1.0.0 (development implementation)

ST3 compatibility implementation for Canopy GSM MATLAB v2.1.

MIT License
Copyright (c) 2026 Abbas Haghshenas
"""

from __future__ import annotations

import numpy as np


def st3_reference(datavect, m: int = 12, p: int = 50) -> np.ndarray:
    """Translate ST3.m while preserving MATLAB empty-cell semantics.

    None represents an empty MATLAB cell. Numeric NaN is retained as a
    present value, matching length(cell2mat(...)) ~= 0.
    """
    if not isinstance(m, (int, np.integer)) or not isinstance(p, (int, np.integer)):
        raise ValueError("m and p must be integers")
    if m < 0 or p < 0:
        raise ValueError("m and p must be non-negative integers")

    vect = list(datavect)
    n = len(vect)
    if n == 0:
        return np.zeros(0, dtype=np.int16)

    def present(value) -> bool:
        return value is not None

    def number(value) -> float:
        return float(value)

    # Find imax exactly in the MATLAB control flow. If the current imax cell
    # is empty, MATLAB assigns imax=i even when the current cell is also empty.
    imax = 0
    for i in range(n):
        if present(vect[imax]):
            if present(vect[i]) and number(vect[i]) > number(vect[imax]):
                imax = i
        else:
            imax = i

    result = np.zeros(n, dtype=np.int16)

    for i in range(n):
        if not present(vect[i]):
            result[i] = 0
            continue

        i_matlab = i + 1

        if i_matlab <= m:
            before_cells = vect[0:i + 1]
            after_cells = vect[i:i + m + 1]
        elif i_matlab > n - m:
            before_cells = vect[i - m:i + 1]
            after_cells = vect[i:n]
        else:
            before_cells = vect[i - m:i + 1]
            after_cells = vect[i:i + m + 1]

        # cell2mat removes empty cells but retains numeric NaN.
        before = np.asarray(
            [number(v) for v in before_cells if present(v)],
            dtype=np.float64,
        )
        after = np.asarray(
            [number(v) for v in after_cells if present(v)],
            dtype=np.float64,
        )

        before2 = before < 1
        after2 = after < 1

        if (
            (before2.sum() == len(before2) and len(before2) > m)
            or (after2.sum() == len(after2) and len(after2) > m)
        ):
            result[i] = 2
            continue

        before3 = before >= 1
        after3 = after >= 1

        if (
            (len(before2) > m and before3.sum() == len(before3))
            or (after3.sum() == len(after3) and len(after2) > m)
            or (i_matlab == imax + 1)
        ):
            result[i] = 4
        elif (
            (i_matlab > p)
            and (i_matlab < imax + 1)
            and before3.sum() >= 1
            and after3.sum() >= 1
            and not (after3.sum() == len(after3))
            and len(before2) > m
            and len(after2) > m
        ):
            result[i] = 3
        elif i_matlab > p:
            result[i] = 5
        else:
            result[i] = 1

    return result
