import os
from web import create_app

# FLASK_ENV is deprecated
# Set BHT_ENV  to choose your configuration
bht_env = os.environ.get("BHT_ENV")
app = create_app(bht_env)
