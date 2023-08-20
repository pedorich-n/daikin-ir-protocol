# Daikin IR protocol 

This repository contains the results of my attempts to decode IR protocol of AC Daikin F28YTES-W with remote ARC478A65 using Raspberry Pi Pico with IR sensor [TSSP4038](https://www.vishay.com/docs/82458/tssp40.pdf) and [AnalysIR](https://www.analysir.com/) (very powerful tool).

## Why
I wanted to control AC using Home-Assistant, and existing solutions provided very limited control at the time.

## Results & Code
Raw results from AnalysIR can be found in [decoding](decoding/) folder. 

Interpreted results can be found [here](src/daikin_ac_state.py).

There's also JSON generator for [SmartIR](https://github.com/smartHomeHub/SmartIR) integration for Home-Assistant [here](src/smartir/smartir_generator.py).


## Acknowledgement
https://github.com/blafois/Daikin-IR-Reverse helped a lot. 

My AC's protocol is pretty much the same, with a couple of changes due to different functions.


---

<sup><sub>TODO: add breadboard photo/scheme</sub></sup>

