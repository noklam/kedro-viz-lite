# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_core.ipynb.

# %% auto 0
__all__ = ['prepare_dag_json', 'run_viz_lite']

# %% ../nbs/00_core.ipynb 3
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import multiprocessing
import kedro_viz
import orjson
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, ORJSONResponse
from kedro.io.data_catalog import DataCatalog
from kedro_viz.api import apps
from kedro_viz.api.rest.responses import (EnhancedORJSONResponse,
                                          get_default_response)
from kedro_viz.constants import DEFAULT_HOST, DEFAULT_PORT
from kedro_viz.data_access import data_access_manager
from kedro_viz.integrations.kedro.data_loader import load_data
from kedro_viz.launchers.jupyter import (_DATABRICKS_HOST, _VIZ_PROCESSES,
                                         _is_databricks, _allocate_port)
from kedro_viz.launchers.utils import _wait_for, _check_viz_up,_is_localhost, _start_browser
from kedro_viz.server import *
from kedro_viz.launchers.jupyter import *
def prepare_dag_json(pipelines, path=None):


    catalog = DataCatalog()  # TODO: can take custom data catalog
    if not isinstance(pipelines, dict):
        pipelines = dict(default=pipelines)
    populate_data(data_access_manager, catalog, pipelines, None, {})

    default_response = get_default_response()
    jsonable_default_response = jsonable_encoder(default_response)
    encoded_default_response = EnhancedORJSONResponse.encode_to_human_readable(
        jsonable_default_response
    )
    if not path:
        path = "dag.json"
    Path(path).write_bytes(encoded_default_response)
    app = apps.create_api_app_from_project(".", False)

# %% ../nbs/00_core.ipynb 4
def run_viz_lite(load_file, port=None, host=None) -> None:
    """
    Line magic function to start kedro viz. It calls a kedro viz in a process and displays it in
    the Jupyter notebook environment.

    Args:
        port: TCP port that viz will listen to. Defaults to 4141.
        local_ns: Local namespace with local variables of the scope where the line magic
            is invoked. This argument must be in the signature, even though it is not
            used. This is because the Kedro IPython extension registers line magics with
            needs_local_scope.
            https://ipython.readthedocs.io/en/stable/config/custommagics.html

    """
    port = port or DEFAULT_PORT  # Default argument doesn't work in Jupyter line magic.
    host = _DATABRICKS_HOST if _is_databricks() else DEFAULT_HOST
    port = _allocate_port(
        host, start_at=int(port)
    )  # Line magic provides string arguments by default, so we need to convert to int.

    if port in _VIZ_PROCESSES and _VIZ_PROCESSES[port].is_alive():
        _VIZ_PROCESSES[port].terminate()


    viz_process = multiprocessing.Process(
        target=run_server,
        daemon=True,
        kwargs={"load_file": load_file, "port": port, "host": host},
    )

    viz_process.start()
    _VIZ_PROCESSES[port] = viz_process

    _wait_for(func=_check_viz_up, host=host, port=port)

    if _is_databricks():
        _display_databricks_html(port)
    else:
        wrapper = f"""
                <html lang="en"><head></head><body style="width:100; height:100;">
                <iframe src="http://{host}:{port}/" height=500 width="100%"></iframe>
                </body></html>"""
        display(HTML(wrapper))

