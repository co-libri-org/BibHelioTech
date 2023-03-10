
alternately, run with ini file

    cp resources/pytest.ini-dist ./pytest.ini
    pytest

or use the whole docker stack

    cp docker-compose.override.yml-dist docker-compose.override.yml
    docker compose up -d --build
    docker compose run web pytest

you may want to skip slow tests:

    BHT_SKIPSLOWTESTS=True python -m pytest tests

you may want to skip bht tests:

    BHT_DONTSKIPBHT=True python -m pytest tests

or allow ISTEX tests if you have IP authorisation

    BHT_DONTSKIPISTEX=True python -m pytest tests
    # defaults to False, that is it wont run istex tests

or allow Selenium functionnal tests if available

    BHT_DONTSKIPSELENIUM=True python -m pytest tests
    # defaults to False, that is it wont run selenium tests

a whole test would then look like

    export BHT_DONTSKIPSELENIUM=True
    export BHT_DONTSKIPISTEX=True
    export BHT_SKIPSLOWTESTS=False
    export BHT_DONTSKIPBHT=True
    python -m pytest tests
