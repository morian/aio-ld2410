Tutorial
========

.. currentmodule:: aio_ld2410

This section covers most of the API with real examples and commands.

Links to the :ref:`reference` will be provided all along so you can get more details.

Before going further, ensure to have a suitable python environment (see :ref:`installation`).


Connecting to the device
------------------------

First you need to identify your device and its name depends on your platform!
You can ask pyserial_ to list all available console devices on your system:

.. _pyserial: https://github.com/pyserial/pyserial/tree/master

.. code-block:: console

   $ python -m serial.tools.list_ports

   /dev/ttyS0
   /dev/ttyS1
   /dev/ttyUSB0
   3 ports found

Here I use an USB serial adapter on ``/dev/ttyUSB0``, which is confirmed by the system logs.
On windows this command most likely returns devices with name in ``COM*``.

For this tutorial I will use ``/dev/ttyUSB0``, replace with yours when applicable.

The following code simply opens the device:

.. literalinclude:: ../../examples/open_device.py
   :caption: examples/open_device.py
   :emphasize-lines: 7
   :linenos:

If you ever need to change the baud rate (defaults to ``256000``) see :meth:`LD2410.__init__`.


Entering the configuration mode
-------------------------------

Entering configuration mode is also implemented as an asynchronous context.
You cannot call configuration commands outside of this context!
This context is a requirement before any other command is issued.

See :meth:`LD2410.configure` for more details.

In the following example the configuration context spread over the emphasized lines:

.. literalinclude:: ../../examples/read_firmware_version.py
   :caption: examples/read_firmware_version.py
   :emphasize-lines: 8-9
   :linenos:

.. admonition:: Debug steps if this code does not work
   :class: hint

   If you ever have an issue with this example, perform the following checks:

     - Check that the device you provided is correct (and is a ``LD2410``)
     - Check that your device does not expect a different baud rate

Notice that on ``LD2410B`` and ``LD2410C``, some features may not be available
if the firmware printed by this code is too old.


Reading configuration
---------------------

Standard parameters
^^^^^^^^^^^^^^^^^^^

The following example used :meth:`LD2410.get_parameters` to read all the standard
parameters from the device (returning a :class:`ParametersStatus`):

.. literalinclude:: ../../examples/read_simple_configuration.py
   :caption: examples/read_simple_configuration.py
   :name: read_simple_configuration
   :linenos:

This code produces the following output:

.. code-block:: console

   $ ./examples/read_simple_configuration.py
   Max distance gate           8
   Max motion detection gate   8
   Max static detection gate   8
   Presence timeout            5
   Detection thresholds:
     Gate       0 |   1 |   2 |   3 |   4 |   5 |   6 |   7 |   8
     Moving    50 |  50 |  40 |  30 |  20 |  15 |  15 |  15 |  15
     Static     0 |   0 |  40 |  40 |  30 |  30 |  20 |  20 |  20


Distance resolution
^^^^^^^^^^^^^^^^^^^

.. admonition:: Not available on all models / firmwares
   :class: warning

   This command seems to only be available for ``LD2410B`` and ``LD2410C`` devices
   with a (quite recent) firmware.

Using :meth:`LD2410.get_distance_resolution` we can read the range covered by gates:

.. literalinclude:: ../../examples/read_distance_resolution.py
   :caption: examples/read_distance_resolution.py
   :linenos:


Writing configuration
---------------------

Gate configuration comes with two methods that are when combined analogous
to the :meth:`LD2410.get_parameters` seen above.


General configuration
^^^^^^^^^^^^^^^^^^^^^

The following example simply sets the maximum detection gate for moving targets to 4
(3 meters) and the maximum detection gate for static targets to 6 (4.5 meters).

It means that detected targets are either close to the sensor and moving, or can be
farther away but standing still.

.. literalinclude:: ../../examples/write_simple_configuration.py
   :caption: examples/write_simple_configuration.py
   :linenos:


Gate sensitivity configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To be perfectly complementary to read_simple_configuration_, we have to use
:meth:`LD2410.set_gate_sensitivity`, as shown in the following example:

.. literalinclude:: ../../examples/write_gate_sensitivity.py
   :caption: examples/write_gate_sensitivity.py
   :linenos:

The result of both scripts can be read again with read_simple_configuration_:

.. code-block:: console

   $ ./examples/read_simple_configuration.py
   Max distance gate           8
   Max motion detection gate   4
   Max static detection gate   6
   Presence timeout            10
   Detection thresholds:
     Gate       0 |   1 |   2 |   3 |   4 |   5 |   6 |   7 |   8
     Moving    50 |  50 |  40 |  40 |  35 |  30 |  15 |  15 |  15
     Static     0 |   0 |  40 |  35 |  30 |  25 |  20 |  20 |  20


Set distance resolution
^^^^^^^^^^^^^^^^^^^^^^^

Distance resolution can easily be set through :meth:`LD2410.set_distance_resolution`
but it requires a device restart to be effective on the sensor itself.

Module restart can be performed through :meth:`LD2410.restart_module`.

.. admonition:: Your device lies to you
   :class: note

   If you forget to restart, a call to :meth:`LD2410.get_distance_resolution` will
   return value you just configured and not the value currently applied.

.. literalinclude:: ../../examples/write_distance_configuration.py
   :caption: examples/write_distance_configuration.py
   :emphasize-lines: 13
   :linenos:

Notice the emphasized line, we have to wait for a little bit before we can send new
commands to the device (as it is restarting).


Reading reports
---------------


