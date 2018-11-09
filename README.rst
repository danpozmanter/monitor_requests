monitor requests
================

|Build Status| |PyPI|

A tool to check for remote calls via the `requests`_ module.

Working on a large and complicated codebase with lot's of slow unit tests?
Suspect external API calls are slowing things down?

Here's a quick tool for just that purpose.

**Usage**

.. code:: python

    import unittest
    import monitor_requests
    from example import example_method

    class ExampleTestCase(unittest.TestCase):

        @classmethod
        def setUpClass(cls):
            cls.monitor = monitor_requests.Monitor()

        @classmethod
        def tearDownClass(cls):
            print('External calls for example:')
            # Optionally pass tracebacks=False to skip outputing tracebacks
            # Report will call .stop() by default.
            cls.monitor.report(tracebacks=False)

        def test_example_method(self):
            result = example_method()
            self.assertEqual(result.status_code, 200)

    if __name__ == 'main':
        unittest.main()

You can also set this up inside a test runner (or a session fixture if using py.test).

To write to a file:

.. code:: python

        @classmethod
        def tearDownClass(cls):
            with open('output.txt', 'w') as f:
                cls.monitor.report(output=f)

**Installation**

.. code:: bash
    
    pip install MonitorRequests

.. _requests: https://github.com/requests/requests
.. |Build Status| image:: https://travis-ci.org/danpozmanter/monitor_requests.svg?branch=master
   :target: https://travis-ci.org/danpozmanter/monitor_requests
.. |PyPI| image:: https://img.shields.io/pypi/v/MonitorRequests.svg
   :target: https://pypi.python.org/pypi/MonitorRequests/