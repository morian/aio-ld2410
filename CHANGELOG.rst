=========
Changelog
=========

The format is based on `Keep a Changelog`_ and this project adheres to `Semantic Versioning`_.

.. _Keep a Changelog: https://keepachangelog.com/en/1.0.0/
.. _Semantic Versioning: https://semver.org/spec/v2.0.0.html


1.0.1 (2024-10-09)
==================

Added
-----
- Support for Python 3.13

Fixed
-----
- Many errors and typos in documentation
- Test framework was simplified a bit


1.0.0 (2024-09-29)
==================

Added
-----
- Added documentation using Sphinx_:
   - Device description and protocol base concepts
   - Tutorial with many short code samples
   - API reference covering the entire user API
   - About section with project related pages (including this CHANGELOG)

.. _Sphinx: https://www.sphinx-doc.org/en/master/

Changed
-------
- Renamed many methods and attributes, inspired by the naming in ESPHome_
   - All references to ``motion`` have been renamed to ``moving``
   - All references to ``standstill`` or ``stationary`` have been renamed to ``static``
   - All references to ``auxiliary`` have been renamed to ``light``
   - Attribute ``no_one_idle_duration`` was renamed to ``presence_timeout``
- Reworked :mod:`.exceptions` to make things easier to understand
- Reworked :class:`stream.FrameStream` with a real iterator

.. _ESPHome: https://github.com/esphome/esphome

Fixed
-----
- Now checking arguments to the following methods:
   - :meth:`.LD2410.set_gate_sensitivity`
   - :meth:`.LD2410.set_light_control`
   - :meth:`.LD2410.set_parameters`
- :meth:`.LD2410.set_baud_rate` can now raise :exc:`.CommandParamError`
- Renamed ``LD2410.set_gate_sentivity`` to :meth:`.LD2410.set_gate_sensitivity`


0.1.0 (2024-09-25)
==================

Initial release
---------------

- Full implementation for ``LD2410C`` devices on firmware ``v2.04.23022511``
- Linted and typed code, using ruff_ and mypy_
- Tests with a dedicated ``LD2410`` emulator, code is fully covered

.. _ruff: https://docs.astral.sh/ruff/
.. _mypy: https://www.mypy-lang.org
