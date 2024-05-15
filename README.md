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
docker pull harbor2.vantage6.ai/algorithms/crosstab
```

It is designed to be run with the [vantage6](https://vantage6.ai)
infrastructure for distributed analysis and learning. The base code for this algorithm
has been created via the [v6-algorithm-template](https://github.com/vantage6/v6-algorithm-template)
generator.

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
docker pull harbor2.vantage6.ai/algorithms/crosstab
```

## Dockerizing your algorithm

To finally run your algorithm on the vantage6 infrastructure, you need to
create a Docker image of your algorithm.

### Automatically

The easiest way to create a Docker image is to use the GitHub Actions pipeline to
automatically build and push the Docker image. All that you need to do is push a
commit to the `main` branch.

### Manually

A Docker image can be created by executing the following command in the root of your
algorithm directory:

```bash
docker build -t [my_docker_image_name] .
```

where you should provide a sensible value for the Docker image name. The
`docker build` command will create a Docker image that contains your algorithm.
You can create an additional tag for it by running

```bash
docker tag [my_docker_image_name] [another_image_name]
```

This way, you can e.g. do
`docker tag local_average_algorithm harbor2.vantage6.ai/algorithms/average` to
make the algorithm available on a remote Docker registry (in this case
`harbor2.vantage6.ai`).

Finally, you need to push the image to the Docker registry. This can be done
by running

```bash
docker push [my_docker_image_name]
```

Note that you need to be logged in to the Docker registry before you can push
the image. You can do this by running `docker login` and providing your
credentials. Check [this page](https://docs.docker.com/get-started/04_sharing_app/)
For more details on sharing images on Docker Hub. If you are using a different
Docker registry, check the documentation of that registry and be sure that you
have sufficient permissions.
