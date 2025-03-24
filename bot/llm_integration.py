import os
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
from text_information import STOP_WORDS

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
    
    points = [
        PointStruct(id=i, vector=embeddings.embed_documents([text.page_content])[0], payload={"text": text.page_content})
        for i, text in enumerate(texts)
    ]
    
    qdrant_client.upsert(collection_name=collection_name, points=points)

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

def LLM_chain(question):
    """Основная функция для обработки запроса и возвращения ответа."""
    load_or_create_qdrant(bucket_name)
    
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
