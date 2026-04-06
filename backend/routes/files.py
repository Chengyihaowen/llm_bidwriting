import os
import uuid
import json
from datetime import datetime
from flask import Blueprint, request, current_app
from werkzeug.utils import secure_filename
from extensions import db
from models import Project, TenderFile, OutlineNode, ParseStatus, ProjectStatus
from utils.response import success, error
from utils.file_utils import allowed_file, get_file_extension, extract_text_from_file
from utils.dify_client import run_parse_workflow

bp = Blueprint('files', __name__)


@bp.route('/<int:project_id>/tender-file', methods=['GET'])
def get_tender_file(project_id):
    Project.query.get_or_404(project_id)
    tf = TenderFile.query.filter_by(project_id=project_id).order_by(TenderFile.id.desc()).first()
    if not tf:
        return success(None)
    return success(tf.to_dict())


@bp.route('/<int:project_id>/tender-file', methods=['POST'])
def upload_tender_file(project_id):
    project = Project.query.get_or_404(project_id)

    if 'file' not in request.files:
        return error('未找到上传文件', 400)

    file = request.files['file']
    if not file.filename:
        return error('文件名为空', 400)

    if not allowed_file(file.filename):
        return error('仅支持 PDF、DOCX 格式', 400, 4001)

    ext = get_file_extension(file.filename)
    safe_name = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'tender')
    file_path = os.path.join(upload_dir, safe_name)
    file.save(file_path)

    tf = TenderFile(
        project_id=project_id,
        file_name=file.filename,
        file_type=ext,
        file_size=os.path.getsize(file_path),
        storage_path=file_path,
        parse_status=ParseStatus.PENDING,
    )
    db.session.add(tf)
    db.session.commit()
    return success(tf.to_dict()), 201


@bp.route('/<int:project_id>/tender-file/parse', methods=['POST'])
def parse_tender_file(project_id):
    project = Project.query.get_or_404(project_id)
    tf = TenderFile.query.filter_by(project_id=project_id).order_by(TenderFile.id.desc()).first()
    if not tf:
        return error('请先上传招标文件', 400)
    if tf.parse_status == ParseStatus.PARSING:
        return error('解析正在进行中', 400)

    # 更新状态
    tf.parse_status = ParseStatus.PARSING
    db.session.commit()

    try:
        # 1. 提取文本
        bid_text = extract_text_from_file(tf.storage_path, tf.file_type)
        if not bid_text.strip():
            raise RuntimeError('文件内容为空，无法提取文本')
        tf.parsed_text = bid_text

        # 2. 调用Dify解析工作流
        outputs = run_parse_workflow(bid_text)

        parsed_bid = outputs.get('parsed_bid', '')
        risk_clauses = outputs.get('risk_clauses', '')
        format_template = outputs.get('format_template', '')
        outline_json_str = outputs.get('outline_json', '')

        tf.parsed_summary = parsed_bid
        tf.risk_clauses = risk_clauses
        tf.format_template = format_template
        tf.parse_status = ParseStatus.SUCCESS

        # 3. 解析目录JSON并保存OutlineNode
        outline_data = []
        if outline_json_str:
            try:
                outline_data = json.loads(outline_json_str)
            except Exception:
                # Dify可能返回markdown包裹，尝试提取JSON
                import re
                m = re.search(r'```(?:json)?\s*(\[[\s\S]*?\])\s*```', outline_json_str)
                if m:
                    outline_data = json.loads(m.group(1))

        if outline_data:
            # 清理旧节点
            OutlineNode.query.filter_by(project_id=project_id).delete()
            _save_outline_nodes(project_id, outline_data)

        project.status = ProjectStatus.OUTLINE_CONFIRMED if outline_data else ProjectStatus.DRAFT
        project.updated_at = datetime.utcnow()
        db.session.commit()

        return success({
            'parseStatus': tf.parse_status,
            'hasParsedSummary': bool(parsed_bid),
            'outlineNodeCount': len(outline_data),
        })

    except Exception as e:
        tf.parse_status = ParseStatus.FAILED
        tf.parse_error_message = str(e)
        db.session.commit()
        return error(f'解析失败: {str(e)}', 500, 4002)


def _save_outline_nodes(project_id: int, nodes: list, parent_id=None, level=1):
    """递归保存目录节点"""
    for i, node in enumerate(nodes):
        n = OutlineNode(
            project_id=project_id,
            parent_id=parent_id,
            level=level,
            title=node.get('title', '未命名章节'),
            order_no=i,
            node_type='chapter' if level == 1 else 'section',
            prompt_requirement=node.get('promptRequirement', ''),
        )
        db.session.add(n)
        db.session.flush()  # 获取ID
        children = node.get('children', [])
        if children:
            _save_outline_nodes(project_id, children, parent_id=n.id, level=level + 1)
