Privacy
=======

.. _privacy-guards:

Guards
------

There are several guards in place to protect sharing too much information on individual
records:

- **Thresholding**: The system will only share information if there are at least `n`
  records in the group. This is to prevent sharing information on individual records.
  By default, the threshold is set to 5 records. Node administrators can change this
  threshold by adding the following to their node configuration file:

  .. code:: yaml

    algorithm_env:
      CROSSTAB_PRIVACY_THRESHOLD: 5

  and setting the value to the desired threshold. This configuration will ensure that
  an environment variable `CROSSTAB_PRIVACY_THRESHOLD` is set to the desired threshold
  and passed to the algorithm container.

  Note that the algorithm also requires at least one field of the contingency table to
  pass the threshold. This is to prevent that if a task is created for a column that
  contains only unique values, the result would reveal which unique values are present
  in the column.

- **Minimum number of data rows to participate**: A node will only participate if it
  contains at least `n` data rows. This is to prevent nodes with very little data from
  participating in the computation. By default, the minimum number of data rows is set
  to 5. Node administrators can change this minimum by adding the following to their
  node configuration file:

  .. code:: yaml

    algorithm_env:
      CROSSTAB_MINIMUM_ROWS_TOTAL: 5

- **Not allowing zero values**: By default, the system will not values of zero to be shared.
  In principle, it should be OK to share zero values, since this only confirms an
  absence of certain combinations of values. However, it may be possible to infer
  information from zero values. For example, for a rather sparse contingency table,
  the information which combinations exist at a certain data is more valuable than for
  a dense table. It is therefore possible not to share this information by not sharing
  zero values.

  If you do wish to share zero values, you can add the following to your node
  configuration:

  .. code:: yaml

    algorithm_env:
      CROSSTAB_ALLOW_ZERO: true


Data sharing
------------

The only intermediate data that is shared, are the local contingency tables. These
are formatted in the same way as the final result, but contain only the data from
the local node. The risk of sharing this data is low, as it concerns aggregated data.

Vulnerabilities to known attacks
--------------------------------

.. Table below lists some well-known attacks. You could fill in this table to show
.. which attacks would be possible in your system.

.. list-table::
    :widths: 25 10 65
    :header-rows: 1

    * - Attack
      - Risk eliminated?
      - Risk analysis
    * - Reconstruction
      - ✔
      -
    * - Differencing
      - ❌
      - May be possible by making smart selection with preprocessing, or by sending
        multiple tasks before and after data is updated.
    * - Deep Leakage from Gradients (DLG)
      - ✔
      -
    * - Generative Adversarial Networks (GAN)
      - ✔
      -
    * - Model Inversion
      - ✔
      -
    * - Watermark Attack
      - ✔
      -