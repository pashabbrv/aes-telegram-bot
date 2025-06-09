from yandex_cloud_ml_sdk import YCloudML
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("YANDEX_API_KEY")
folder_id = os.getenv("YANDEX_FOLDER_ID")

sdk = YCloudML(
    folder_id=folder_id,
    auth=api_key,
)

def llm_censor(question):
    model = sdk.models.text_classifiers("yandexgpt").configure(
        task_description="Запрос связан с незаконными действиями, политикой, войной, наркотиками, провокацией и тд",
        labels=["Нет", "Да"]
    )

    result = model.run(question)
    best_label = max(result, key=lambda x: x.confidence)
    return best_label.label
 
def llm_validator(response):
    model = sdk.models.text_classifiers("yandexgpt").configure(
        task_description="В ответе LLM имеется ya.ru",
        labels=["Нет", "Да"]
    )

    result = model.run(response)
    best_label = max(result, key=lambda x: x.confidence)
    return best_label.label
