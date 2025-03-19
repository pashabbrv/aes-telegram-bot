import os
import pickle
import time
import boto3
import string
from langchain_community.llms import YandexGPT
from langchain_community.embeddings.yandex import YandexGPTEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv
from .text_information import STOP_WORDS

# Загрузка переменных окружения
load_dotenv()

# Конфигурация Qdrant
qdrant_url = os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")

# Инициализация YandexGPT и эмбеддингов
api_key = os.getenv("YANDEX_API_KEY")
folder_id = os.getenv("YANDEX_FOLDER_ID")
embeddings = YandexGPTEmbeddings(api_key=api_key, folder_id=folder_id)
yandex_gpt = YandexGPT(api_key=api_key, folder_id=folder_id)

# Конфигурация S3
aws_access_key_id = os.getenv("AWS_ACCESS_KEY")
aws_secret_access_key = os.getenv("AWS_SECRET_KEY")
bucket_name = os.getenv("YANDEX_BUCKET_NAME")

# Инициализация клиента Qdrant
qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
collection_name = "documents"

# Инициализация клиента S3 для Yandex Cloud
session = boto3.session.Session()
s3 = session.client(
    service_name='s3',
    endpoint_url='https://storage.yandexcloud.net',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)

# Функции для Яндекс Бакета
def list_files_in_s3(bucket_name):
    """Получить список файлов в S3 бакете."""
    file_keys = []
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get('Contents', []):
            file_keys.append(obj['Key'])
    return file_keys

def download_file_from_s3(bucket_name, key, download_path):
    """Загрузить файл из S3."""
    with open(download_path, 'wb') as f:
        s3.download_fileobj(bucket_name, key, f)

def load_pdfs_from_s3(bucket_name):
    """Загрузить все PDF-файлы из S3 бакета."""
    documents = []
    file_keys = list_files_in_s3(bucket_name)
    for file_key in file_keys:
        if file_key.endswith(".pdf"):
            download_path = os.path.join(os.getcwd(), os.path.basename(file_key))
            download_file_from_s3(bucket_name, file_key, download_path)
            loader = PyPDFLoader(download_path)
            documents.extend(loader.load())
            os.remove(download_path)
    return documents

# Функции для работы с эмбеддингами и qdrant
def get_cached_embeddings(texts):
    """Загрузить закэшированные эмбеддинги, если они есть."""
    embeddings_cache = "embeddings_cache.pkl"
    # проверка на тип файла
    if os.path.exists(embeddings_cache) and os.path.isdir(embeddings_cache):
        raise Exception("Embeddings cache is directory! Delete it and restart.")
    
    if os.path.exists(embeddings_cache):
        with open(embeddings_cache, "rb") as f:
            cache = pickle.load(f)
    else:
        cache = {}

    new_texts = [t for t in texts if t.page_content not in cache]
    if new_texts:
        print(f"Создаём эмбеддинги для {len(new_texts)} новых фрагментов...")
        new_embeddings = []
        for i, text in enumerate(new_texts):
            emb = embeddings.embed_documents([text.page_content])[0]
            if i == 0:
                print("Размер эмбеддинга:", len(emb))
            new_embeddings.append(emb)
            if i % 10 == 0:
                time.sleep(1)

        for text, emb in zip(new_texts, new_embeddings):
            cache[text.page_content] = emb

        with open(embeddings_cache, "wb") as f:
            pickle.dump(cache, f)

    return [cache[t.page_content] for t in texts]

def create_collection_if_not_exists():
    """Создать коллекцию, если она не существует."""
    try:
        qdrant_client.get_collection(collection_name)
        print(f"Коллекция '{collection_name}' уже существует.")
    except Exception:
        print(f"Создаём коллекцию '{collection_name}' в Qdrant.")
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config={"size": 256, "distance": "Cosine"}
        )

def load_or_create_qdrant(bucket_name, use_cache=True):
    """Загружает или создаёт индекс в Qdrant, если это необходимо."""
    if use_cache:
        embeddings_cache = "embeddings_cache.pkl"
        if os.path.exists(embeddings_cache):
            with open(embeddings_cache, "rb") as f:
                cache = pickle.load(f)
        else:
            cache = {}

        if cache:
            print("Используем закэшированные эмбеддинги, база данных не вызывается.")
            return list(cache.values()), []

    # Если кеша нет или его недостаточно, создаем новый индекс в Qdrant
    print("Кешированные эмбеддинги отсутствуют или недостаточны. Загружаем данные в базу данных.")
    create_collection_if_not_exists()
    documents = load_pdfs_from_s3(bucket_name)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)
    embeddings_list = get_cached_embeddings(texts)
    points = [
        PointStruct(id=i, vector=embeddings_list[i], payload={"text": texts[i].page_content})
        for i in range(len(texts))
    ]
    qdrant_client.upsert(collection_name=collection_name, points=points)
    return embeddings_list, texts

def extract_key_terms(question):
    """Извлечь ключевые термины из вопроса, убирая стоп-слова."""
    stop_words = STOP_WORDS
    question = question.lower().translate(str.maketrans("", "", string.punctuation))
    terms = [word for word in question.split() if word not in stop_words]
    return terms if terms else question.split()

def clean_text(text):
    """Удаляет спецсимволы и приводит текст к читаемому виду."""
    return text.replace("\n", " ").replace("\\n", " ").replace('"', '').strip()

def contains_key_term(text, key_terms):
    """Проверяет, содержит ли текст хотя бы одно из ключевых слов."""
    text = text.lower()
    return any(term in text for term in key_terms)

# Функция вызова LLM
def LLM_chain(question):
    """Основная функция для обработки запроса и возвращения ответа."""
    load_or_create_qdrant(bucket_name, use_cache=True)

    # Выполняем поиск в базе данных только если эмбеддинги свежие
    query_vector = embeddings.embed_documents([question])[0]
    search_result = qdrant_client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=1000
    ).points

    question_words = set(extract_key_terms(question))
    relevant_results = [r for r in search_result if any(word in r.payload["text"].lower() for word in question_words)]
    
    if relevant_results and any(contains_key_term(r.payload["text"], question_words) for r in relevant_results):
        context = "\n".join([clean_text(result.payload["text"]) for result in relevant_results[:10]])
        
        template = """Ты ассистент по вопросам, связанным с ПИШ и ЛЭТИ. Если в вопросе упоминается "ПИШ" или "ЛЭТИ", отвечай в их контексте. 
        Если в вопросе нет явного указания на ПИШ или ЛЭТИ, подразумевай, что он о ПИШ. 
        Используй предоставленный контекст для ответа. Если контекста недостаточно, дай общий ответ, связанный с ПИШ. Давай развернутый ответ.
        Контекст: {context}
        Вопрос: {question}
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = (
            {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
            | prompt
            | yandex_gpt
            | StrOutputParser()
        )
        
        response = chain.invoke({"context": context, "question": question})
    else:
        response = fallback_response(question)
    
    return response + "\n\nЕсли не нашли ответ на свой вопрос, воспользуйтесь сайтом: https://pish.etu.ru/. Или задайте вопрос менеджеру программы."

def fallback_response(question):
    template = """Ты универсальный GPT ассистент давай развернутые ответы на вопросы.
    Вопрос: {question}
    """
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | yandex_gpt | StrOutputParser()
    return chain.invoke({"question": question})

if __name__ == "__main__":
    # Тестовые вопросы
    questions = ["промышленная электроника", "напиши легкую html страницу"]
    for question in questions:
        print(f"\nВопрос: {question}")
        answer = LLM_chain(question)
        print(f"Ответ: {answer}")
