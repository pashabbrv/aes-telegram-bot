import time
from langchain_community.llms import YandexGPT
from langchain_community.embeddings.yandex import YandexGPTEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv
import os

load_dotenv()
iam_token = os.getenv("IAM_TOKEN")
folder_id = os.getenv("FOLDER_ID")

yandex_gpt = YandexGPT(iam_token=iam_token, folder_id=folder_id)
embeddings = YandexGPTEmbeddings(iam_token=iam_token, folder_id=folder_id)
loader = PyPDFLoader("docs/Правила приема/Правила приема.pdf") 
documents = loader.load()[1:20]

# Разделение текста на чанки
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
texts = text_splitter.split_documents(documents)

# Создание эмбеддингов
embeddings_list = []
for text in texts:
    embedding = embeddings.embed_documents([text.page_content])
    embeddings_list.extend(embedding)
    time.sleep(0.1)

# Создание векторного хранилища
text_embedding_pairs = list(zip([t.page_content for t in texts], embeddings_list))
vectorstore = FAISS.from_embeddings(text_embedding_pairs, embeddings)
retriever = vectorstore.as_retriever()

# Создание цепочки RAG
template = """Используй следующие фрагменты текста, чтобы ответить на вопрос. Если ответа нет, скажи "Извините, но мы не нашли ответ на ваш вопрос :(".

Контекст: {context}

Вопрос: {question}
"""
prompt = ChatPromptTemplate.from_template(template)

chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | yandex_gpt
    | StrOutputParser()
)

question = "Расскажи в общих чертах насыщенно какие правила приема в ЛЭТИ"
response = chain.invoke(question)
print(response)