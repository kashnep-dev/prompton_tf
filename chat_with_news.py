import os

from langchain.callbacks.base import BaseCallbackHandler
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from langchain_core.tracers import LangChainTracer
from langchain_core.tracers.run_collector import RunCollectorCallbackHandler
from langsmith import Client

# Customize if needed
def configure_run():
    client = Client()
    ls_tracer = LangChainTracer(project_name=os.environ["LANGCHAIN_PROJECT"], client=client)
    run_collector = RunCollectorCallbackHandler()
    cfg = RunnableConfig()
    cfg["callbacks"] = [ls_tracer, run_collector]
    cfg["configurable"] = {"session_id": "any"}

    return client, run_collector, cfg


class StreamHandler(BaseCallbackHandler):
    def __init__(self, container, initial_text=""):
        self.container = container
        self.text = initial_text

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.text += token
        self.container.markdown(self.text)


# Set up memory
def make_prompt():
    template = """
            Answer the following questions as best you can. Please always answer the results in Korean.
            You have access to the following tools:
            #Additional information:
            - News articles should be written concisely, no longer than 300 words.
            - The summary should include the main content and key information of each article.
            - The summary must be written from an objective and neutral perspective.
            - Unnecessary information should be removed and only the core content should be extracted and written.

            #Print:
            - Summary results must be written in 300 words or less.
            - Please write the summary results in table form.
            - The source of the summary results for each article, the article creation date, and the source url must also be written.

            #Data Source:
            - You must definitely refer to 'items' of Grounding data
            - summary : You must definitely refer to description.
            - the article creation date : You must definitely refer to pubDate. Print the date format as follows: Example: March 28, 2024 9:30
            - source url : You must definitely refer to originallink.
            Grounding data: {context}
            Answer: 
        """

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", template),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )
    return prompt
