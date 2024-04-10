import os

from langchain.callbacks.base import BaseCallbackHandler
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from langchain_core.tracers import LangChainTracer
from langchain_core.tracers.run_collector import RunCollectorCallbackHandler
from langsmith import Client
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS, Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_transformers import LongContextReorder
import embeddings
import retriever
from langchain_core.runnables import (
    RunnableLambda
)


class StreamHandler(BaseCallbackHandler):
    def __init__(self, container, initial_text=""):
        self.container = container
        self.text = initial_text

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.text += token
        self.container.markdown(self.text)


# Set up memory
def make_prompt_by_api(type, st):
    template = ''
    if type == '종목뉴스 요약':
        template = """
            당신은 대한민국 경제 전문가입니다. 반드시 대한민국 경제 전문가처럼 생각하고 행동해야 합니다. 결과는 항상 한국어로 답변해주세요
            다음 지시사항을 참고하세요
            <glossary>
                - 요약에는 각 기사의 주요 내용과 핵심 정보가 포함되어야 합니다
                - 요약은 객관적이고 중립적인 관점에서 작성되어야 합니다
                - 중복 정보는 제외하고 핵심 내용만 추출하여 작성해야 합니다
                #출력 기준:
                    - 반드시 grounding data를 참고하시기 바랍니다
                    - 주요 키워드는 최대 5개까지만 작성해주세요
                    - 작성일은 한국 시간 기준 연월일시분초로 작성해주세요
                    - 출처 URL은 해당 기사의 URL을 작성해주세요
                    - 요약 결과를 순번, 요약, 주요 키워드, 출처, 작성일, 출처 URL의 헤더를 가지는 표 형식으로 작성해주세요
            </glossary>
            <grounding data>
                {context}
            </grounding data>
            답변:
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
                {context}
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
        너의 페르소나는 주식 애널리스트야. 반드시 애널리스트처럼 생각하고 행동해야돼.
        나는 주식투자를 해본 적 없고, 주식투자를 통해 자산을 늘려보려고 해.
        해당 기간 동안의 최저가, 최고가, 평균가를 알려줘.
        확실하게 이해할 수 있도록 전문 애널리스트 톤으로 대답해줘.
        <context>
            {context}
        </context>
        질문 : {question}
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
    stream_handler = StreamHandler(st.empty())
    llm = ChatOpenAI(model='gpt-3.5-turbo', streaming=True, callbacks=[stream_handler])
    chain = prompt | llm
    return chain

def make_prompt_by_file(f, st, status):
    template = """
    당신은 증권사 약관 분석 전문가입니다. 반드시 증권사 약관 분석 전문가처럼 생각하고 행동해야합니다. 결과는 항상 한국어로 답변해주세요.
    <glossary>
        - context에 있는 내용을 참고하여 약관을 분석해주세요.
        - 모든 결과는 반드시 출처와 함께 제공되어야 합니다.
    </glossary>
    <context>
     {context}
    </context>
    질문 : {question}
    답변 : 
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", template),
            # MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]
    )

    loader = PDFPlumberLoader(f)
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=50)
    splits = text_splitter.split_documents(docs)
    st.write("① 임베딩 생성")
    status.update(label="① 임베딩을 생성 중..🔥", state="running")
    # Embedding 생성
    embedding = embeddings.embedding_factory()
    st.write("② DB 인덱싱")
    status.update(label="② DB 인덱싱 생성 중..🔥", state="running")
    # VectorStore 생성
    faiss = FAISS.from_documents(splits, embedding["faiss"])
    
    st.write("③ Retriever 생성")
    status.update(label="③ Retriever 생성 중..🔥", state="running")

    # FAISSRetriever 생성
    faiss_retriever = faiss.as_retriever()
    stream_handler = StreamHandler(st.empty())
    llm = ChatOpenAI(model='gpt-3.5-turbo', streaming=True, callbacks=[stream_handler])
    chain = (
                {
                    "context": faiss_retriever,
                    "question": RunnablePassthrough(),
                }
                | prompt
                | llm
    )
    st.session_state["chain"] = chain
    st.write("완료 ✅")
    status.update(label="완료 ✅", state="complete", expanded=False)
    st.markdown(f'💬 `{st.session_state["uploaded_file"].name}`')
    st.markdown(
        "🔔참고\n\n**새로운 파일** 로 대화를 시작하려면, `새로고침` 후 진행해 주세요"
    )
