import enum
from datetime import datetime
from extensions import db


class ProjectStatus(str, enum.Enum):
    DRAFT = 'draft'
    OUTLINE_CONFIRMED = 'outline_confirmed'
    GENERATING = 'generating'
    PENDING_REVIEW = 'pending_review'
    EXPORTABLE = 'exportable'
    EXPORTED = 'exported'


class ParseStatus(str, enum.Enum):
    PENDING = 'pending'
    PARSING = 'parsing'
    SUCCESS = 'success'
    FAILED = 'failed'


class ChapterStatus(str, enum.Enum):
    NOT_GENERATED = 'not_generated'
    GENERATING = 'generating'
    GENERATED = 'generated'
    MANUALLY_EDITED = 'manually_edited'
    FAILED = 'failed'


class TaskStatus(str, enum.Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    SUCCESS = 'success'
    FAILED = 'failed'


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    bidder_name = db.Column(db.String(200))
    tender_title = db.Column(db.String(500))
    tender_no = db.Column(db.String(100))
    status = db.Column(db.String(50), default=ProjectStatus.DRAFT)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tender_files = db.relationship('TenderFile', backref='project', lazy=True, cascade='all, delete-orphan')
    outline_nodes = db.relationship('OutlineNode', backref='project', lazy=True, cascade='all, delete-orphan')
    chapter_contents = db.relationship('ChapterContent', backref='project', lazy=True, cascade='all, delete-orphan')
    bid_check_results = db.relationship('BidCheckResult', backref='project', lazy=True, cascade='all, delete-orphan')
    export_tasks = db.relationship('ExportTask', backref='project', lazy=True, cascade='all, delete-orphan')
    knowledge_files = db.relationship('KnowledgeFile', backref='project', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'bidderName': self.bidder_name,
            'tenderTitle': self.tender_title,
            'tenderNo': self.tender_no,
            'status': self.status,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
        }


class TenderFile(db.Model):
    __tablename__ = 'tender_files'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    file_name = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50))
    file_size = db.Column(db.Integer)
    storage_path = db.Column(db.String(1000))
    parsed_text = db.Column(db.Text)          # 解析出的纯文本
    parsed_summary = db.Column(db.Text)       # Dify Node2 的 parsed_bid 摘要
    risk_clauses = db.Column(db.Text)         # Dify 风险条款摘要
    format_template = db.Column(db.Text)      # Dify 模板摘要
    parse_status = db.Column(db.String(50), default=ParseStatus.PENDING)
    parse_error_message = db.Column(db.Text)
    dify_file_id = db.Column(db.String(200))  # 上传到Dify的文件ID
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'projectId': self.project_id,
            'fileName': self.file_name,
            'fileType': self.file_type,
            'fileSize': self.file_size,
            'parseStatus': self.parse_status,
            'parseErrorMessage': self.parse_error_message,
            'uploadedAt': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'hasParsedText': bool(self.parsed_text),
            'hasSummary': bool(self.parsed_summary),
            'hasRiskClauses': bool(self.risk_clauses),
            'hasFormatTemplate': bool(self.format_template),
        }


class OutlineNode(db.Model):
    __tablename__ = 'outline_nodes'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('outline_nodes.id'), nullable=True)
    level = db.Column(db.Integer, nullable=False, default=1)
    title = db.Column(db.String(500), nullable=False)
    order_no = db.Column(db.Integer, default=0)
    node_type = db.Column(db.String(50), default='chapter')  # chapter / section
    prompt_requirement = db.Column(db.Text)
    is_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    children = db.relationship('OutlineNode', backref=db.backref('parent', remote_side=[id]), lazy=True)
    chapter_content = db.relationship('ChapterContent', backref='outline_node', uselist=False, cascade='all, delete-orphan')

    def to_dict(self, include_children=False):
        d = {
            'id': self.id,
            'projectId': self.project_id,
            'parentId': self.parent_id,
            'level': self.level,
            'title': self.title,
            'orderNo': self.order_no,
            'nodeType': self.node_type,
            'promptRequirement': self.prompt_requirement,
            'isEnabled': self.is_enabled,
        }
        if include_children:
            d['children'] = [c.to_dict(include_children=True) for c in sorted(self.children, key=lambda x: x.order_no)]
        return d


class ChapterContent(db.Model):
    __tablename__ = 'chapter_contents'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    outline_node_id = db.Column(db.Integer, db.ForeignKey('outline_nodes.id'), nullable=False)
    current_version_no = db.Column(db.Integer, default=0)
    content = db.Column(db.Text)
    content_format = db.Column(db.String(50), default='markdown')
    status = db.Column(db.String(50), default=ChapterStatus.NOT_GENERATED)
    last_generated_at = db.Column(db.DateTime)
    last_edited_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    versions = db.relationship('ChapterContentVersion', backref='chapter_content', lazy=True, cascade='all, delete-orphan', order_by='ChapterContentVersion.version_no.desc()')

    def to_dict(self, include_versions=False):
        d = {
            'id': self.id,
            'projectId': self.project_id,
            'outlineNodeId': self.outline_node_id,
            'currentVersionNo': self.current_version_no,
            'content': self.content,
            'contentFormat': self.content_format,
            'status': self.status,
            'lastGeneratedAt': self.last_generated_at.isoformat() if self.last_generated_at else None,
            'lastEditedAt': self.last_edited_at.isoformat() if self.last_edited_at else None,
        }
        if include_versions:
            d['versions'] = [v.to_dict() for v in self.versions[:10]]
        return d


class ChapterContentVersion(db.Model):
    __tablename__ = 'chapter_content_versions'

    id = db.Column(db.Integer, primary_key=True)
    chapter_content_id = db.Column(db.Integer, db.ForeignKey('chapter_contents.id'), nullable=False)
    version_no = db.Column(db.Integer, nullable=False)
    source_type = db.Column(db.String(50))  # ai_generated / manual_edit / regenerated
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'versionNo': self.version_no,
            'sourceType': self.source_type,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
        }


class GenerationTask(db.Model):
    __tablename__ = 'generation_tasks'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    outline_node_id = db.Column(db.Integer, db.ForeignKey('outline_nodes.id'), nullable=False)
    task_type = db.Column(db.String(50), default='chapter_generate')
    status = db.Column(db.String(50), default=TaskStatus.PENDING)
    dify_task_id = db.Column(db.String(200))
    error_message = db.Column(db.Text)
    started_at = db.Column(db.DateTime)
    finished_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'projectId': self.project_id,
            'outlineNodeId': self.outline_node_id,
            'status': self.status,
            'errorMessage': self.error_message,
            'startedAt': self.started_at.isoformat() if self.started_at else None,
            'finishedAt': self.finished_at.isoformat() if self.finished_at else None,
        }


class BidCheckResult(db.Model):
    __tablename__ = 'bid_check_results'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    check_version = db.Column(db.Integer, default=1)
    risk_level = db.Column(db.String(20))  # high / medium / low
    rule_type = db.Column(db.String(50))
    title = db.Column(db.String(500))
    description = db.Column(db.Text)
    suggestion = db.Column(db.Text)
    related_outline_node_id = db.Column(db.Integer)
    status = db.Column(db.String(50), default='open')  # open / resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'projectId': self.project_id,
            'checkVersion': self.check_version,
            'riskLevel': self.risk_level,
            'ruleType': self.rule_type,
            'title': self.title,
            'description': self.description,
            'suggestion': self.suggestion,
            'relatedOutlineNodeId': self.related_outline_node_id,
            'status': self.status,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
        }


class KnowledgeFile(db.Model):
    __tablename__ = 'knowledge_files'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    file_name = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50))
    file_size = db.Column(db.Integer)
    storage_path = db.Column(db.String(1000))
    content_text = db.Column(db.Text)
    parse_status = db.Column(db.String(50), default=ParseStatus.PENDING)
    parse_error_message = db.Column(db.Text)
    provider = db.Column(db.String(50), default='local')
    provider_doc_id = db.Column(db.String(200))
    chunk_count = db.Column(db.Integer, default=0)
    is_enabled = db.Column(db.Boolean, default=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    chunks = db.relationship('KnowledgeChunk', backref='knowledge_file', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'projectId': self.project_id,
            'fileName': self.file_name,
            'fileType': self.file_type,
            'fileSize': self.file_size,
            'parseStatus': self.parse_status,
            'parseErrorMessage': self.parse_error_message,
            'provider': self.provider,
            'providerDocId': self.provider_doc_id,
            'chunkCount': self.chunk_count or 0,
            'isEnabled': self.is_enabled,
            'uploadedAt': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
            'hasContentText': bool(self.content_text),
        }


class KnowledgeChunk(db.Model):
    __tablename__ = 'knowledge_chunks'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False, index=True)
    knowledge_file_id = db.Column(db.Integer, db.ForeignKey('knowledge_files.id'), nullable=False, index=True)
    chunk_no = db.Column(db.Integer, nullable=False)
    chunk_text = db.Column(db.Text, nullable=False)
    chunk_len = db.Column(db.Integer)
    provider_chunk_id = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'projectId': self.project_id,
            'knowledgeFileId': self.knowledge_file_id,
            'chunkNo': self.chunk_no,
            'chunkText': self.chunk_text,
            'chunkLen': self.chunk_len,
            'providerChunkId': self.provider_chunk_id,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
        }


class ExportTask(db.Model):
    __tablename__ = 'export_tasks'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    template_name = db.Column(db.String(100), default='standard-bid-v1')
    status = db.Column(db.String(50), default=TaskStatus.PENDING)
    file_path = db.Column(db.String(1000))
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'projectId': self.project_id,
            'templateName': self.template_name,
            'status': self.status,
            'filePath': self.file_path,
            'errorMessage': self.error_message,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'finishedAt': self.finished_at.isoformat() if self.finished_at else None,
        }

