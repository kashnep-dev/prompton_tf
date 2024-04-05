from dotenv import load_dotenv

import prompt as pt
from search import search_by_naver_api

# 1. 환경변수를 읽어온다.
load_dotenv()

# 2. naver 뉴스 api 검색을 한다.
param = "LG유플러스"

# 3. naver 뉴스 api 결과를 가져온다.
json_str = search_by_naver_api(param)

# 4. api 결과를 JSONLoader로 읽어온다.
docs = pt.load_by_json(json_str)

# 5. 벡터스토어를 생성한다.
vectorstore = pt.make_vectorstore(docs)

# 6. llm chain을 생성한다.
rag_chain = pt.make_llm_chain(param, vectorstore)

# 7. 질의를 입력하고, 답변을 출력한다.
print(
    rag_chain.invoke(
        "LG유플러스 관련 뉴스를 요약해주세요."
    )  # 문서에 대한 질의를 입력하고, 답변을 출력합니다.
)
