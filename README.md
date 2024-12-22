# Daikin IR protocol 

This repository contains the results of my attempts to decode IR protocol of AC Daikin F28YTES-W with remote ARC478A65.

## Results & Code
Raw results from AnalysIR can be found in [decoding](decoding/) folder. 

Interpreted protocol can be found [here](src/daikin_ac_state.py).

There's also JSON generator for [SmartIR](https://github.com/smartHomeHub/SmartIR) integration for Home-Assistant [here](src/smartir/smartir_generator.py) (Broadlink controller). With the help of [ir_tools.py](src/smartir/ir_tools.py) it's possible to write generators for other controllers.


## Acknowledgement
https://github.com/blafois/Daikin-IR-Reverse helped a lot. 

My AC's protocol is pretty much the same, with a couple of changes due to different functions.



