import requests
from bs4 import BeautifulSoup
from openai import AzureOpenAI

def search_by_bing(param):
    search_url = "https://www.bing.com/news/search?q={0}&qft=interval%3d%228%22&form=PTFTNR".format(param)
    html_doc = requests.get(search_url)
    soup = BeautifulSoup(html_doc.text, "html.parser")

    news_list = soup.select("div[id='algocore']>div")

    url_list = []
    if len(news_list) > 0:
        for news_card in news_list:
            if "hankyung" not in news_card and "yna" not in news_card:
                print(news_card.attrs['data-url'])
                url_list.append(news_card.attrs['data-url'])
                if len(url_list) > 19: break
    else:
        print("No Results")
    return url_list