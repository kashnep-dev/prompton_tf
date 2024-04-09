
def getPrompt():
    '''
    올해 최저가/최고가/평균가를 구하는 프롬프트
    '''

    # 페르소나
    persona = "너의 페르소나는 주식 애널리스트야. 반드시 애널리스트처럼 생각하고 행동해야돼. "

    # 맥락
    context = "나는 주식투자를 해본 적 없고, 주식투자를 통해 자산을 늘려보려고 해. "

    #작업
    task = "해당 기간 동안의 최저가, 최고가, 평균가를 알려줘. "

    #예시
    example = ""

    #형식
    form = ""

    #어조
    tone = "확실하게 이해할 수 있도록 전문 애널리스트 톤으로 대답해줘."

    prompt = persona + context + task + example + form + tone


    return prompt


def getPredictPrompt():
    '''
    향후 5일 간의 주가를 예측하는 프롬프트
    '''

    # 페르소나
    persona = "너의 페르소나는 주식 차트 전문가야. 반드시 주식 차트 전문가처럼 생각하고 행동해야돼. "

    # 맥락
    context = "나는 주식투자를 해본 적 없고, 차트 분석을 통해 주식투자를 할 예정이야. "

    #작업
    task = "해당 기간 동안의 종가를 기준으로 해당 회사의 2010년부터 현재까지 주식그래프와 코싸인 유사도를 비교해보고 자기 자신을 제외한 가장 유사도가 높은 그래프를 가지고 와서 향후 5일 간의 주가 그래프를 그려줘. "

    #예시
    example = ""

    #형식
    form = ""

    #어조
    tone = "확실하게 이해할 수 있도록 주식 차트 전문가 톤으로 대답해줘."

    prompt = persona + context + task + example + form + tone


    return prompt