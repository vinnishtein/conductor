from flask import request
from app.controllers.auth_controller import AuthController
from library.engine.utils import json_response, cursor_to_list
from library.engine.cache import cached_function

open_ctrl = AuthController("open", __name__, require_auth=False)

@cached_function(positive_only=True)
def get_executer_data(query):
    from app.models import Project, Datacenter, Group, Host
    projects = Project.find(query)
    projects = cursor_to_list(projects)
    project_ids = [x["_id"] for x in projects]

    groups = Group.find({ "project_id": { "$in": project_ids }})
    groups = cursor_to_list(groups)
    group_ids = [x["_id"] for x in groups]

    hosts = Host.find({ "group_id": { "$in": group_ids }})
    hosts = cursor_to_list(hosts)

    datacenters = Datacenter.find({})
    datacenters = cursor_to_list(datacenters)

    return {
        "datacenters": datacenters,
        "projects": projects,
        "groups": groups,
        "hosts": hosts
    }


@open_ctrl.route("/executer_data")
def executer_data():
    query = {}
    if "projects" in request.values:
        project_names = [x for x in request.values["projects"].split(",") if x != ""]
        if len(project_names) > 0:
            query["name"] = { "$in": project_names }
    results = get_executer_data(query)
    return json_response({ "data": results })

@open_ctrl.route("/conductor")
def version():
    from app import app

    results = {
        "app": {
            "name": "conductor"
        }
    }
    if "VERSION" in dir(app):
        results["app"]["version"] = app.VERSION
    else:
        results["app"]["version"] = "unknown"

    from library.db import db
    results["mongodb"] = db.conn.client.server_info()

    import flask
    results["flask_version"] = flask.__version__

    from library.engine.cache import check_cache
    results["cache"] = {
        "type": app.cache.__class__.__name__,
        "active": check_cache()
    }

    results["endpoints"] = app.config.http["ROUTES"]

    return json_response({ "conductor_info": results })