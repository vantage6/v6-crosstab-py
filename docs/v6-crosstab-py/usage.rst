How to use
==========

Input arguments
---------------

.. list-table::
   :widths: 20 20 60
   :header-rows: 1

   * - Argument
     - Type
     - Description
   * - ``results_col``
     - Column name (string)
     - The column whose categories will be the columns of the contingency table.
   * - ``group_cols``
     - List of column names (list of strings)
     - One or more columns whose categories, or combinations of categories, will be the
       rows of the contingency table.
   * - ``organizations_to_include``
     - List of integers
     - Which organizations to include in the computation.

Python client example
---------------------

To understand the information below, you should be familiar with the vantage6
framework. If you are not, please read the `documentation <https://docs.vantage6.ai>`_
first, especially the part about the
`Python client <https://docs.vantage6.ai/en/main/user/pyclient.html>`_.

Let's say you want to know how many males and females are overweight in different age
groups, e.g. something like:

.. list-table::
   :widths: 20 20 20 20
   :header-rows: 1

   * - AgeGroup
     - isOverweight
     - Male
     - Female
   * - 0-18
     - True
     - 11
     - 6
   * - 0-18
     - False
     - 30
     - 29
   * - 18-65
     - True
     - 55
     - 44
   * - 18-65
     - False
     - 50
     - 56
   * - 65+
     - True
     - 5
     - 10
   * - 65+
     - False
     - 15
     - 14


Such a result could be obtained by running the following Python client code. Note that
``AgeGroup``, ``isOverweight``, and ``Gender`` should be categorical values in your
dataset, and that you should replace the values at the top to authenticate with your
vantage6 server.

.. code-block:: python

  from vantage6.client import Client

  server = 'http://localhost'
  port = 5000
  api_path = '/api'
  private_key = None
  username = 'root'
  password = 'password'

  # Create connection with the vantage6 server
  client = Client(server, port, api_path)
  client.setup_encryption(private_key)
  client.authenticate(username, password)

  input_ = {
    'method': 'central_crosstab',
    'kwargs': {
        'results_col': 'Gender',
        'group_cols': ["AgeGroup", "isOverweight"]
    }
  }

  my_task = client.task.create(
      collaboration=1,
      organizations=[1],
      name='Compute contingency table',
      description='Create a contingency table showing the relationship between two or more variables',
      image='harbor2.vantage6.ai/algorithms/v6-crosstab-py:latest',
      input=input_,
      databases=[
          {'label': 'default'}
      ]
  )

  task_id = my_task.get('id')
  results = client.wait_for_results(task_id)