import FinanceDataReader as fdr
import pandas as pd
import datetime

import warnings
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np

# 삼성전자 종목코드: '005930'
# 시작일: '2024-01-01'
# 종료일: 현재


start_date = datetime.datetime(datetime.datetime.now().year, 1, 1)
end_date = datetime.datetime.now()
today = '2024-04-09'
company_code = '005930'



# 올해 종가만 가져오는 함수
def get_yearly_close_price():
    close_list = fdr.DataReader(company_code, '2024-01-01')['Close'].values
    close_list = close_list.astype('str')
    close_str = ', '.join(close_list)
    return close_str

# 올해 전체 가격
def get_yearly_price():
    return fdr.DataReader(company_code, '2024-01-01')

# 현재 가격
def get_today_price():
    return fdr.DataReader(company_code, today, today)

# 올해 최저가
def get_yearly_low():
    return fdr.DataReader(company_code, '2024-01-01')['Close'].min()

# 올해 최고가
def get_yearly_high():
    return fdr.DataReader(company_code, '2024-01-01')['Close'].max()

# 올해 평균 종가
def get_avg_close():
    return fdr.DataReader(company_code, '2024-01-01')['Close'].mean()

# 향후 5일 간의 주가를 예측
class PatternFinder():
    def __init__(self, period=5):
        self.period = period

    def set_stock(self, code: str):
        self.code = code
        self.data = fdr.DataReader(code)
        self.close = self.data['Close']
        self.change = self.data['Change']
        return self.data

    def search(self, start_date, end_date, threshold=0.98):
        base = self.close[start_date:end_date]
        self.base_norm = (base - base.min()) / (base.max() - base.min())
        self.base = base

        #display(base)

        window_size = len(base)
        moving_cnt = len(self.data) - window_size - self.period - 1
        cos_sims = self.__cosine_sims(moving_cnt, window_size)

        self.window_size = window_size
        cos_sims = cos_sims[cos_sims > threshold]

        return cos_sims
        #return cos_sims.index[1]

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
        #plt.show()

        preds = self.change[idx + self.window_size: idx + self.window_size + period]
        #display(preds)
        #print(f'pred: {round(preds.mean()*100, 2)} % ')
        return f'{round(preds.mean()*100, 2)} % '

    def stat_prediction(self, result, period=5):
        idx_list = list(result.keys())
        mean_list = []
        for idx in idx_list:
            pred = self.change[idx + self.window_size: idx + self.window_size + period]
            mean_list.append(pred.mean())
        return np.array(mean_list)

