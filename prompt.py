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
def make_prompt_by_api(type):
    template = ''
    if type == '종목뉴스 요약':
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
    elif type == '재무정보 요약':
        template = """
            <glossary>
                해당 내용을 알기 위해서는 기업 재무재표를 제대로 이해하고 있어야 합니다.
                제공되는 문서는 {{기업}}에 대한 재무재표를 Json 형식입니다.
                재무제표는 대차대조표(재무상태표), 손익계산서, 현금흐름표로 나타냅니다.
                대차대조표(재무상태표)를 통해 기업의 자본 및 부채 비율을 확인할 수 있습니다.
                자산총계 = 부채총계 + 자본총계 입니다.
                손익계산서는 수주(매출액), 영업이익, 당기순이익(손실)로 확인할 수 있습니다.
                </glossary>
                <context>
                </context>
                <instruction>
                위에 json은 특정회사에 재무정보입니다.
                재무정보를 요약할때는 매출연도, 수주(매출액), 영업이익, 당기순이익을 알려줘.
                입력받은 {{thstrm_nm}} 값은 최근 3년치 정보입니다.
                수주(매출액) = 매출액 = 영업수익 = 매출및지분법손익 = 매출
                영업이익 = 영업이익(손실)
                당기순이익(손실) = 당기순이익
                {{thstrm_nm}} 값을 이용하여 최근 3년치 정보를 표로 생성해줘.
                금액은 백만원 단위로 해.
                표 이후에는 최근 1년치에 대한 매출연도, 수주(매출액), 영업이익, 당기순이익을 말로써 설명해줘.
                ###
                매출연도는 2023년 형식으로 표기해줘
                ###
                </instruction>
                <user>
                {question}
                </user>
        """
    elif type == '주식정보 분석':
        template = """
        올해 최저가/최고가/평균가를 구하는 프롬프트
        너의 페르소나는 주식 애널리스트야. 반드시 애널리스트처럼 생각하고 행동해야돼.
        나는 주식투자를 해본 적 없고, 주식투자를 통해 자산을 늘려보려고 해.
        해당 기간 동안의 최저가, 최고가, 평균가를 알려줘.
        확실하게 이해할 수 있도록 전문 애널리스트 톤으로 대답해줘.
        """
        # 향후 5일 간의 주가를 예측하는 프롬프트
        # 너의 페르소나는 주식 차트 전문가야. 반드시 주식 차트 전문가처럼 생각하고 행동해야돼.
        # 나는 주식투자를 해본 적 없고, 차트 분석을 통해 주식투자를 할 예정이야.
        # 해당 기간 동안의 종가를 기준으로 해당 회사의 2010년부터 현재까지 주식그래프와 코싸인 유사도를 비교해보고 자기 자신을 제외한 가장 유사도가 높은 그래프를 가지고 와서 향후 5일 간의 주가 그래프를 그려줘.
        # 확실하게 이해할 수 있도록 주식 차트 전문가 톤으로 대답해줘.
        
        

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", template),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )
    return prompt
