import json
from urllib.parse import urlencode
from datetime import datetime
from flask import Blueprint, request, Response, stream_with_context
from extensions import db
from models import (
    Project, OutlineNode, TenderFile, ChapterContent, ChapterContentVersion,
    GenerationTask, ChapterStatus, TaskStatus, ProjectStatus
)
from routes.files import extract_text_from_file
from utils.ThinkStreamFilter import ThinkStreamFilter
from utils.response import success, error
from utils.dify_client import stream_generate_chapter
from utils.knowledge_client import build_generation_knowledge_context

bp = Blueprint('generation', __name__)


def _build_chapter_structure(node: OutlineNode) -> str:
    """构建章节结构文本，包含子节点"""
    lines = [f"# {node.title}"]
    children = sorted(node.children, key=lambda x: x.order_no)
    for child in children:
        lines.append(f"## {child.title}")
        if child.prompt_requirement:
            lines.append(f"  要求：{child.prompt_requirement}")
    return '\n'.join(lines)


@bp.route('/<int:project_id>/chapters/<int:node_id>', methods=['GET'])
def get_chapter(project_id, node_id):
    Project.query.get_or_404(project_id)
    OutlineNode.query.get_or_404(node_id)
    content = ChapterContent.query.filter_by(
        project_id=project_id, outline_node_id=node_id
    ).first()
    if not content:
        return success({
            'outlineNodeId': node_id,
            'status': ChapterStatus.NOT_GENERATED,
            'content': None,
            'currentVersionNo': 0,
            'versions': [],
        })
    return success(content.to_dict(include_versions=True))


@bp.route('/<int:project_id>/chapters/<int:node_id>', methods=['PUT'])
def save_chapter(project_id, node_id):
    Project.query.get_or_404(project_id)
    OutlineNode.query.get_or_404(node_id)
    data = request.get_json()
    new_content = data.get('content', '')

    content = ChapterContent.query.filter_by(
        project_id=project_id, outline_node_id=node_id
    ).first()

    if not content:
        content = ChapterContent(
            project_id=project_id,
            outline_node_id=node_id,
            current_version_no=1,
            content=new_content,
            status=ChapterStatus.MANUALLY_EDITED,
            last_edited_at=datetime.utcnow(),
        )
        db.session.add(content)
    else:
        content.current_version_no = (content.current_version_no or 0) + 1
        content.content = new_content
        content.status = ChapterStatus.MANUALLY_EDITED
        content.last_edited_at = datetime.utcnow()

    # 保存版本
    version = ChapterContentVersion(
        chapter_content_id=content.id if content.id else None,
        version_no=content.current_version_no,
        source_type='manual_edit',
        content=new_content,
    )
    db.session.add(content)
    db.session.flush()
    version.chapter_content_id = content.id
    db.session.add(version)
    db.session.commit()
    return success(content.to_dict())


@bp.route('/<int:project_id>/chapters/<int:node_id>/generate', methods=['POST'])
def generate_chapter(project_id, node_id):
    """创建生成任务，返回 taskId 和 streamUrl"""
    Project.query.get_or_404(project_id)
    OutlineNode.query.get_or_404(node_id)
    data = request.get_json(silent=True) or {}
    use_knowledge = data.get('useKnowledge', True)
    knowledge_top_k = data.get('knowledgeTopK')

    # 创建任务记录
    task = GenerationTask(
        project_id=project_id,
        outline_node_id=node_id,
        status=TaskStatus.PENDING,
    )
    db.session.add(task)
    db.session.commit()

    stream_query = urlencode({
        'useKnowledge': str(bool(use_knowledge)).lower(),
        'knowledgeTopK': knowledge_top_k or '',
    })

    return success({
        'taskId': task.id,
        'streamUrl': f'/api/projects/{project_id}/generation-tasks/{task.id}/stream?{stream_query}',
        'useKnowledge': bool(use_knowledge),
        'knowledgeTopK': knowledge_top_k,
    })


@bp.route('/<int:project_id>/generation-tasks/<int:task_id>/stream', methods=['GET'])
def stream_task(project_id, task_id):
    project = Project.query.get_or_404(project_id)
    task = GenerationTask.query.get_or_404(task_id)
    node = OutlineNode.query.get_or_404(task.outline_node_id)
    tf = TenderFile.query.filter_by(project_id=project_id).order_by(TenderFile.id.desc()).first()
    if not tf:
        return error('请先上传招标文件', 400)
    if not tf.storage_path:
        return error('招标文件路径不存在', 400)

    use_knowledge = request.args.get('useKnowledge', 'true').lower() != 'false'
    knowledge_top_k = request.args.get('knowledgeTopK', type=int)

    file_path = tf.storage_path
    parsed_bid = tf.parsed_summary if tf else ''
    chapter_structure = _build_chapter_structure(node)
    prompt_requirement = node.prompt_requirement or ''

    def generate():
        # 发送start事件
        yield f"event: start\ndata: {json.dumps({'taskId': task_id, 'nodeId': node.id}, ensure_ascii=False)}\n\n"

        full_text = []
        has_error = False
        stream_finished = False
        error_message = None
        knowledge_result = {'provider': 'local', 'items': [], 'context': ''}

        try:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            db.session.commit()

            # 更新章节状态
            content = ChapterContent.query.filter_by(
                project_id=project_id, outline_node_id=node.id
            ).first()
            if not content:
                content = ChapterContent(
                    project_id=project_id,
                    outline_node_id=node.id,
                    status=ChapterStatus.GENERATING,
                )
                db.session.add(content)
            else:
                content.status = ChapterStatus.GENERATING
            db.session.commit()

            if use_knowledge:
                knowledge_query = '\n'.join(filter(None, [node.title, chapter_structure, prompt_requirement]))
                try:
                    knowledge_result = build_generation_knowledge_context(project_id, knowledge_query, top_k=knowledge_top_k)
                    yield f"event: retrieval\ndata: {json.dumps({'provider': knowledge_result.get('provider'), 'items': knowledge_result.get('items', [])}, ensure_ascii=False)}\n\n"
                except Exception as retrieval_error:
                    yield f"event: retrieval\ndata: {json.dumps({'provider': 'fallback', 'items': [], 'message': str(retrieval_error)}, ensure_ascii=False)}\n\n"

            final_prompt_requirement = prompt_requirement
            if knowledge_result.get('context'):
                final_prompt_requirement = '\n\n'.join(filter(None, [
                    '请优先参考以下知识库片段进行生成，并在内容中吸收相关要求：',
                    knowledge_result['context'],
                    prompt_requirement,
                ]))

            for line in stream_generate_chapter(
                file_path=file_path,
                parsed_bid=parsed_bid,
                chapter_title=node.title,
                chapter_structure=chapter_structure,
                prompt_requirement=final_prompt_requirement,
            ):
                if line.startswith('data:'):
                    raw = line[5:].strip()
                    try:
                        event_data = json.loads(raw)
                        # Dify streaming event格式
                        event_type = event_data.get('event', '')

                        if event_type == 'workflow_started':
                            yield f"event: start\ndata: {json.dumps({'taskId': task_id}, ensure_ascii=False)}\n\n"

                        elif event_type == 'text_chunk':
                            # 节点文本输出
                            text = event_data.get('data', {}).get('text', '')
                            if text:
                                full_text.append(text)
                                yield f"event: delta\ndata: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"
                        elif event_type == 'node_finished':
                            outputs = event_data.get('data', {}).get('outputs', {})
                            # 如果有 text/content 输出
                            for key in ('text', 'content', 'result', 'output'):
                                val = outputs.get(key, '')
                                if val and key != 'text':  # text_chunk已处理
                                    pass

                        elif event_type == 'workflow_finished':
                            stream_finished = True
                            outputs = event_data.get('data', {}).get('outputs', {})
                            # 工作流最终输出
                            for key in ('content', 'result', 'text', 'output', 'chapter_content'):
                                val = outputs.get(key, '')
                                if val and not full_text:
                                    full_text.append(val)
                                    yield f"event: delta\ndata: {json.dumps({'text': val}, ensure_ascii=False)}\n\n"
                                    break

                        elif event_type == 'error':
                            msg = event_data.get('message', '生成失败')
                            has_error = True
                            error_message = msg
                            yield f"event: error\ndata: {json.dumps({'message': msg}, ensure_ascii=False)}\n\n"

                    except json.JSONDecodeError:
                        pass

        except Exception as e:
            has_error = True
            error_message = str(e)
            print(e)
            if not stream_finished:
                yield f"event: error\ndata: {json.dumps({'message': error_message}, ensure_ascii=False)}\n\n"

        # 保存结果
        try:
            final_text = ''.join(full_text)

            content = ChapterContent.query.filter_by(
                project_id=project_id, outline_node_id=node.id
            ).first()
            if not content:
                content = ChapterContent(
                    project_id=project_id,
                    outline_node_id=node.id,
                )
                db.session.add(content)

            if final_text and not has_error:
                content.current_version_no = (content.current_version_no or 0) + 1
                content.content = final_text
                content.status = ChapterStatus.GENERATED
                content.last_generated_at = datetime.utcnow()
                content.last_edited_at = None

                db.session.add(content)
                db.session.flush()
                version = ChapterContentVersion(
                    chapter_content_id=content.id,
                    version_no=content.current_version_no,
                    source_type='ai_generated',
                    content=final_text,
                )
                db.session.add(version)
            else:
                content.status = ChapterStatus.FAILED

            task.status = TaskStatus.SUCCESS if not has_error else TaskStatus.FAILED
            task.error_message = None if not has_error else error_message
            task.finished_at = datetime.utcnow()
            db.session.commit()

            version_no = content.current_version_no if not has_error else 0
            yield f"event: complete\ndata: {json.dumps({'versionNo': version_no, 'success': not has_error, 'message': error_message}, ensure_ascii=False)}\n\n"

        except Exception as e:
            print(e)
            task.status = TaskStatus.FAILED
            task.error_message = f'保存失败: {str(e)}'
            task.finished_at = datetime.utcnow()
            db.session.commit()
            if not stream_finished:
                yield f"event: error\ndata: {json.dumps({'message': task.error_message}, ensure_ascii=False)}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        }
    )
