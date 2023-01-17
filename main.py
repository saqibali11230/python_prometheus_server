# uvicorn main:app --reload
import os
import json
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI()

filename = os.path.expanduser("~/targets.json")


class Data(BaseModel):
    job: Optional[str] = "qa1-monitoring"
    address: str
    docker_monitoring: Optional[bool] = False


@app.get("/")
def home():
    return {"data": "App is alive and healthy"}


@app.post("/api/config")
def write(data: Data):
    job = data.job
    host = data.address
    docker_monitoring = data.docker_monitoring
    if not host:
        raise HTTPException(status_code= 502, detail="address cannot be empty")
    nxp_host = f"{host}:9100"
    doc_host = f"{host}:9101"
    doc_job = "prom-docker"
    if job is not None:
        pre = job.split("-")[0]
        if "qa" in pre or "dev" in pre or "prod" in pre:
            doc_job = f"{pre}-docker"
    new_data = []
    with open(filename) as f:
        temp = json.load(f)
        find = next((i for i in temp if i["labels"]["job"] == job), None)
        if find:
            check = nxp_host in find["targets"]
            if check:
                new_data.extend(temp)
            else:
                find["targets"].append(nxp_host)
                new_data.extend(temp)
        else:
            new_job = {"targets": [nxp_host], "labels": {"env": "prod", "job": job}}
            temp.append(new_job)
            new_data.extend(temp)

        if docker_monitoring:
            find_djob = next((i for i in temp if i["labels"]["job"] == doc_job), None)
            if find_djob:
                check = doc_host in find_djob["targets"]
                if not check:
                    find_djob["targets"].append(doc_host)
            else:
                new_djob = {
                    "targets": [doc_host],
                    "labels": {"env": "prod", "job": doc_job},
                }
                new_data.append(new_djob)
    with open(filename, "w") as f:
        json.dump(new_data, f, indent=2)
    return {"success": True, "msg": "Prometheus updated successfully!"}
