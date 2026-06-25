"""
Run this script to test your algorithm locally (without building a Docker
image) using the mock client.

Run as:

    pytest test/test.py -v

Make sure to do so in an environment where the package and dev dependencies
are installed. This can be done by running:

    uv sync --group dev
"""

import json
from pathlib import Path

import pandas as pd

from vantage6.algorithm.mock.network import MockNetwork

current_path = Path(__file__).parent

df1 = pd.read_csv(current_path / "test_data.csv")
df2 = pd.read_csv(current_path / "test_data2.csv")
data = pd.concat([df1, df2], ignore_index=True)

DATABASE_LABEL = "Database"

network = MockNetwork(
    datasets=[
        {DATABASE_LABEL: {"database": df1}},
        {DATABASE_LABEL: {"database": df2}},
    ],
    module_name="v6-crosstab-py",
)
client = network.user_client

DATABASES = [{"type": "dataframe", "dataframe_id": network.hq.dataframes[0]["id"]}]

organizations = client.organization.list()
org_ids = [organization["id"] for organization in organizations]

CROSSTAB_ARGS = {
    "results_col": "Gender",
    "group_cols": ["isOverweight"],
    "organizations_to_include": org_ids,
}


def _unwrap_central(results):
    """Central crosstab results are returned as a single-element list."""
    return results[0]


def test_central_crosstab():
    """Test central method aggregates partial contingency tables."""
    central_task = client.task.create(
        method="central_crosstab",
        arguments=CROSSTAB_ARGS,
        organizations=[org_ids[0]],
        databases=DATABASES,
    )
    results = _unwrap_central(client.wait_for_results(central_task.get("id")))

    assert "contingency_table" in results
    assert "chi2" in results
    assert isinstance(results["contingency_table"], list)
    assert len(results["contingency_table"]) > 0

    table = pd.DataFrame(results["contingency_table"])
    assert "isOverweight" in table.columns
    assert "Gender" in table.columns or "M" in table.columns or "F" in table.columns

    expected = (
        data.fillna("N/A")
        .groupby(["isOverweight", "Gender"], dropna=False)
        .size()
        .unstack(fill_value=0)
    )
    for overweight in expected.index:
        row = table[table["isOverweight"] == str(overweight)]
        if row.empty:
            continue
        for gender in expected.columns:
            if gender not in row.columns:
                continue
            cell = row.iloc[0][gender]
            if isinstance(cell, str) and cell.isdigit():
                assert int(cell) == expected.loc[overweight, gender]


def test_partial_crosstab():
    """Test partial method returns a parseable contingency table."""
    task = client.task.create(
        method="partial_crosstab",
        arguments={
            "results_col": "Gender",
            "group_cols": ["isOverweight"],
        },
        organizations=[org_ids[0]],
        databases=DATABASES,
    )
    results = client.wait_for_results(task.get("id"))

    partial_result = json.loads(results[0])
    assert isinstance(partial_result, list)
    assert len(partial_result) > 0
    assert "isOverweight" in partial_result[0]
    assert "Gender" in partial_result[0] or "M" in partial_result[0]


def test_central_with_privacy_placeholders():
    """Central aggregation should handle privacy range placeholders like '0-4'."""
    import importlib
    from io import StringIO

    central = importlib.import_module("v6-crosstab-py.central")
    partial_json = (
        pd.DataFrame(
            [
                {"Gender": "M", "0-4": "0-4", "40-49": "12"},
                {"Gender": "F", "0-4": "3", "40-49": "0-4"},
            ]
        )
        .astype(str)
        .to_json(orient="records")
    )

    # pandas may infer string columns instead of object when reading JSON
    partial_json_nullable = pd.read_json(
        StringIO(partial_json), dtype_backend="numpy_nullable"
    ).to_json(orient="records")

    results = central._aggregate_results(
        [partial_json_nullable], ["Gender"], include_chi2=False, include_totals=False
    )
    table = pd.DataFrame(results["contingency_table"])
    assert "0-4" in table.columns
    assert "40-49" in table.columns


def test_central_without_chi2():
    """Test central method without chi-squared statistic."""
    central_task = client.task.create(
        method="central_crosstab",
        arguments={
            **CROSSTAB_ARGS,
            "include_chi2": False,
        },
        organizations=[org_ids[0]],
        databases=DATABASES,
    )
    results = _unwrap_central(client.wait_for_results(central_task.get("id")))

    assert "contingency_table" in results
    assert "chi2" not in results
