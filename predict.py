import FinanceDataReader as fdr
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from langchain.chains.conversation.base import ConversationChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import ChatPromptTemplate, \
    FewShotChatMessagePromptTemplate
from langchain_openai import ChatOpenAI


def get_company_code(question):
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0
    )
    examples = [
        {
            "input": "삼성전자의 종목코드는 뭐야?",
            "output": "032640"
        },

        {
            "input": "현재 삼성전자의 주식시장에서 종목코드는 어떻게 돼?",
            "output": "032640"
        }
    ]
    example_prompt = ChatPromptTemplate.from_messages(
        [
            ("human", "{input}"),
            ("ai", "{output}")
        ]
    )
    few_shot_promt = FewShotChatMessagePromptTemplate(
        examples=examples,
        example_prompt=example_prompt
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "너는 회사명을 한국 주식의 종목코드로 변환해주는 assistant야. browsing 기능을 사용해서라도 반드시 종목코드를 알려줘야해."),
            few_shot_promt,
            ("human", "{input}")
        ]
    )

    chain = prompt | llm
    chain.invoke({"input": question})

    conversation = ConversationChain(
        llm=llm,
        memory=ConversationBufferWindowMemory(k=1)
    )
    response = conversation.predict(
        input=prompt.format(input=question)
    )

    return response


####################################################################################


# 회사명 추출
def get_company_name(question):
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0
    )
    examples = [
        {
            "input": "삼성전자의 주가 시황 알려줘",
            "output": "삼성전자"
        },

        {
            "input": "현재 삼성전자의 주식 가격은 어때?",
            "output": "삼성전자"
        }
    ]
    example_prompt = ChatPromptTemplate.from_messages(
        [
            ("human", "{input}"),
            ("ai", "{output}")
        ]
    )
    few_shot_promt = FewShotChatMessagePromptTemplate(
        examples=examples,
        example_prompt=example_prompt
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You're an assistant that extracts only the company names from sentences."),
            few_shot_promt,
            ("human", "{input}")
        ]
    )

    chain = prompt | llm
    chain.invoke({"input": question})

    conversation = ConversationChain(
        llm=llm,
        memory=ConversationBufferWindowMemory(k=1)
    )
    response = conversation.predict(
        input=prompt.format(input=question)
    )

    return response


####################################################################################

class PatternFinder():
    def __init__(self, period=5):
        self.period = period

    def set_stock(self, code: str):
        self.code = code
        self.data = fdr.DataReader(code)
        self.close = self.data['Close']
        self.change = self.data['Change']
        return self.data

    def search(self, start_date, end_date, threshold=0.95):
        base = self.close[start_date:end_date]
        self.base_norm = (base - base.min()) / (base.max() - base.min())
        self.base = base

        # display(base)

        window_size = len(base)
        moving_cnt = len(self.data) - window_size - self.period - 1
        cos_sims = self.__cosine_sims(moving_cnt, window_size)

        self.window_size = window_size
        cos_sims = cos_sims[cos_sims > threshold]

        return cos_sims
        # return cos_sims.index[1]

    def __cosine_sims(self, moving_cnt, window_size):
        def cosine_similarity(x, y):
            return np.dot(x, y) / (np.sqrt(np.dot(x, x)) * np.sqrt(np.dot(y, y)))

        # 유사도 저장 딕셔너리
        sim_list = []

        for i in range(moving_cnt):
            target = self.close[i:i + window_size]

            # Normalize
            target_norm = (target - target.min()) / (target.max() - target.min())

            # 코사인 유사도 저장
            cos_similarity = cosine_similarity(self.base_norm, target_norm)

            # 코사인 유사도 <- i(인덱스), 시계열데이터 함께 저장
            sim_list.append(cos_similarity)
        return pd.Series(sim_list).sort_values(ascending=False)

    def plot_pattern(self, idx, period=5):
        if period != self.period:
            self.period = period

        top = self.close[idx:idx + self.window_size + period]
        top_norm = (top - top.min()) / (top.max() - top.min())

        plt.plot(self.base_norm.values, label='base')
        plt.plot(top_norm.values, label='target')
        plt.axvline(x=len(self.base_norm) - 1, c='r', linestyle='--')
        plt.axvspan(len(self.base_norm.values) - 1, len(top_norm.values) - 1, facecolor='yellow', alpha=0.3)
        plt.legend()
        # plt.show()

        preds = self.change[idx + self.window_size: idx + self.window_size + period]
        # display(preds)
        # print(f'pred: {round(preds.mean()*100, 2)} % ')
        return f'{round(preds.mean() * 100, 2)} % '

    def stat_prediction(self, result, period=5):
        idx_list = list(result.keys())
        mean_list = []
        for idx in idx_list:
            pred = self.change[idx + self.window_size: idx + self.window_size + period]
            mean_list.append(pred.mean())
        return np.array(mean_list)
