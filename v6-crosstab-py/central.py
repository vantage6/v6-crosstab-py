"""
This file contains all central algorithm functions. It is important to note
that the central method is executed on a node, just like any other method.

The results in a return statement are sent to the vantage6 server (after
encryption if that is enabled).
"""

from typing import Any
from io import StringIO
import pandas as pd
import scipy

from vantage6.algorithm.tools.util import info
from vantage6.algorithm.tools.decorators import algorithm_client
from vantage6.algorithm.client import AlgorithmClient


@algorithm_client
def central_crosstab(
    client: AlgorithmClient,
    results_col: str,
    group_cols: list[str],
    organizations_to_include: list[int] = None,
    include_chi2: bool = True,
    include_totals: bool = True,
) -> Any:
    """
    Central part of the algorithm

    Parameters
    ----------
    client : AlgorithmClient
        The client object used for communication with the server.
    results_col : str
        The column for which counts are calculated
    group_cols : list[str]
        List of one or more columns to group the data by.
    organizations_to_include : list[int], optional
        List of organization ids to include in the computation. If not provided, all
        organizations in the collaboration are included.
    include_chi2 : bool, optional
        Whether to include the chi-squared statistic in the results.
    include_totals : bool, optional
        Whether to include totals in the contingency table.
    """
    # get all organizations (ids) within the collaboration so you can send a
    # task to them.
    if not organizations_to_include:
        organizations = client.organization.list()
        organizations_to_include = [
            organization.get("id") for organization in organizations
        ]

    # Define input parameters for a subtask
    info("Defining input parameters")
    input_ = {
        "method": "partial_crosstab",
        "kwargs": {
            "results_col": results_col,
            "group_cols": group_cols,
        },
    }

    # create a subtask for all organizations in the collaboration.
    info("Creating subtask to compute partial contingency tables")
    task = client.task.create(
        input_=input_,
        organizations=organizations_to_include,
        name="Partial crosstabulation",
        description="Contingency table for each organization",
    )

    # wait for node to return results of the subtask.
    info("Waiting for results")
    results = client.wait_for_results(task_id=task.get("id"))
    info("Results obtained!")

    # return the final results of the algorithm
    return _aggregate_results(results, group_cols, include_chi2, include_totals)


def _aggregate_results(
    results: dict, group_cols: list[str], include_chi2: bool, include_totals: bool
) -> pd.DataFrame:
    """
    Aggregate the results of the partial computations.

    Parameters
    ----------
    results : list[dict]
        List of JSON data containing the partial results.
    group_cols : list[str]
        List of columns that were used to group the data.
    include_chi2 : bool
        Whether to include the chi-squared statistic in the results.
    include_totals : bool
        Whether to include totals in the contingency table.

    Returns
    -------
    pd.DataFrame
        Aggregated results.
    """
    # The results are pandas dictionaries converted to JSON. Convert them back and
    # then add them together to get the final partial_df.
    partial_dfs = []
    for result in results:
        df = pd.read_json(StringIO(result))
        # set group cols as index
        df.set_index(group_cols, inplace=True)
        partial_dfs.append(df)

    # Get all unique values for the result column
    all_result_levels = list(set([col for df in partial_dfs for col in df.columns]))

    # The partial results are already in the form of a contingency table, but they
    # contain ranges (e.g. "0-5"). These are converted to two columns: one for the
    # minimum value and one for the maximum value.
    converted_results = []
    for partial_df in partial_dfs:
        # expand the ranges to min and max values
        orig_columns = partial_df.columns
        for col in orig_columns:
            if partial_df[col].dtype == "object":
                # if the column contains a range, split it into two columns
                partial_df[[f"{col}_min", f"{col}_max"]] = partial_df[col].str.split(
                    "-", expand=True
                )
                partial_df[f"{col}_max"] = partial_df[f"{col}_max"].fillna(
                    partial_df[f"{col}_min"]
                )
            else:
                # column is already numeric: simply copy it to the new columns
                partial_df[f"{col}_min"] = partial_df[col]
                partial_df[f"{col}_max"] = partial_df[col]
        # drop the original columns
        partial_df.drop(columns=orig_columns, inplace=True)
        # convert to numeric
        partial_df = partial_df.apply(pd.to_numeric).astype(int)
        converted_results.append(partial_df)

    # We now have a list of partial results that contain minimum and maximum values
    # for each cell in the contingency table. We can now add them together to get the
    # final result.
    aggregated_df = pd.concat(converted_results).fillna(0).astype(int)
    aggregated_df = aggregated_df.groupby(aggregated_df.index).sum()

    # above groupby puts multiindex groupby into tuples, which we need to unpack
    if len(group_cols) > 1:
        aggregated_df.index = pd.MultiIndex.from_tuples(
            aggregated_df.index, names=group_cols
        )

    min_colnames = [f"{col}_min" for col in orig_columns]
    max_colnames = [f"{col}_max" for col in orig_columns]
    # Compute chi-squared statistic
    if include_chi2:
        chi2, chi2_pvalue = compute_chi_squared(
            aggregated_df, min_colnames, max_colnames
        )

    if include_totals:
        col_totals, row_totals, total_total = _compute_totals(
            aggregated_df, min_colnames, max_colnames
        )

    # Convert back to strings so that we can add ranges
    aggregated_df = aggregated_df.astype(str)

    # Finally, we need to combine the min and max values back into ranges
    min_max_cols = aggregated_df.columns
    for level in all_result_levels:
        aggregated_df[level] = _concatenate_min_max(
            aggregated_df[f"{level}_min"], aggregated_df[f"{level}_max"]
        )

    # clean up: drop the min and max columns
    aggregated_df.drop(min_max_cols, axis=1, inplace=True)

    # reset index to pass the group columns along to results
    aggregated_df = aggregated_df.reset_index()

    # add totals ranges
    if include_totals:
        aggregated_df["Total"] = row_totals
        aggregated_df.loc[len(aggregated_df)] = (
            ["Total"]
            + ["" for _ in group_cols[1:]]
            + col_totals.tolist()
            + [total_total]
        )

    results = {"contingency_table": aggregated_df.to_json(orient="records")}
    if include_chi2:
        results.update({"chi2": {"chi2": chi2, "P-value": chi2_pvalue}})
    return results


def compute_chi_squared(
    contingency_table: pd.DataFrame, min_colnames: list[str], max_colnames: list[str]
) -> tuple[str]:
    """
    Compute chi squared statistic based on the contingency table

    Parameters
    ----------
    contingency_table : pd.DataFrame
        The contingency table.
    min_colnames : list[str]
        List of column names for the minimum values of each range.
    max_colnames : list[str]
        List of column names for the maximum values of each range.

    Returns
    -------
    tuple[str]
        Tuple containing the chi-squared statistics and pvalues. If the contingency
        table contains ranges, the statistics and pvalues are also returned as a range.
    """
    info("Computing chi-squared statistic...")

    # for minimum values, remove rows with only zeros
    min_df = contingency_table[min_colnames]
    min_df = min_df.loc[(min_df != 0).any(axis=1)]
    max_df = contingency_table[max_colnames]

    chi2_min = scipy.stats.chi2_contingency(min_df)
    chi2_max = scipy.stats.chi2_contingency(max_df)

    if chi2_min.statistic == chi2_max.statistic:
        return str(chi2_min.statistic), str(chi2_min.pvalue)

    # note that if giving a range, MAX goes before MIN, because the values of the
    # statistic are actually larger for the minimum side of the range, because then the
    # difference with the average is larger than for the maximum side of the range
    # (p-value is not reversed as that is again the reverse of the statistic :-))
    return (
        f"{chi2_max.statistic} - {chi2_min.statistic}",
        f"{chi2_min.pvalue} - {chi2_max.pvalue}",
    )


def _compute_totals(
    contingency_table: pd.DataFrame, min_colnames: list[str], max_colnames: list[str]
) -> tuple:
    """
    Compute the totals for the contingency table.

    Parameters
    ----------
    contingency_table : pd.DataFrame
        The contingency table.
    min_colnames : list[str]
        List of column names for the minimum values of each range.
    max_colnames : list[str]
        List of column names for the maximum values of each range.

    Returns
    -------
    tuple
        Tuple containing the column totals, row totals, and the sum of all data points.
    """
    # Add totals
    min_row_totals = contingency_table[min_colnames].sum(axis=1)
    min_col_totals = contingency_table[min_colnames].sum(axis=0)
    max_row_totals = contingency_table[max_colnames].sum(axis=1)
    max_col_totals = contingency_table[max_colnames].sum(axis=0)

    min_total_total = min_row_totals.sum()
    max_total_total = max_row_totals.sum()
    if min_total_total != max_total_total:
        total_total = f"{min_total_total} - {max_total_total}"
    else:
        total_total = str(min_total_total)

    min_row_totals = min_row_totals.astype(str).reset_index(drop=True)
    min_col_totals = min_col_totals.astype(str).reset_index(drop=True)
    max_row_totals = max_row_totals.astype(str).reset_index(drop=True)
    max_col_totals = max_col_totals.astype(str).reset_index(drop=True)

    # check if the totals are the same
    col_totals = _concatenate_min_max(min_col_totals, max_col_totals)
    row_totals = _concatenate_min_max(min_row_totals, max_row_totals)
    return col_totals, row_totals, total_total


def _concatenate_min_max(min_col: pd.Series, max_col: pd.Series) -> pd.Series:
    """
    Concatenate two columns into a single column with ranges.

    Parameters
    ----------
    min_col : pd.Series
        The column with minimum values.
    max_col : pd.Series
        The column with maximum values.

    Returns
    -------
    pd.Series
        The concatenated column.
    """
    # first, simply concatenate the columns
    result = min_col + "-" + max_col
    # then, remove extra text where min and max are the same
    min_max_same = min_col == max_col
    result.loc[min_max_same] = result.loc[min_max_same].str.replace(
        r"-(\d+)", "", regex=True
    )
    return result
