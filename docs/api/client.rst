Client
======

.. currentmodule:: aio_ld2410

.. autoclass:: LD2410
   :no-show-inheritance:

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

   .. automethod:: get_auxiliary_controls
   .. automethod:: get_bluetooth_address
   .. automethod:: get_distance_resolution
   .. automethod:: get_firmware_version
   .. automethod:: get_parameters


Setters
^^^^^^^

.. class:: LD2410
   :no-index:

   .. automethod:: reset_to_factory
   .. automethod:: restart_module
   .. automethod:: set_auxiliary_controls
   .. automethod:: set_baudrate
   .. automethod:: set_bluetooth_mode
   .. automethod:: set_bluetooth_password
   .. automethod:: set_distance_resolution
   .. automethod:: set_engineering_mode
   .. automethod:: set_gate_sensitivity
   .. automethod:: set_parameters


Reports
-------

.. class:: LD2410
   :no-index:

   .. automethod:: get_last_report
   .. automethod:: get_next_report
   .. automethod:: get_reports
