import openai 
from langchain.vectorstores.faiss import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain_openai import ChatOpenAI, OpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders.csv_loader import CSVLoader

from app.core.config import settings
import os

class OpenAIModel:
    def __init__(self):
        self.model_name = 'gpt-4o-mini-2024-07-18'
        self.embedding = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY,model='text-embedding-3-small')
        self.thresh = 0.5
        self.chat_bot = ChatOpenAI(model_name=self.model_name, openai_api_key=settings.OPENAI_API_KEY)
        self.client = OpenAI(openai_api_key=settings.OPENAI_API_KEY)

    def build_vector_db(self, chatbot_id: str, data_files: list[dict[str, str]]) -> None:
        documents = []

        for data_file in data_files:
            if data_file['type'] == 'csv':
                loader = CSVLoader(data_file['path'])
                documents.extend(loader.load())
            else:
                with open(data_file['path'], 'r', encoding='utf-8') as file:
                    text = file.read()

                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                texts = text_splitter.split_text(text)
                documents.extend([{"text": txt, "metadata": {"chatbot_id": chatbot_id}} for txt in texts])

        faiss = FAISS.from_texts([doc["text"] for doc in documents], embedding=self.embedding)

        directory = f"data/vector_dbs"
        if not os.path.exists(directory):
            os.makedirs(directory)
        faiss.save_local(f"{directory}/{chatbot_id}_faiss.index")
        return faiss

    def load_vector_db(self, chatbot_id: str):
        directory = f"data/vector_dbs"
        faiss = FAISS.load_local(f"{directory}/{chatbot_id}_faiss.index", 
                                 embeddings=self.embedding,
                                 allow_dangerous_deserialization=True)
        return faiss

    def delete_vector_db(self, chatbot_id: str):
        directory = f"data/vector_dbs"
        os.remove(f"{directory}/{chatbot_id}_faiss.index")

    def ask_by_chatbot_id(self, chatbot_id: str, question: str, chat_history: list[dict] = None) -> dict:
        try:
            faiss = self.load_vector_db(chatbot_id)
            return self.ask_by_faiss(faiss, question, chat_history)
        except Exception as e:
            # Tạo messages từ chat history
            messages = []
            if chat_history:
                messages.extend(chat_history)
            messages.append({"role": "user", "content": question})
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=150
            )
            return {"answer": response.choices[0].message.content}

    def ask_by_faiss(self, faiss: FAISS, question: str, chat_history: list[dict] = None) -> dict:
        question_vector = self.embedding.embed_query(question)
        results = faiss.similarity_search_by_vector(question_vector, k=5)
        
        # Tạo prompt với context và chat history
        messages = []
        if chat_history:
            messages.extend(chat_history)
        
        if results:
            context = results[0].page_content
            messages.append({"role": "system", "content": f"Context: {context}"})
        
        messages.append({"role": "user", "content": question})
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=150
        )
        return {"answer": response.choices[0].message.content}
    
openai_model = OpenAIModel()
