Implementation
==============

Overview
--------

The implementation is rather straightforward. The central part requests the partial
contingency table from each node, which they compute in one go. The central part then
aggregates the partial contingency tables to the final table.

.. uml::

  !theme superhero-outline

  caption The central part of the algorithm is responsible for the \
          orchestration and aggregation\n of the algorithm. The partial \
          parts are executed on each node.

  |client|
  :request analysis;

  |central|
  :Collect organizations
  in collaboration;
  :Create partial tasks;

  |partial|
  :Partial_crosstab creates
  partial contingency tables;

  |partial|
  :Mask values below
  privacy threshold;

  |central|
  :Combine contingency
  tables;

  |client|
  :Receive results;


Partials
--------

Partials are the computations that are executed on each node. The partials have access
to the data that is stored on the node. The partials are executed in parallel on each
node.

``partial_crosstab``
~~~~~~~~~~~~~~~~~~~~

The partial function computes the local contingency table. Any values below the privacy threshold
are converted to a range. For example, if the privacy threshold is 5, then all values
below 5 are converted to '0-4'. The local contingency table is sent to the central part.

The partial function includes several privacy checks - see the
:ref:`privacy guards <privacy-guards>` section for more information.

Central
-------

The central part is responsible for the aggregation of the cross-tables of individual
nodes.

``central_crosstab``
~~~~~~~~~~~~~~~~~~~~

The central part sums up the local contingency tables resulting in the global
contingency table.

- If the local contingency table contains values below the privacy threshold, the
  central part will show a range instead of the actual value. For example, if the
  privacy threshold is 5, and the two nodes included in an analysis report back 0-4
  and 11, the central part will show 11-15 as the value for the corresponding cell.
- If one node does not contain a cell that another node do have, the central part will
  simply count zero for the missing cell, i.e. the central part will simply show the
  sum of the values that *are* reported.

