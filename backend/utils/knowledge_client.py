import math
import re
from collections import Counter
from typing import Optional

from flask import current_app

from extensions import db
from models import KnowledgeChunk, KnowledgeFile, ParseStatus
from utils.file_utils import extract_text_from_file


class BaseKnowledgeClient:
    provider_name = 'base'

    def ingest_file(self, project_id: int, knowledge_file: KnowledgeFile) -> dict:
        raise NotImplementedError

    def delete_file(self, project_id: int, knowledge_file: KnowledgeFile) -> bool:
        raise NotImplementedError

    def search(self, project_id: int, query: str, top_k: Optional[int] = None) -> dict:
        raise NotImplementedError


class LocalKnowledgeClient(BaseKnowledgeClient):
    provider_name = 'local'

    def ingest_file(self, project_id: int, knowledge_file: KnowledgeFile) -> dict:
        text = extract_text_from_file(knowledge_file.storage_path, knowledge_file.file_type)
        if not text or not text.strip():
            raise RuntimeError('文件内容为空，无法提取文本')

        chunks = _split_text(
            text,
            chunk_size=current_app.config['KNOWLEDGE_CHUNK_SIZE'],
            overlap=current_app.config['KNOWLEDGE_CHUNK_OVERLAP'],
        )
        if not chunks:
            raise RuntimeError('文件解析后没有可用内容')

        KnowledgeChunk.query.filter_by(knowledge_file_id=knowledge_file.id).delete()
        for idx, chunk in enumerate(chunks, start=1):
            db.session.add(KnowledgeChunk(
                project_id=project_id,
                knowledge_file_id=knowledge_file.id,
                chunk_no=idx,
                chunk_text=chunk,
                chunk_len=len(chunk),
            ))

        knowledge_file.content_text = text
        knowledge_file.parse_status = ParseStatus.SUCCESS
        knowledge_file.parse_error_message = None
        knowledge_file.provider = self.provider_name
        knowledge_file.provider_doc_id = None
        knowledge_file.chunk_count = len(chunks)
        db.session.add(knowledge_file)
        db.session.flush()
        return {
            'provider': self.provider_name,
            'providerDocId': knowledge_file.provider_doc_id,
            'chunkCount': len(chunks),
        }

    def delete_file(self, project_id: int, knowledge_file: KnowledgeFile) -> bool:
        return True

    def search(self, project_id: int, query: str, top_k: Optional[int] = None) -> dict:
        limit = top_k or current_app.config['KNOWLEDGE_TOP_K']
        query_terms = _tokenize(query)
        if not query_terms:
            return {'provider': self.provider_name, 'items': []}

        rows = db.session.query(KnowledgeChunk, KnowledgeFile).join(
            KnowledgeFile, KnowledgeChunk.knowledge_file_id == KnowledgeFile.id
        ).filter(
            KnowledgeChunk.project_id == project_id,
            KnowledgeFile.is_enabled.is_(True),
            KnowledgeFile.parse_status == ParseStatus.SUCCESS,
        ).all()

        scored = []
        for chunk, file in rows:
            score = _score_text(query_terms, chunk.chunk_text)
            if score <= 0:
                continue
            scored.append({
                'content': chunk.chunk_text,
                'score': round(score, 4),
                'source': {
                    'fileId': file.id,
                    'fileName': file.file_name,
                    'chunkNo': chunk.chunk_no,
                },
            })

        scored.sort(key=lambda item: item['score'], reverse=True)
        return {
            'provider': self.provider_name,
            'items': scored[:limit],
        }


class AliyunKnowledgeClient(BaseKnowledgeClient):
    provider_name = 'aliyun'

    def ingest_file(self, project_id: int, knowledge_file: KnowledgeFile) -> dict:
        raise RuntimeError('阿里云知识库接入参数尚未配置，当前请先使用本地知识库模式')

    def delete_file(self, project_id: int, knowledge_file: KnowledgeFile) -> bool:
        return True

    def search(self, project_id: int, query: str, top_k: Optional[int] = None) -> dict:
        raise RuntimeError('阿里云知识库接入参数尚未配置，当前请先使用本地知识库模式')


class FallbackKnowledgeClient(LocalKnowledgeClient):
    provider_name = 'local'


def get_knowledge_client() -> BaseKnowledgeClient:
    provider = (current_app.config.get('KNOWLEDGE_PROVIDER') or 'local').lower()
    if provider == 'aliyun':
        api_key = current_app.config.get('ALIYUN_KNOWLEDGE_API_KEY')
        workspace_id = current_app.config.get('ALIYUN_KNOWLEDGE_WORKSPACE_ID')
        index_id = current_app.config.get('ALIYUN_KNOWLEDGE_INDEX_ID')
        if api_key and workspace_id and index_id:
            return AliyunKnowledgeClient()
        return FallbackKnowledgeClient()
    return LocalKnowledgeClient()


def build_generation_knowledge_context(project_id: int, query: str, top_k: Optional[int] = None) -> dict:
    result = get_knowledge_client().search(project_id, query, top_k=top_k)
    items = result.get('items', [])
    if not items:
        return {
            'provider': result.get('provider', 'local'),
            'items': [],
            'context': '',
        }

    lines = ['以下内容来自当前项目知识库，仅在相关时引用并保持事实一致：']
    for idx, item in enumerate(items, start=1):
        source = item.get('source', {})
        lines.append(
            f"[KB{idx}] 文件：{source.get('fileName', '未知文件')} | 片段：#{source.get('chunkNo', '-')}\n{item.get('content', '')}"
        )
    return {
        'provider': result.get('provider', 'local'),
        'items': items,
        'context': '\n\n'.join(lines),
    }


def _split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    normalized = re.sub(r'\r\n?', '\n', text or '').strip()
    if not normalized:
        return []

    paragraphs = [part.strip() for part in normalized.split('\n\n') if part.strip()]
    chunks = []
    current = ''
    for paragraph in paragraphs:
        candidate = f'{current}\n\n{paragraph}'.strip() if current else paragraph
        if len(candidate) <= chunk_size:
            current = candidate
            continue
        if current:
            chunks.append(current)
        if len(paragraph) <= chunk_size:
            current = paragraph
            continue
        start = 0
        step = max(chunk_size - overlap, 1)
        while start < len(paragraph):
            piece = paragraph[start:start + chunk_size].strip()
            if piece:
                chunks.append(piece)
            start += step
        current = ''
    if current:
        chunks.append(current)
    return chunks


def _tokenize(text: str) -> list[str]:
    text = (text or '').lower()
    tokens = []
    for part in re.findall(r'[\u4e00-\u9fff]+|[a-z0-9]+', text):
        if re.fullmatch(r'[\u4e00-\u9fff]+', part):
            if len(part) <= 2:
                tokens.append(part)
            else:
                tokens.extend(part[i:i + 2] for i in range(len(part) - 1))
                tokens.append(part)
        else:
            tokens.append(part)
    return [token for token in tokens if token.strip()]


def _score_text(query_terms: list[str], text: str) -> float:
    doc_terms = _tokenize(text)
    if not doc_terms:
        return 0.0

    counter = Counter(doc_terms)
    score = 0.0
    for term in query_terms:
        tf = counter.get(term, 0)
        if tf <= 0:
            continue
        score += 1 + math.log(tf + 1)
    if score <= 0:
        return 0.0
    return score / math.sqrt(len(doc_terms))
