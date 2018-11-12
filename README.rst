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


To filter what domains are captured:

.. code:: python

    # Only capture facebook and google requests:
    monitor = monitor_requests.Monitor(
        domains=['facebook\.com', 'google\.com']
    )

To set this up inside a django test runner:
(Note you may need to run with --parallel=1)

.. code:: python

    def run_suite(self, suite, **kwargs):
        monitor = monitor_requests.Monitor()
        test_result = super(ReelioTestRunner, self).run_suite(suite, **kwargs)
        monitor.report()
        return test_result

To set up inside a py.test session fixture:

.. code:: python

    @pytest.fixture(scope='session')
    def session_fixture():
        monitor = monitor_requests.Monitor()
        yield
        monitor.report()

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