prerequisites

    source venv/bin/activate
    pip install -r requirements.txt

basic run

    pytest
    

alternately, run with ini file

    cp resources/pytest.ini-dist ./pytest.ini
    pytest

or use the whole docker stack

    cp docker-compose.override.yml-dist docker-compose.override.yml
    docker compose up -d --build
    docker compose run web pytest

you may want to skip slow tests:

    BHT_SKIP_SLOW=True python -m pytest tests

you may want to skip bht tests:

    BHT_SKIP_BHT=True python -m pytest tests

or allow ISTEX tests if you have IP authorisation

    BHT_SKIP_ISTEX=False python -m pytest tests
    # defaults to False, that is it wont run istex tests

or allow Selenium functional tests if available

    BHT_SKIP_SELENIUM=False python -m pytest tests
    # defaults to False, that is it wont run selenium tests

a whole test would then look like

    export BHT_SKIP_SLOW=False
    export BHT_SKIP_SELENIUM=False
    export BHT_SKIP_ISTEX=False
    export BHT_SKIP_BHT=False
    python -m pytest tests
