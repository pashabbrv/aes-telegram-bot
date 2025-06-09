import os
import boto3
import time
from yandex_cloud_ml_sdk import YCloudML
from langchain_community.embeddings.yandex import YandexGPTEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from llm_judge import llm_censor, llm_validator
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Конфигурация Qdrant
qdrant_url = os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")

# Инициализация YandexCloud параметров и эмбеддингов YandexGPT
api_key = os.getenv("YANDEX_API_KEY")
folder_id = os.getenv("YANDEX_FOLDER_ID")
embeddings = YandexGPTEmbeddings(api_key=api_key, folder_id=folder_id)

# Инициализация Llama из YandexCloud
sdk = YCloudML(
        folder_id=folder_id,
        auth=api_key,
    )
llama_model = sdk.models.completions("llama").configure(
    temperature=0.5,
    max_tokens=500,
).langchain(model_type="chat")

# Конфигурация S3 (Yandex Bucket)
aws_access_key_id = os.getenv("AWS_ACCESS_KEY")
aws_secret_access_key = os.getenv("AWS_SECRET_KEY")
bucket_name = os.getenv("YANDEX_BUCKET_NAME")

# Инициализация клиента Qdrant
qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
collection_name = "documents"

def create_collection_if_not_exists():
    """Создать коллекцию, если она не существует."""
    try:
        qdrant_client.get_collection(collection_name)
        print(f"Коллекция '{collection_name}' уже существует.")
        return True
    except Exception:
        print(f"Создаём коллекцию '{collection_name}' в Qdrant.")
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config={"size": 256, "distance": "Cosine"}
        )
        return False

def load_pdfs_from_s3(bucket_name):
    """Загрузить все PDF-файлы из S3 бакета."""
    documents = []
    session = boto3.session.Session()
    s3 = session.client(
        service_name='s3',
        endpoint_url='https://storage.yandexcloud.net',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get('Contents', []):
            if obj['Key'].endswith(".pdf"):
                download_path = os.path.join(os.getcwd(), os.path.basename(obj['Key']))
                with open(download_path, 'wb') as f:
                    s3.download_fileobj(bucket_name, obj['Key'], f)
                loader = PyPDFLoader(download_path)
                documents.extend(loader.load())
                os.remove(download_path)
    return documents

def load_or_create_qdrant(bucket_name):
    """Загружает данные в Qdrant только если коллекция не существует."""
    if create_collection_if_not_exists():
        print("Коллекция уже существует, пропускаем загрузку из S3.")
        return
    
    print("Загружаем данные из S3 в Qdrant.")
    documents = load_pdfs_from_s3(bucket_name)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)
    
    points = []
    for i, text in enumerate(texts):
        time.sleep(0.1)
        
        point = PointStruct(
            id=i,
            vector=embeddings.embed_documents([text.page_content])[0],
            payload={"text": text.page_content}
        )
        points.append(point)
    
    qdrant_client.upsert(collection_name=collection_name, points=points)

def clean_text(text):
    """Удаляет спецсимволы и приводит текст к читаемому виду."""
    return text.replace("\n", " ").replace("\\n", " ").replace('"', '').strip()

def LLM_chain(question):
    """Основная функция для обработки запроса и возвращения ответа."""
    load_or_create_qdrant(bucket_name)
    info = "\n\nЕсли не нашли ответ на свой вопрос, воспользуйтесь сайтом: https://pish.etu.ru/. Или задайте вопрос менеджеру программы."

    if llm_censor(question) == "Да":
        return "Я не могу отвечать на такие вопросы, извини." + info
    
    query_vector = embeddings.embed_documents([question])[0]
    
    search_result = qdrant_client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=10
    ).points

    if search_result:
        context = "\n".join([clean_text(result.payload["text"]) for result in search_result])
        #print(f"Контекст для запроса: {context[:300]}...")

        template = """Ты ассистент по вопросам, связанным с ПИШ(передовой инженерной школой) ЛЭТИ. Отвечай в контексте ПИШ ЛЭТИ.
        ПИШ имеет бакалавриат, магистратуру, дополнительное образование и является проектом ЛЭТИ.
        Используй предоставленный контекст для ответа. Не упоминай контекст в ответе. Дай ответ максимум в 450 токенов.
        ВАЖНО! Всегда давай развернутый ответ на вопросы абитуриента.
        Контекст: {context}
        Вопрос: {question}
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = (
            {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
            | prompt
            | llama_model
            | StrOutputParser()
        )
        
        response = chain.invoke({"context": context, "question": question})

        validation = llm_validator(response)
        print(validation)

        if validation == "Да":
            search_result = qdrant_client.query_points(
                collection_name=collection_name,
                query=query_vector,
                limit=1
            ).points
            context = "\n".join([clean_text(result.payload["text"]) for result in search_result])

            template = """Ты ассистент по вопросам, связанным с ПИШ(передовой инженерной школой) ЛЭТИ.
            ПИШ имеет бакалавриат, магистратуру, дополнительное образование и является проектом ЛЭТИ.
            Отвечай используя обычную логику, свою базу знаний и знания о процессе обучения в ВУЗах.
            Можешь общаться с пользователем, но не давай ему информацию о чем-то не связанном с ПИШ ЛЭТИ.
            ВАЖНО! Всегда давай развернутый ответ на вопросы абитуриента.
            Контекст: {context}
            Вопрос: {question}
            """
            
            prompt = ChatPromptTemplate.from_template(template)
            chain = (
                {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
                | prompt
                | llama_model
                | StrOutputParser()
            )
            response = chain.invoke({"context": context, "question": question})
            
    else:
        return "Не получилось ничего найти по данному запросу." + info
    
    return response + info

if __name__ == "__main__":
    # Тестовые вопросы
    questions = ["как поступить на военную кафедру"]
    for question in questions:
        print(f"\nВопрос: {question}")
        answer = LLM_chain(question)
        print(f"Ответ: {answer}")