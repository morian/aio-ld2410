Contributing
============

Thanks for considering a contribution to ``aio-ld2410``!

Code of Conduct
---------------

This project and everyone participating in it is governed by the `Code of Conduct`_.
By participating in any way, you are expected to uphold this code.

.. _Code of conduct: https://github.com/morian/aio-ld2410/blob/master/CODE_OF_CONDUCT.md


Contributions
-------------

`Bug reports`_ and `pull requests`_ are welcome.

.. _Bug reports: https://github.com/morian/aio-ld2410/issues/new
.. _pull requests: https://github.com/morian/aio-ld2410/compare/

To quickly get started with development run the following commands:

.. code-block:: console

   $ git clone https://github.com/morian/aio-ld2410.git
   $ cd aio-ld2410
   $ python3 -m venv venv
   $ source venv/bin/activate
   (venv) $ make install


Before a pull request, make sure to check for linting and typing using the following commands:

.. code-block:: console

   $ make lint mypy

If if fixes a non trivial issue with the code, an additional test-case would be nice as well.

.. code-block:: console

   $ make test

I am especially interested in feedbacks on variants and firmwares behaviors, especially
if we can find a reliable way to detect the type of variant this library is discussing with.

Also, writing documentation is not my favorite cup of tea, all improvements are valuable!


Questions
---------

I opened the `discussion area`_ on github for any question and discussion that cannot fit
in a bug report. Please use this space for anything related to this library.

This place is not suitable in the following situations:

- A question about asyncio_ and how to do things with it
- A question that is already answered in this documentation or in the discussion space

.. _asyncio: https://docs.python.org/3/library/asyncio.html
.. _discussion area: https://github.com/morian/aio-ld2410/discussions
