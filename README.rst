=====
drought
=====

Process and display drought data.
Optional Module for ISDC

Quick start
-----------

1. Add "drought" to your DASHBOARD_PAGE_MODULES setting like this::

    DASHBOARD_PAGE_MODULES = [
        ...
        'drought',
    ]

    If necessary add "drought" in (check comment for description): 
        QUICKOVERVIEW_MODULES, 
        MAP_APPS_TO_DB_CUSTOM

    For development in virtualenv add DROUGHT_PROJECT_DIR path to VENV_NAME/bin/activate:
        export PYTHONPATH=${PYTHONPATH}:\
        ${HOME}/DROUGHT_PROJECT_DIR

2. To create the drought tables:

   python manage.py makemigrations
   python manage.py migrate drought --database geodb

