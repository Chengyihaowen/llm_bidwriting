import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///bid_system.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', './uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 52428800))  # 50MB
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}

    # Knowledge Base
    KNOWLEDGE_PROVIDER = os.environ.get('KNOWLEDGE_PROVIDER', 'local')
    KNOWLEDGE_TOP_K = int(os.environ.get('KNOWLEDGE_TOP_K', 5))
    KNOWLEDGE_CHUNK_SIZE = int(os.environ.get('KNOWLEDGE_CHUNK_SIZE', 800))
    KNOWLEDGE_CHUNK_OVERLAP = int(os.environ.get('KNOWLEDGE_CHUNK_OVERLAP', 120))

    # Aliyun knowledge integration placeholders
    ALIYUN_KNOWLEDGE_API_KEY = os.environ.get('ALIYUN_KNOWLEDGE_API_KEY', '')
    ALIYUN_KNOWLEDGE_WORKSPACE_ID = os.environ.get('ALIYUN_KNOWLEDGE_WORKSPACE_ID', '')
    ALIYUN_KNOWLEDGE_INDEX_ID = os.environ.get('ALIYUN_KNOWLEDGE_INDEX_ID', '')

    # Dify
    DIFY_BASE_URL = os.environ.get('DIFY_BASE_URL', 'http://localhost/v1')
    DIFY_API_KEY_PARSE = os.environ.get('DIFY_API_KEY_PARSE', '')
    DIFY_API_KEY_GENERATE = os.environ.get('DIFY_API_KEY_GENERATE', '')
    DIFY_API_KEY_CHECK = os.environ.get('DIFY_API_KEY_CHECK', '')
    DIFY_TIMEOUT = 300
