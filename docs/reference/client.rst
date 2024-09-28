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


Configuration mode
------------------

.. class:: LD2410
   :no-index:

   .. automethod:: configure


Getters
^^^^^^^

.. class:: LD2410
   :no-index:

   .. automethod:: get_bluetooth_address
   .. automethod:: get_distance_resolution
   .. automethod:: get_firmware_version
   .. automethod:: get_light_control
   .. automethod:: get_parameters


Setters
^^^^^^^

.. class:: LD2410
   :no-index:

   .. automethod:: reset_to_factory
   .. automethod:: restart_module
   .. automethod:: set_baud_rate
   .. automethod:: set_bluetooth_mode
   .. automethod:: set_bluetooth_password
   .. automethod:: set_distance_resolution
   .. automethod:: set_engineering_mode
   .. automethod:: set_gate_sensitivity
   .. automethod:: set_light_control
   .. automethod:: set_parameters


Reports
-------

.. class:: LD2410
   :no-index:

   .. automethod:: get_last_report
   .. automethod:: get_next_report
   .. automethod:: get_reports
