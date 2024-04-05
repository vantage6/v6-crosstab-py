"""
This file contains all partial algorithm functions, that are normally executed
on all nodes for which the algorithm is executed.

The results in a return statement are sent to the vantage6 server (after
encryption if that is enabled). From there, they are sent to the partial task
or directly to the user (if they requested partial results).
"""

import os
import pandas as pd
from typing import Any

from vantage6.algorithm.tools.util import info, warn, error
from vantage6.algorithm.tools.decorators import data
from vantage6.algorithm.tools.util import get_env_var

from .globals import (
    DEFAULT_PRIVACY_THRESHOLD,
    DEFAULT_MINIMUM_ROWS_TOTAL,
    DEFAULT_ALLOW_ZERO,
)


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
    # get environment variables with privacy settings
    # pylint: disable=invalid-name
    PRIVACY_THRESHOLD = _convert_envvar_to_int(
        "CROSSTAB_PRIVACY_THRESHOLD", DEFAULT_PRIVACY_THRESHOLD
    )
    MINIMUM_ROWS_TOTAL = _convert_envvar_to_int(
        "CROSSTAB_MINIMUM_ROWS_TOTAL", DEFAULT_MINIMUM_ROWS_TOTAL
    )
    ALLOW_ZERO = _convert_envvar_to_bool("CROSSTAB_ALLOW_ZERO", DEFAULT_ALLOW_ZERO)

    # check if env var values are compatible
    info("Checking privacy settings before starting...")
    _do_prestart_privacy_checks(df, PRIVACY_THRESHOLD, ALLOW_ZERO, MINIMUM_ROWS_TOTAL)

    # Fill empty (categorical) values with "N/A"
    df = df.fillna("N/A")

    # Create contingency table
    info("Creating contingency table...")
    cross_tab_df = (
        df.groupby(group_cols + [results_col], dropna=False)[results_col]
        .count()
        .unstack(level=results_col)
        .fillna(0)
        .astype(int)
    )
    info("Contingency table created!")

    # if no values are higher than the threshold, return an error
    if not (cross_tab_df >= PRIVACY_THRESHOLD).any().any():
        raise ValueError(
            "No values in the contingency table are higher than the privacy threshold "
            f"of {PRIVACY_THRESHOLD}. Please check if you submitted categorical "
            "variables - if you did, there may simply not be enough data at this node."
        )

    # Replace too low values with a privacy-preserving value
    info("Replacing values below threshold with privacy-enhancing values...")
    replace_value = 1 if ALLOW_ZERO else 0
    replace_condition = (
        (cross_tab_df >= PRIVACY_THRESHOLD) & (cross_tab_df == 0)
        if ALLOW_ZERO
        else (cross_tab_df >= PRIVACY_THRESHOLD)
    )
    cross_tab_df.where(replace_condition, replace_value, inplace=True)

    # Cast to string and set non-privacy-preserving values to a placeholder indicating
    # that the value is below the threshold
    BELOW_THRESHOLD_PLACEHOLDER = _get_threshold_placeholder(
        PRIVACY_THRESHOLD, ALLOW_ZERO
    )
    cross_tab_df = cross_tab_df.astype(str).where(
        replace_condition, BELOW_THRESHOLD_PLACEHOLDER
    )
    # reset index to ensure that groups are passed along to central part
    cross_tab_df = cross_tab_df.reset_index()

    # Cast results to string to ensure they can be read again
    info("Returning results!")
    return cross_tab_df.astype(str).to_json(orient="records")


def _do_prestart_privacy_checks(
    df: pd.DataFrame, privacy_threshold: int, allow_zero: bool, minimum_rows_total: int
) -> None:
    """
    Perform privacy checks before starting the computation.

    Parameters
    ----------
    df : pd.DataFrame
        The dataframe containing the data.
    privacy_threshold : int
        The privacy threshold value.
    allow_zero : bool
        The flag indicating whether zero values are allowed.
    minimum_rows_total : int
        The minimum number of rows to be found in the supplied dataframe.
    """

    if privacy_threshold == 0 and not allow_zero:
        raise ValueError(
            "Privacy threshold is set to 0, but zero values are not allowed. This "
            "directly contradicts each other - please change one of the settings."
        )

    # Check if dataframe contains enough rows
    if len(df) < minimum_rows_total:
        raise ValueError(
            f"Dataframe contains less than {minimum_rows_total} rows. Refusing to "
            "handle this computation, as it may lead to privacy issues."
        )


def _get_threshold_placeholder(privacy_threshold: int, allow_zero: bool) -> str:
    """
    Get the below threshold placeholder based on the privacy threshold and allow zero flag.

    Parameters
    ----------
    privacy_threshold : int
        The privacy threshold value.
    allow_zero : bool
        The flag indicating whether zero values are allowed.

    Returns
    -------
    str
        The below threshold placeholder.
    """
    if allow_zero:
        if privacy_threshold > 2:
            return f"1-{privacy_threshold-1}"
        else:
            return "1"
    else:
        if privacy_threshold > 1:
            return f"0-{privacy_threshold-1}"
        else:
            return "0"


def _convert_envvar_to_bool(envvar_name: str, default: str) -> bool:
    """
    Convert an environment variable to a boolean value.

    Parameters
    ----------
    envvar_name : str
        The environment variable name to convert.
    default : str
        The default value to use if the environment variable is not set.

    Returns
    -------
    bool
        The boolean value of the environment variable.
    """
    envvar = get_env_var(envvar_name, default).lower()
    if envvar in ["true", "1", "yes", "t"]:
        return True
    elif envvar in ["false", "0", "no", "f"]:
        return False
    else:
        raise ValueError(
            f"Environment variable '{envvar_name}' has value '{envvar}' which cannot be"
            " converted to a boolean value. Please use 'false' or 'true'."
        )


def _convert_envvar_to_int(envvar_name: str, default: str) -> int:
    """
    Convert an environment variable to an integer value.

    Parameters
    ----------
    envvar_name : str
        The environment variable name to convert.
    default : str
        The default value to use if the environment variable is not set.

    Returns
    -------
    int
        The integer value of the environment variable.
    """
    envvar = get_env_var(envvar_name, default)
    error_msg = (
        f"Environment variable '{envvar_name}' has value '{envvar}' which cannot be "
        "converted to a positive integer value."
    )
    try:
        envvar = int(envvar)
    except ValueError as exc:
        raise ValueError(error_msg) from exc
    if envvar < 0:
        raise ValueError(error_msg)
    return envvar
