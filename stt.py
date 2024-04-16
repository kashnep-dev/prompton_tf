import os

import azure.cognitiveservices.speech as speechsdk
import speech_recognition as sr


def button_click():
    speech_key = 'f6d35f8af8cf4ed3912e532c186a93c2'
    speech_region = 'koreacentral'
    speech_language = 'ko-KR'
    # 음성 인식 엔진 초기화
    recognizer = sr.Recognizer()
    # Creates a recognizer with the given settings
    # Azure STT & TTS API key
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region,
                                           speech_recognition_language=speech_language)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

    print("알고 싶은 정보를 말씀해 주세요 >")

    # Starts speech recognition, and returns after a single utterance is recognized. The end of a
    # single utterance is determined by listening for silence at the end or until a maximum of 15
    # seconds of audio is processed.
    result = speech_recognizer.recognize_once()

    # Checks result.
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print("음성인식결과: {}".format(result.text))
    elif result.reason == speechsdk.ResultReason.NoMatch:
        print("일치하는 음성이 없습니다.: {}".format(result.no_match_details))
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("음성 인식이 취소되었습니다.: {}".format(
            cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                print("Error details: {}".format(
                    cancellation_details.error_details))
    return result

# root = tk.Tk()
# root.title("Voice Assistant")

# # 버튼 생성
# button = tk.Button(root, text="말씀하세요.", command=button_click)
# button.pack()

# root.mainloop()


# print(button_click())
