import pytest
import os

from web import create_app

skip_slow_test = pytest.mark.skipif(
    os.environ.get("BHT_SKIPSLOWTESTS") is not None, reason="Slow test skipping"
)


@pytest.fixture(scope="module")
def test_client():
    flask_app = create_app()

    # Create a test client using the Flask application configured for testing
    with flask_app.test_client() as testing_client:
        # Establish an application context
        with flask_app.app_context():
            yield testing_client  # this is where the testing happens!
