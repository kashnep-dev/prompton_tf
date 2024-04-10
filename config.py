import os

from langchain_core.runnables import RunnableConfig
from langchain_core.tracers import LangChainTracer
from langchain_core.tracers.run_collector import RunCollectorCallbackHandler
from langsmith import Client
import streamlit as st
# Customize if needed
def configure_run():
    client = Client()
    ls_tracer = LangChainTracer(project_name=os.environ["LANGCHAIN_PROJECT"], client=client)
    run_collector = RunCollectorCallbackHandler()
    cfg = RunnableConfig()
    cfg["callbacks"] = [ls_tracer, run_collector]
    cfg["configurable"] = {"session_id": "any"}

    st.session_state["client"] = client
    st.session_state["run_collector"] = run_collector
    st.session_state["cfg"] = cfg
