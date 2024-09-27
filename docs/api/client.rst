Client
======

.. currentmodule:: aio_ld2410.ld2410

.. autoclass:: LD2410
   :no-show-inheritance:

   Runtime properties
   ------------------

   .. autoproperty:: configuring
   .. autoproperty:: connected
   .. autoproperty:: entered

   Creating and connecting
   -----------------------

   .. automethod:: __init__
   .. automethod:: __aenter__
   .. automethod:: __aexit__

   Configuration mode
   ------------------

   .. automethod:: configure

   Getters
   ^^^^^^^

   .. automethod:: get_auxiliary_controls
   .. automethod:: get_bluetooth_address
   .. automethod:: get_distance_resolution

   Setters
   ^^^^^^^

   .. automethod:: restart_module

   .. automethod:: set_auxiliary_controls
   .. automethod:: set_distance_resolution
