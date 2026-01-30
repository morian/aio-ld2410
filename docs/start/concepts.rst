Concepts
========

What is a HLK-LD2410?
---------------------

Main features
^^^^^^^^^^^^^

``LD2410`` is a high-sensitivity 24GHz human presence sensor developed by `Hi-Link Electronics`_.
The farthest sensing distance can reach 6 meters, and the default distance resolution is 75cm.
It features a large detection angle covering ±60 degrees.

.. _Hi-Link Electronics: https://www.hlktech.net

This library currently supports three variants, ``LD2410``, ``LD2410B`` and ``LD2410C``.

While model ``LD2410`` is only configurable through the serial link, ``LD2410B`` and ``LD2410C``
also come with a bluetooth chip, making it possible to configure the device though the air.

A dedicated application called HLKRadarTool_ has been released by the vendor for this purpose.

.. _HLKRadarTool: https://play.google.com/store/apps/details?id=com.hlk.hlkradartool

``aio-ld2410`` implements all actions currently provided by this application.

.. admonition:: Beware while using HLKRadarTool_ and this library at the same time.
   :class: caution

   Any or both of them could experience unexpected behaviors due to conflicting requests
   and mixed responses.

Effective detection can be performed in two distinct ways:
- A dedicated ``OUT`` pin on the printed circuit board (only ``LOW`` or ``HIGH``)
- Report frames being sent regularly on the serial link or bluetooth (if applicable)


Extra features
^^^^^^^^^^^^^^

Models ``LD2410B`` and ``LD2410C``, when running with firmware ≥ 2.04 also come with
extra features:

  - Resolution can be dropped from 75cm to 20cm, for a maximum detection range of 160cm,
    but with a greater distance accuracy.
  - Bluetooth control is now password protected with a 6 ASCII character password.
  - An additional photo-sensitive diode now reports the ambient light level.
  - This light level can be used to determine the status of the ``OUT`` pin.


How was it implemented?
-----------------------

Gates, gates everywhere
^^^^^^^^^^^^^^^^^^^^^^^

The area in front of the sensor is divided into 9 ranges called gates in the documentation.

The following table tells the range covered by each gate depending on the distance
resolution setting:

+-----------------------++-----------------------+
|     75cm resolution   ||     20cm resolution   |
+======+========+=======++======+========+=======+
| Gate |  Start |  End  || Gate |  Start |  End  |
+------+--------+-------++------+--------+-------+
+------+--------+-------++------+--------+-------+
|    0 |      - |    0  ||    0 |      - |     0 |
+------+--------+-------++------+--------+-------+
|    1 |      0 |   75  ||    1 |      0 |    20 |
+------+--------+-------++------+--------+-------+
|    2 |     75 |  150  ||    2 |     20 |    40 |
+------+--------+-------++------+--------+-------+
|    3 |    150 |  225  ||    3 |     40 |    60 |
+------+--------+-------++------+--------+-------+
|    4 |    225 |  300  ||    4 |     60 |    80 |
+------+--------+-------++------+--------+-------+
|    5 |    300 |  375  ||    5 |     80 |   100 |
+------+--------+-------++------+--------+-------+
|    6 |    375 |  450  ||    6 |    100 |   120 |
+------+--------+-------++------+--------+-------+
|    7 |    450 |  525  ||    7 |    120 |   140 |
+------+--------+-------++------+--------+-------+
|    8 |    525 |  600  ||    8 |    140 |   160 |
+------+--------+-------++------+--------+-------+


Energy and sensitivity
^^^^^^^^^^^^^^^^^^^^^^

Each gate is configured individually with two energy thresholds, one for moving targets
and one for static targets. When the reading energy value is above the configured threshold,
a target is detected (either as moving or standing still).

Both reported energies and threshold have values ranging from 0 to 100.
Here is the list of default energy thresholds:

====== ================== ===================
 Gate   Moving threshold   Static threshold
====== ================== ===================
     0              50%                 N/A
     1              50%                 N/A
     2              40%                 40%
     3              30%                 40%
     4              20%                 30%
     5              15%                 30%
     6              15%                 20%
     7              15%                 20%
     8              15%                 20%
====== ================== ===================


Engineering & Configuration mode
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. currentmodule:: aio_ld2410

The device constantly generates status reports over the serial link (at a typical rate of 10/sec).

These reports (see :class:`.ReportStatus`) can contain either basic information or basic
and advanced details (see :class:`.ReportBasicStatus` and :class:`.ReportEngineeringStatus`).
It depends on whether the engineering mode is currently enabled or not.

To send commands to the device, we first have to put it in the configuration mode.
During this phase, status reports are no longer being generated.

All command requests sent to the device have to be performed in configuration mode, otherwise
the device will simply send back an error status. Also note that some commands require a device
restart to be effective.
