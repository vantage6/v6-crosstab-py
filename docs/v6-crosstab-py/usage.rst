How to use
==========

Input arguments
---------------

.. describe the input arguments:
.. ['organizations_to_include']

Python client example
---------------------

To understand the information below, you should be familiar with the vantage6
framework. If you are not, please read the `documentation <https://docs.vantage6.ai>`_
first, especially the part about the
`Python client <https://docs.vantage6.ai/en/main/user/pyclient.html>`_.

.. TODO Some explanation of the code below

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
    'master': True,
    'method': 'central_crosstab',
    'args': [],
    'kwargs': {
        'organizations_to_include': 'my_value',
    },
    'output_format': 'json'
  }

  my_task = client.task.create(
      collaboration=1,
      organizations=[1],
      name='v6-crosstab-py',
      description='Create a contingency table showing the relationship between two or more variables',
      image='harbor2.vantage6.ai/algorithms/v6-crosstab-py:v4',
      input=input_,
      data_format='json'
  )

  task_id = my_task.get('id')
  results = client.wait_for_results(task_id)