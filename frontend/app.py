"""
Frontend flask app, serves the graphical html version
and provides endpoints for getting/pushing quotes.
"""
import os
import random
import socket
import logging
import requests
from kubernetes import client as kubernetes_client
from kubernetes import config as kubernetes_config
from flask import Flask, render_template, jsonify, request
from flask.wrappers import Response
from flask.logging import create_logger
from flask_healthz import healthz
from quotes import default_quotes

# configure logging
logging.basicConfig(level=logging.INFO)

# create the flask app
APP = Flask(__name__)
log = create_logger(APP)

# add flask-healthz config to flask config
APP.config["HEALTHZ"] = {"live": "healthz.liveness", "ready": "healthz.readiness"}
# create the healthz endpoints
APP.register_blueprint(healthz, url_prefix="/healthz")


# Read environment variables
BACKEND_HOST = os.environ.get("backend_host", False)
BACKEND_PORT = os.environ.get("backend_port", False)
# host for the backend, if not set default to False
BACKEND_ENDPOINT = bool(BACKEND_HOST and BACKEND_PORT)
# build the url for the backend
BACKEND_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"
# whether the container is running in kubernetes, assumes that it is
NOT_RUNNING_IN_KUBERNETES = bool(os.environ.get("not_running_in_kubernetes", False))


def check_backend_endpoint_env_var() -> bool:
    """Checks if the user has set the backend host environment variable"""
    if BACKEND_ENDPOINT:
        log.info(
            str.format(
                "Found 'backend_host' environment variable, will attempt to connect to the backend on: %s", BACKEND_URL
            )
        )
        return True
    log.warning("'backend_host' environment variable not set, set this to connect to the backend.")
    return False


def check_if_database_is_available() -> bool:
    """Check if the database is reachable and should be used"""
    # check if the env var has been set
    if check_backend_endpoint_env_var():
        # try querying the backend
        try:
            backend_health_endpoint = f"{BACKEND_URL}/check-db-connection"
            response = requests.get(backend_health_endpoint, timeout=1)
            if response.status_code == 200:
                body = response.json()
                if "db-connected" in body:
                    if body["db-connected"] == "true":
                        return True
                    return False
            else:
                return False
            return False
        except (requests.ConnectionError, KeyError):
            return False
    else:
        return False


def check_if_backend_is_available() -> bool:
    """Check if the backend is reachable and should be used"""
    # check if the env var has been set
    if BACKEND_ENDPOINT:
        # try querying the backend
        try:
            backend_health_endpoint = f"{BACKEND_URL}/healthz/ready"
            response = requests.get(backend_health_endpoint, timeout=1)
            return response.status_code == 200
        except requests.ConnectionError:
            return False
    else:
        return False


def get_random_quote_from_backend() -> str:
    """get a single quote from the backend"""
    response = requests.get(f"{BACKEND_URL}/quote", timeout=1)
    if response.status_code == 200:
        return response.text
    log.error("did not get a response 200 from backend")
    return ""


def get_all_quotes_from_backend() -> list[str]:
    """get list of all quotes form the backend"""
    response = requests.get(f"{BACKEND_URL}/quotes", timeout=1)
    if response.status_code == 200:
        return response.json()
    log.error("did not get a response 200 from backend")
    return []


@APP.route("/")
def index():
    """Main endpoint, serves the frontend"""
    # check if the backend and database are available and communicate this to user
    backend_available = check_if_backend_is_available()
    # check if the backend is communicating with the database
    database_available = check_if_database_is_available()

    if backend_available:
        _quotes = get_all_quotes_from_backend()
    else:
        _quotes = default_quotes

    frontend_hostname, backend_hostname = get_hostnames()
    # render the html template with arguments
    return render_template(
        "index.html",
        backend=backend_available,
        database=database_available,
        quotes=_quotes,
        frontend_hostname=frontend_hostname,
        backend_hostname=backend_hostname,
    )


@APP.route("/random-quote")
def random_quote():
    """return a random quote"""
    if check_if_backend_is_available():
        #  return random.choice(get_all_quotes_from_backend())
        return get_random_quote_from_backend()
    return random.choice(default_quotes)


@APP.route("/quotes")
def quotes():
    """Get all available quotes as JSON"""
    if check_if_backend_is_available():
        return jsonify(get_all_quotes_from_backend())
    return jsonify(default_quotes)


@APP.route("/add-quote", methods=["POST"])
def add_quote():
    """receive quote and pass it on to the backend"""
    log.info("attempting to add new quote to backend ...")
    if request.method == "POST":
        request_json = request.get_json()
        log.info(f"recieved JSON: {request_json}")

        if "quote" in request_json:
            url = f"{BACKEND_URL}/add-quote"
            try:
                res = requests.post(url, json=request_json, timeout=1)
                if res.status_code == 200:
                    log.info("new quote successfully posted to backend.")
                    return "Quote received", 200
                log.error("could not successfully post new quote to backend.")
                return "error inserting quote", 500
            except (requests.ConnectionError, KeyError) as err:
                log.error("encountered error when trying to pass quote to backend:")
                log.error(err)
                return "error inserting quote", 500
        else:
            log.error("could not find 'quote' in request")
            return "No 'quote' key in JSON", 500
    return "Could not parse quote", 500


def get_hostnames() -> tuple[str, str]:
    """returns tuple of (frontend_hostname, backend_hostname)"""
    log.info("Attempting to get backend hostname ...")
    frontend_hostname = socket.gethostname()
    if check_if_backend_is_available():
        try:
            response = requests.get(f"{BACKEND_URL}/hostname", timeout=1)
            if response.status_code == 200:
                resp_json = response.json()
                log.debug(resp_json)
                if "backend" in resp_json:
                    backend_hostname = resp_json["backend"]
                    return (frontend_hostname, backend_hostname)
        except (requests.ConnectionError, KeyError) as err:
            log.error("Encountered an error trying to get hostname from backend: ")
            log.error(err)
            return (frontend_hostname, None)
    log.error("did not get a response 200 from backend")
    return (frontend_hostname, None)


@APP.route("/hostname")
def hostname():
    """return the hostname of the given container"""
    frontend_hostname, backend_hostname = get_hostnames()
    hostnames = {"frontend": frontend_hostname, "backend": backend_hostname}
    return jsonify(hostnames)
