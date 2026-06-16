<h1 align="center">
  <br>
  <a href="https://vantage6.ai"><img src="https://github.com/IKNL/guidelines/blob/master/resources/logos/vantage6.png?raw=true" alt="vantage6" width="350"></a>
</h1>

<!-- Badges go here-->
<h3 align="center">

[![Release](https://github.com/vantage6/vantage6/actions/workflows/release.yml/badge.svg)](https://github.com/vantage6/vantage6/actions/workflows/release.yml)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/a22f3bcea6f545fc832fdb810bb825a5)](https://app.codacy.com/gh/vantage6/v6-crosstab-py/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
[![DOI](https://zenodo.org/badge/779196318.svg)](https://zenodo.org/badge/latestdoi/779196318)

</h3>

# v6-crosstab-py

This algorithm creates a contingency table showing the relationship between two or more
variables. The docker image is available at:

```bash
docker pull ghcr.io/vantage6/algorithm/crosstab
```

It is designed to be run with the [vantage6](https://vantage6.ai)
infrastructure for distributed analysis and learning. The base code for this algorithm
has been created via the [v6-algorithm-template](https://github.com/vantage6/v6-algorithm-template)
generator.

## Running the algorithm

Data is no longer loaded automatically inside compute functions. In a session, run a **data extraction** step first (for example `read_csv` from [v6-extract-basics-py](https://github.com/vantage6/v6-extract-basics-py)), then run **`central_crosstab`** with `results_col`, `group_cols`, and optional flags such as `include_chi2` and `include_totals`.

## Build

```bash
make image
```

## Documentation

The documentation is hosted [here](https://algorithms.vantage6.ai/en/latest/v6-crosstab-py/implementation.html).

You can run the documentation locally by running:

```bash
cd docs
pip install -r requirements.txt
make livehtml
```

## Docker image

The Docker image that contains this algorithm can be retrieved with:

```
docker pull ghcr.io/vantage6/algorithm/crosstab
```
