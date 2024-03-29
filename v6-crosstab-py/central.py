"""
This file contains all central algorithm functions. It is important to note
that the central method is executed on a node, just like any other method.

The results in a return statement are sent to the vantage6 server (after
encryption if that is enabled).
"""

from typing import Any
import pandas as pd
from io import StringIO

from vantage6.algorithm.tools.util import info
from vantage6.algorithm.tools.decorators import algorithm_client
from vantage6.algorithm.client import AlgorithmClient


@algorithm_client
def central_crosstab(
    client: AlgorithmClient,
    results_col: str,
    group_cols: list[str],
    organizations_to_include: list[int] = None,
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
    print(results)
    info("Results obtained!")

    # return the final results of the algorithm
    return _aggregate_results(results, group_cols)


def _aggregate_results(results: dict, group_cols: list[str]) -> pd.DataFrame:
    """
    Aggregate the results of the partial computations.

    Parameters
    ----------
    results : list[dict]
        List of JSON data containing the partial results.
    group_cols : list[str]
        List of columns that were used to group the data.

    Returns
    -------
    pd.DataFrame
        Aggregated results.
    """
    # The results are pandas dictionaries converted to JSON. Convert them back and
    # then add them together to get the final partial_df.
    results = [pd.read_json(StringIO(result)) for result in results]

    # set group cols as index
    for idx, df in enumerate(results):
        results[idx] = df.set_index(group_cols)

    # Get all unique values for the result column
    all_result_levels = list(set([col for df in results for col in df.columns]))

    # The partial results are already in the form of a contingency table, but they
    # contain ranges (e.g. "0-5"). These are converted to two columns: one for the
    # minimum value and one for the maximum value.
    converted_results = []
    for partial_df in results:
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

    # Convert back to strings so that we can add ranges
    aggregated_df = aggregated_df.astype(str)

    # Finally, we need to combine the min and max values back into ranges
    min_max_cols = aggregated_df.columns
    for level in all_result_levels:
        # first, simply concatenate the columns
        aggregated_df[level] = (
            aggregated_df[f"{level}_min"] + "-" + aggregated_df[f"{level}_max"]
        )
        # then, remove extra text where min and max are the same
        min_max_same = aggregated_df[f"{level}_min"] == aggregated_df[f"{level}_max"]
        aggregated_df.loc[min_max_same, level] = aggregated_df.loc[
            min_max_same, level
        ].str.replace(r"-(\d+)", "", regex=True)

    # clean up: drop the min and max columns
    aggregated_df.drop(min_max_cols, axis=1, inplace=True)

    # reset index to pass the group columns along to results
    aggregated_df = aggregated_df.reset_index()

    return aggregated_df.to_json(orient="records")
