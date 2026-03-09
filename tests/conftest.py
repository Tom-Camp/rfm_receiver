import sys
from unittest.mock import MagicMock

# Mock hardware/CircuitPython modules that require physical hardware before
# any import of rfm_receiver, so tests can run on a standard machine.
for _mod in ["board", "busio", "digitalio", "adafruit_rfm9x"]:
    sys.modules[_mod] = MagicMock()
