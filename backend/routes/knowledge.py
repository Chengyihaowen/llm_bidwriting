import os
import uuid
from flask import Blueprint, current_app, request
from models import Project, KnowledgeFile, KnowledgeChunk, ParseStatus
from extensions import db
from utils.response import success, error
from utils.file_utils import allowed_file, get_file_extension
from utils.knowledge_client import get_knowledge_client

bp = Blueprint('knowledge', __name__)


@bp.route('/<int:project_id>/knowledge-files', methods=['GET'])
def list_knowledge_files(project_id):
    Project.query.get_or_404(project_id)
    files = KnowledgeFile.query.filter_by(project_id=project_id).order_by(KnowledgeFile.uploaded_at.desc()).all()
    return success([item.to_dict() for item in files])


@bp.route('/<int:project_id>/knowledge-files', methods=['POST'])
def upload_knowledge_file(project_id):
    Project.query.get_or_404(project_id)

    if 'file' not in request.files:
        return error('未找到上传文件', 400)

    file = request.files['file']
    if not file.filename:
        return error('文件名为空', 400)

    if not allowed_file(file.filename):
        return error('仅支持 PDF、DOCX、DOC 格式', 400, 4101)

    ext = get_file_extension(file.filename)
    safe_name = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'knowledge')
    file_path = os.path.join(upload_dir, safe_name)
    file.save(file_path)

    knowledge_file = KnowledgeFile(
        project_id=project_id,
        file_name=file.filename,
        file_type=ext,
        file_size=os.path.getsize(file_path),
        storage_path=file_path,
        parse_status=ParseStatus.PENDING,
        provider=(current_app.config.get('KNOWLEDGE_PROVIDER') or 'local').lower(),
    )
    db.session.add(knowledge_file)
    db.session.commit()
    return success(knowledge_file.to_dict()), 201


@bp.route('/<int:project_id>/knowledge-files/<int:file_id>/parse', methods=['POST'])
def parse_knowledge_file(project_id, file_id):
    Project.query.get_or_404(project_id)
    knowledge_file = KnowledgeFile.query.filter_by(project_id=project_id, id=file_id).first_or_404()

    if knowledge_file.parse_status == ParseStatus.PARSING:
        return error('知识库文件解析进行中', 400)
    if not knowledge_file.storage_path or not os.path.exists(knowledge_file.storage_path):
        return error('知识库文件不存在', 400)

    knowledge_file.parse_status = ParseStatus.PARSING
    knowledge_file.parse_error_message = None
    db.session.commit()

    try:
        result = get_knowledge_client().ingest_file(project_id, knowledge_file)
        db.session.commit()
        return success({
            'file': knowledge_file.to_dict(),
            'provider': result.get('provider'),
            'chunkCount': result.get('chunkCount', 0),
        })
    except Exception as e:
        knowledge_file.parse_status = ParseStatus.FAILED
        knowledge_file.parse_error_message = str(e)
        knowledge_file.chunk_count = 0
        db.session.commit()
        return error(f'知识库解析失败: {str(e)}', 500, 4102)


@bp.route('/<int:project_id>/knowledge-files/<int:file_id>', methods=['PUT'])
def update_knowledge_file(project_id, file_id):
    Project.query.get_or_404(project_id)
    knowledge_file = KnowledgeFile.query.filter_by(project_id=project_id, id=file_id).first_or_404()
    data = request.get_json() or {}

    if 'isEnabled' in data:
        knowledge_file.is_enabled = bool(data.get('isEnabled'))

    db.session.commit()
    return success(knowledge_file.to_dict())


@bp.route('/<int:project_id>/knowledge-files/<int:file_id>', methods=['DELETE'])
def delete_knowledge_file(project_id, file_id):
    Project.query.get_or_404(project_id)
    knowledge_file = KnowledgeFile.query.filter_by(project_id=project_id, id=file_id).first_or_404()

    try:
        get_knowledge_client().delete_file(project_id, knowledge_file)
    except Exception:
        pass

    storage_path = knowledge_file.storage_path
    db.session.delete(knowledge_file)
    db.session.commit()

    if storage_path and os.path.exists(storage_path):
        try:
            os.remove(storage_path)
        except OSError:
            pass

    return success(True)


@bp.route('/<int:project_id>/knowledge/search', methods=['POST'])
def search_knowledge(project_id):
    Project.query.get_or_404(project_id)
    data = request.get_json() or {}
    query = (data.get('query') or '').strip()
    top_k = data.get('topK')

    if not query:
        return error('请输入检索内容', 400)

    try:
        result = get_knowledge_client().search(project_id, query, top_k=top_k)
        return success(result)
    except Exception as e:
        return error(f'知识库检索失败: {str(e)}', 500, 4103)
