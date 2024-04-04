from dotenv import load_dotenv
from search import search_by_bing
import prompt as pt

# 1. 환경변수를 읽어온다.
load_dotenv()

# 2. bing 검색을 한다.
param = "삼성전자"

url_list = search_by_bing(param)

docs = pt.load_by_web(url_list)

vectorstore = pt.make_vectorstore(docs)

rag_chain = pt.make_llm_chain(param, vectorstore)

print(
    rag_chain.invoke(
        "삼성전자 최신 뉴스를 요약해주세요."
    )  # 문서에 대한 질의를 입력하고, 답변을 출력합니다.
)