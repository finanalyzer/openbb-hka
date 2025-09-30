from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from core.registry import register_widget, WIDGETS, add_template, TEMPLATES, load_agent_config
from core.config import config
from routes.charts import charts_router
from routes.equity_cn import equity_cn_router
from routes.equity_hk import equity_hk_router
from routes.agents import agents_router
import logging
from mysharelib.tools import setup_logger

setup_logger(__name__)
logger = logging.getLogger(__name__)

app = FastAPI(title=config.title,
    description=config.description,
    version="0.1.2")

origins = [
    "https://pro.openbb.co",
    "http://localhost:1420"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Info": f"{config.description}"}

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy"}

app.include_router(
    charts_router,
    prefix="/charts",
)

app.include_router(
    equity_cn_router,
    prefix="/cn",
)
add_template("cn")

app.include_router(
    equity_hk_router,
    prefix="/hk",
)
add_template("hk")

app.include_router(
    agents_router,
    prefix="/a",
)

@app.get("/agents.json")
def get_agents_config():
    """Agents configuration file for the OpenBB Workspace"""
    return JSONResponse(load_agent_config())

# Apps configuration file for the OpenBB Workspace
# it contains the information and configuration about all the
# apps that will be displayed in the OpenBB Workspace
@app.get("/apps.json")
def get_apps():
    """Apps configuration file for the OpenBB Workspace
    
    Returns:
        JSONResponse: The contents of apps.json file
    """
    # Read and return the apps configuration file
    return list(TEMPLATES.values())

# Endpoint that returns the registered widgets configuration
# The WIDGETS dictionary is maintained by the registry.py helper
# which automatically registers widgets when using the @register_widget decorator
@app.get("/widgets.json")
def get_widgets():
    """Returns the configuration of all registered widgets
    
    The widgets are automatically registered through the @register_widget decorator
    and stored in the WIDGETS dictionary from registry.py
    Returns:
        dict: The configuration of all registered widgets
    Issue:
    Refer to the issue below for more details about authentication header
    https://github.com/OpenBB-finance/OpenBB/issues/7175
    """
    return WIDGETS

