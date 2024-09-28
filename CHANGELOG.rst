=========
Changelog
=========

The format is based on `Keep a Changelog`_ and this project adheres to `Semantic Versioning`_.

.. _Keep a Changelog: https://keepachangelog.com/en/1.0.0/
.. _Semantic Versioning: https://semver.org/spec/v2.0.0.html

.. currentmodule:: aio_ld2410

1.0.0 (UNRELEASED)
==================

Added
-----
- Add a lot of documentation

Changed
-------
- Renamed many things, inspired by ESPHome_
- Reworked :mod:`.exceptions` to make things more straightforward
- Reworked :class:`stream.FrameStream` with a real iterator

.. _ESPHome: https://github.com/esphome/esphome


Fixed
-----
- Now checking arguments to the following methods:
   - :meth:`.LD2410.set_gate_sensitivity`
   - :meth:`.LD2410.set_light_control`
   - :meth:`.LD2410.set_parameters`
- Renamed ``LD2410.set_gate_sentivity`` to `.LD2410.set_gate_sensitivity`


0.1.0 (2024-09-25)
==================

Initial release
---------------

- Full implementation for ``LD2410C`` devices on firmware ``v2.04.23022511``
- Linted and typed code, using ruff_ and mypy_
- Tests with a dedicated ``LD2410`` emulator, code is fully covered

.. _ruff: https://docs.astral.sh/ruff/
.. _mypy: https://www.mypy-lang.org
