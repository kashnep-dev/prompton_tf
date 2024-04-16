import os

from langchain_core.runnables import RunnableConfig
from langchain_core.tracers import LangChainTracer
from langchain_core.tracers.run_collector import RunCollectorCallbackHandler
from langsmith import Client


def ls_configure():
    client = Client()
    ls_tracer = LangChainTracer(project_name=os.getenv("LANGCHAIN_PROJECT"), client=client)
    run_collector = RunCollectorCallbackHandler()
    cfg = RunnableConfig()
    cfg["callbacks"] = [ls_tracer, run_collector]
    cfg["configurable"] = {"session_id": "any"}

    return client, run_collector, cfg
