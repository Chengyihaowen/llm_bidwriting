from flask import Blueprint, request
from extensions import db
from models import Project, ProjectStatus
from utils.response import success, error
from datetime import datetime

bp = Blueprint('projects', __name__)


@bp.route('', methods=['GET'])
def list_projects():
    projects = Project.query.order_by(Project.updated_at.desc()).all()
    return success([p.to_dict() for p in projects])


@bp.route('', methods=['POST'])
def create_project():
    data = request.get_json()
    if not data or not data.get('name'):
        return error('项目名称不能为空', 400)

    project = Project(
        name=data['name'],
        bidder_name=data.get('bidderName'),
        tender_title=data.get('tenderTitle'),
        tender_no=data.get('tenderNo'),
    )
    db.session.add(project)
    db.session.commit()
    return success(project.to_dict()), 201


@bp.route('/<int:project_id>', methods=['GET'])
def get_project(project_id):
    project = Project.query.get_or_404(project_id)
    return success(project.to_dict())


@bp.route('/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    if 'name' in data:
        project.name = data['name']
    if 'bidderName' in data:
        project.bidder_name = data['bidderName']
    if 'tenderTitle' in data:
        project.tender_title = data['tenderTitle']
    if 'tenderNo' in data:
        project.tender_no = data['tenderNo']
    project.updated_at = datetime.utcnow()
    db.session.commit()
    return success(project.to_dict())


@bp.route('/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return success(None, '删除成功')
