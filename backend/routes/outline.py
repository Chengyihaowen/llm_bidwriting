from datetime import datetime
from flask import Blueprint, request
from extensions import db
from models import Project, OutlineNode, ProjectStatus
from utils.response import success, error

bp = Blueprint('outline', __name__)


@bp.route('/<int:project_id>/outline', methods=['GET'])
def get_outline(project_id):
    Project.query.get_or_404(project_id)
    # 获取一级节点，递归包含子节点
    roots = OutlineNode.query.filter_by(
        project_id=project_id, parent_id=None
    ).order_by(OutlineNode.order_no).all()
    return success({
        'projectId': project_id,
        'nodes': [n.to_dict(include_children=True) for n in roots],
    })


@bp.route('/<int:project_id>/outline', methods=['PUT'])
def save_outline(project_id):
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    nodes = data.get('nodes', [])

    if not nodes:
        return error('目录节点不能为空', 400, 4003)

    # 清空旧节点并重建
    OutlineNode.query.filter_by(project_id=project_id).delete()
    db.session.flush()

    _insert_nodes(project_id, nodes, parent_id=None, level=1)

    project.status = ProjectStatus.OUTLINE_CONFIRMED
    project.updated_at = datetime.utcnow()
    db.session.commit()
    return success({'message': '保存成功'})


def _insert_nodes(project_id, nodes, parent_id, level):
    for i, n in enumerate(nodes):
        node = OutlineNode(
            project_id=project_id,
            parent_id=parent_id,
            level=level,
            title=n.get('title', ''),
            order_no=i,
            node_type=n.get('nodeType', 'chapter' if level == 1 else 'section'),
            prompt_requirement=n.get('promptRequirement', ''),
            is_enabled=n.get('isEnabled', True),
        )
        db.session.add(node)
        db.session.flush()
        children = n.get('children', [])
        if children:
            _insert_nodes(project_id, children, parent_id=node.id, level=level + 1)
