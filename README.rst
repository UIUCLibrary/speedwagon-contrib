speedwagon-contrib
==================

This contains contributed workflows for Speedwagon. They have been developed from the community and are shared here.

Create a Development Environment
--------------------------------
Use uv to create development environment

On Mac or linux

.. code-block:: console

    uv sync
    source .venv/bin/activate

On Windows (Powershell)

.. code-block:: pwsh-session

    uv sync
    .venv\Scripts\Activate.ps1

On Windows (cmd)

.. code-block:: doscon

    uv sync
    .venv\Scripts\activate.bat


Run Tests
---------

To run tests, use pytest

.. code-block:: console

    pytest

To test all supported platforms, use tox

.. code-block:: console

    uv run --only-group tox-uv --isolated tox run --runner=uv-venv-lock-runner

Run Static Analysis
-------------------

To run all static analysis tools supported, use tox with "lint" label

.. code-block:: console

    uv run --only-group tox-uv --isolated tox run --runner=uv-venv-lock-runner -m lint
