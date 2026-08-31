Client
======

.. currentmodule:: aio_ld2410

.. py:class:: LD2410
   :no-typesetting:


:class:`LD2410` is the :mod:`asyncio` serial client from :mod:`aio_ld2410` to handle ``LD2410``
devices.


Create and Connect
------------------

.. class:: LD2410
   :no-index:

   .. automethod:: __init__
   .. automethod:: __aenter__
   .. automethod:: __aexit__


Properties
----------

.. class:: LD2410
   :no-index:

   .. autoproperty:: configuring
   .. autoproperty:: connected
   .. autoproperty:: entered


Reports
-------

.. class:: LD2410
   :no-index:

   .. automethod:: get_last_report
   .. automethod:: get_next_report
   .. automethod:: get_reports


Configuration mode
------------------

.. class:: LD2410
   :no-index:

   .. automethod:: configure


Utilities
^^^^^^^^^

.. class:: LD2410
   :no-index:

   .. automethod:: get_firmware_version
   .. automethod:: reset_to_factory
   .. automethod:: restart_module
   .. automethod:: set_baud_rate
   .. automethod:: set_engineering_mode


Gates
^^^^^

.. class:: LD2410
   :no-index:

   .. automethod:: get_parameters
   .. automethod:: set_parameters
   .. automethod:: set_gate_sensitivity

   .. automethod:: get_distance_resolution
   .. automethod:: set_distance_resolution


Noise detection
^^^^^^^^^^^^^^^

These features are only available on ``LD2410B`` and ``LD2410C`` starting with
firmware ``2.44`` and can be used for automatic calibration.

.. class:: LD2410
   :no-index:

   .. automethod:: start_noise_detection
   .. automethod:: get_noise_detection_status


Bluetooth
^^^^^^^^^

.. class:: LD2410
   :no-index:

   .. automethod:: get_bluetooth_address
   .. automethod:: set_bluetooth_mode
   .. automethod:: set_bluetooth_password


Light sensor
^^^^^^^^^^^^

.. class:: LD2410
   :no-index:

   .. automethod:: get_light_control
   .. automethod:: set_light_control
