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

PRIVACY_THRESHOLD = 5


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
        df.groupby(group_cols + results_col, dropna=False)[results_col]
        .count()
        .unstack(level=results_col)
        # TODO get rid of copy?
        .copy()
    )

    # TODO Check that all values are higher than the threshold
    # TODO if no values are higher than the threshold, return an error
    print(cross_tab_df)

    return cross_tab_df
