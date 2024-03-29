"""
This file contains all central algorithm functions. It is important to note
that the central method is executed on a node, just like any other method.

The results in a return statement are sent to the vantage6 server (after
encryption if that is enabled).
"""

from typing import Any

from vantage6.algorithm.tools.util import info
from vantage6.algorithm.tools.decorators import algorithm_client
from vantage6.algorithm.client import AlgorithmClient


@algorithm_client
def central_crosstab(
    client: AlgorithmClient, organizations_to_include: list[int] = None
) -> Any:
    """
    Central part of the algorithm

    Parameters
    ----------
    client : AlgorithmClient
        The client object used for communication with the server.
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
        "kwargs": {},
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

    # TODO probably you want to aggregate or combine these results here.
    # For instance:
    # results = [sum(result) for result in results]

    # return the final results of the algorithm
    return results
