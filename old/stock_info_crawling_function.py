import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta

# 삼성전자 종목코드: '005930'
# 시작일: '2024-01-01'
# 종료일: 현재


start_date = datetime(datetime.now().year, 1, 1)
end_date = datetime.now()

company_code = '005930'

today = datetime.now().strftime("%Y-%m-%d")
one_week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
print(start_date,  end_date, today, one_week_ago)

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

