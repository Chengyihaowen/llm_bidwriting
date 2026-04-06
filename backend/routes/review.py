import json
import re
from datetime import datetime
from flask import Blueprint, request
from extensions import db
from models import Project, TenderFile, OutlineNode, ChapterContent, BidCheckResult
from utils.response import success, error
from utils.dify_client import run_check_workflow

bp = Blueprint('review', __name__)


def _parse_check_results(outputs: str, project_id: int) -> list:
    """从Dify输出解析废标检查结果列表"""
    results = []
    outputs=json.loads(outputs)

    raw_results = outputs.get('results', outputs.get('check_results', []))
    raw_summary = outputs.get('summary', {})

    if isinstance(raw_results, str):
        try:
            raw_results = json.loads(raw_results)
        except Exception:
            raw_results = _parse_markdown_results(raw_results)

    if isinstance(raw_summary, str):
        try:
            raw_summary = json.loads(raw_summary)
        except Exception:
            raw_summary = {}

    if isinstance(raw_results, list):
        for item in raw_results:
            results.append({
                'riskLevel': item.get('riskLevel', item.get('risk_level', 'low')),
                'title': item.get('title', ''),
                'description': item.get('description', ''),
                'suggestion': item.get('suggestion', ''),
                'relatedOutlineNodeId': item.get('relatedOutlineNodeId'),
            })

    if not results and outputs.get('check_result'):
        results.append({
            'riskLevel': 'medium',
            'title': '废标检查报告',
            'description': outputs['check_result'],
            'suggestion': '请人工复核',
            'relatedOutlineNodeId': None,
        })

    return results, raw_summary


def _parse_markdown_results(text: str) -> list:
    """从markdown表格中解析检查结果"""
    results = []
    lines = text.split('\n')
    in_table = False
    for line in lines:
        if '|' in line and ('高风险' in line or '中风险' in line or '低风险' in line or 'high' in line.lower()):
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if len(cells) >= 2:
                risk = 'high' if '高' in cells[0] or 'high' in cells[0].lower() else \
                       'medium' if '中' in cells[0] or 'medium' in cells[0].lower() else 'low'
                results.append({
                    'riskLevel': risk,
                    'title': cells[1] if len(cells) > 1 else '',
                    'description': cells[2] if len(cells) > 2 else '',
                    'suggestion': cells[3] if len(cells) > 3 else '',
                    'relatedOutlineNodeId': None,
                })
    return results


@bp.route('/<int:project_id>/bid-check', methods=['POST'])
def run_bid_check(project_id):
    project = Project.query.get_or_404(project_id)

    # 获取招标文件解析摘要
    tf = TenderFile.query.filter_by(project_id=project_id).order_by(TenderFile.id.desc()).first()
    if not tf or not tf.parsed_summary:
        return error('请先完成招标文件解析', 400)

    # 汇总所有章节内容
    contents = ChapterContent.query.filter_by(project_id=project_id).all()
    nodes_map = {n.id: n for n in OutlineNode.query.filter_by(project_id=project_id).all()}
    chapters_text = []
    for c in contents:
        if c.content:
            node = nodes_map.get(c.outline_node_id)
            title = node.title if node else f'章节{c.outline_node_id}'
            chapters_text.append(f"# {title}\n{c.content}")
    chapters_content = '\n\n---\n\n'.join(chapters_text)

    try:
        outputs = run_check_workflow(
            tf.parsed_summary or '',
            tf.risk_clauses or '',
            chapters_content,
        )
        print(outputs)

        # 获取当前最大check_version
        max_ver = db.session.query(db.func.max(BidCheckResult.check_version))\
            .filter_by(project_id=project_id).scalar() or 0
        check_version = max_ver + 1

        # 解析结果
        parsed_results, parsed_summary = _parse_check_results(outputs, project_id)

        # 保存到数据库
        saved = []
        for r in parsed_results:
            record = BidCheckResult(
                project_id=project_id,
                check_version=check_version,
                risk_level=r['riskLevel'],
                title=r['title'],
                description=r['description'],
                suggestion=r['suggestion'],
                related_outline_node_id=r['relatedOutlineNodeId'],
                status='open',
            )
            db.session.add(record)
            saved.append(r)
        db.session.commit()

        high = parsed_summary.get('high') if isinstance(parsed_summary, dict) else None
        medium = parsed_summary.get('medium') if isinstance(parsed_summary, dict) else None
        low = parsed_summary.get('low') if isinstance(parsed_summary, dict) else None

        if high is None:
            high = sum(1 for r in saved if r['riskLevel'] == 'high')
        if medium is None:
            medium = sum(1 for r in saved if r['riskLevel'] == 'medium')
        if low is None:
            low = sum(1 for r in saved if r['riskLevel'] == 'low')

        return success({
            'checkVersion': check_version,
            'summary': {'high': high, 'medium': medium, 'low': low},
            'results': [r.to_dict() for r in BidCheckResult.query.filter_by(
                project_id=project_id, check_version=check_version
            ).all()],
        })

    except Exception as e:
        return error(f'废标检查失败: {str(e)}', 500)


@bp.route('/<int:project_id>/bid-check', methods=['GET'])
def get_bid_check(project_id):
    Project.query.get_or_404(project_id)
    # 返回最新版本的检查结果
    max_ver = db.session.query(db.func.max(BidCheckResult.check_version))\
        .filter_by(project_id=project_id).scalar()
    if not max_ver:
        return success({'checkVersion': 0, 'results': [], 'summary': {'high': 0, 'medium': 0, 'low': 0}})

    results = BidCheckResult.query.filter_by(project_id=project_id, check_version=max_ver).all()
    high = sum(1 for r in results if r.risk_level == 'high')
    medium = sum(1 for r in results if r.risk_level == 'medium')
    low = sum(1 for r in results if r.risk_level == 'low')

    return success({
        'checkVersion': max_ver,
        'summary': {'high': high, 'medium': medium, 'low': low},
        'results': [r.to_dict() for r in results],
    })
