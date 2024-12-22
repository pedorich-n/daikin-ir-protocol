# Decoding

I've used a Raspberry Pi Pico with IR sensor [TSSP4038](https://www.vishay.com/docs/82458/tssp40.pdf) and an amazing tool called [AnalysIR](https://analysir.com/) to capture and decode IR codes. 
Chris from AnalysIR helped me understand how to use the program and decode some results. Thanks!
Ultimately I had to define a custom protocol for AnalysIR as existing ones didn't manage to fully capture all packets. The new protocol had to be added in `C:\Users\<user>\AppData\Roaming\AnalysIR\AnalysIR.ini` file. Protocol definition is in the [AnalysIR_custom_protocol.ini](./AnalysIR_custom_protocol.ini). The magical part is `Syntax=HB160THB152T`. That's what tells AnalysIR for how many packets to look for and try to decode.


## Protocol details

Low level IR info can be found in [Daikin_AC_Long_Protocol_History.txt](./Daikin_AC_Long_Protocol_History.txt).

On a higher level: each button press on the remote makes it transmit the entire desired state of the AC. The state consists of two "frames" of 20 bytes.
Bytes are encoded using the Little Endian order.
Each frame has a header of 4 bytes that are static: (11 DA 27 00) and a checksum that is computed by summing 19 bytes of the frame and the result is inserted as 20th.

For information about each specific byte please refer to the Python implementation in [daikin_ac_state.py](../src/daikin_ac_state.py).