import pytest
import os

skip_slow_test = pytest.mark.skipif(
    os.environ.get("BHT_SKIPSLOWTESTS") is not None, reason="Slow test skipping"
)
