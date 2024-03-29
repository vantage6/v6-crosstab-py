"""
This file contains all partial algorithm functions, that are normally executed
on all nodes for which the algorithm is executed.

The results in a return statement are sent to the vantage6 server (after
encryption if that is enabled). From there, they are sent to the partial task
or directly to the user (if they requested partial results).
"""

import pandas as pd
from typing import Any

from vantage6.algorithm.tools.util import info, warn, error
from vantage6.algorithm.tools.decorators import data

# TODO decide if/how this should be settable
from .globals import PRIVACY_THRESHOLD, BELOW_THRESHOLD_PLACEHOLDER


@data(1)
def partial_crosstab(
    df: pd.DataFrame,
    results_col: str,
    group_cols: list[str],
) -> Any:
    """
    Decentral part of the algorithm

    Parameters
    ----------
    df : pd.DataFrame
        The dataframe containing the data.
    results_col : str
        The column for which counts are calculated
    group_cols : list[str]
        List of one or more columns to group the data by.
    """
    # TODO check that results col + group cols are categorical

    # Fill empty (categorical) values with "N/A"
    df = df.fillna("N/A")

    # Create contingency table
    cross_tab_df = (
        df.groupby(group_cols + [results_col], dropna=False)[results_col]
        .count()
        .unstack(level=results_col)
        .fillna(0)
        .astype(int)
    )

    # if no values are higher than the threshold, return an error
    if not (cross_tab_df > PRIVACY_THRESHOLD).any().any():
        raise ValueError(
            "No values in the contingency table are higher than the privacy threshold "
            f"of {PRIVACY_THRESHOLD}. Please check if you submitted categorical "
            "variables - if you did, there may simply not be enough data at this node."
        )

    # TODO is a value of zero allowed?
    # TODO > or >= to threshold? Otherwise placeholder should also be changed
    # Replace too low values with a privacy-preserving value
    if PRIVACY_THRESHOLD > 0:
        cross_tab_df.where(cross_tab_df > PRIVACY_THRESHOLD, 0, inplace=True)

    # Cast to string to ensure it can be read again. Also, set zero values to ranges
    # indicating that the value is below the threshold
    cross_tab_df = cross_tab_df.astype(str).where(
        cross_tab_df > PRIVACY_THRESHOLD, BELOW_THRESHOLD_PLACEHOLDER
    )
    # reset index to ensure that groups are passed along to central part
    cross_tab_df = cross_tab_df.reset_index()

    # Cast results to string to ensure they can be read again
    return cross_tab_df.astype(str).to_json(orient="records")
