from flask import Flask
from flask_cors import CORS
from config import Config
from extensions import db
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'tender'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'knowledge'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'exports'), exist_ok=True)

    from routes.projects import bp as projects_bp
    from routes.files import bp as files_bp
    from routes.outline import bp as outline_bp
    from routes.generation import bp as generation_bp
    from routes.review import bp as review_bp
    from routes.export import bp as export_bp
    from routes.knowledge import bp as knowledge_bp

    app.register_blueprint(projects_bp, url_prefix='/api/projects')
    app.register_blueprint(files_bp, url_prefix='/api/projects')
    app.register_blueprint(outline_bp, url_prefix='/api/projects')
    app.register_blueprint(generation_bp, url_prefix='/api/projects')
    app.register_blueprint(review_bp, url_prefix='/api/projects')
    app.register_blueprint(export_bp, url_prefix='/api/projects')
    app.register_blueprint(knowledge_bp, url_prefix='/api/projects')

    with app.app_context():
        db.create_all()
        inspector = db.inspect(db.engine)

        tender_file_columns = {col['name'] for col in inspector.get_columns('tender_files')} if inspector.has_table('tender_files') else set()
        if 'risk_clauses' not in tender_file_columns:
            db.session.execute(db.text("ALTER TABLE tender_files ADD COLUMN risk_clauses TEXT"))
        if 'format_template' not in tender_file_columns:
            db.session.execute(db.text("ALTER TABLE tender_files ADD COLUMN format_template TEXT"))

        knowledge_file_columns = {col['name'] for col in inspector.get_columns('knowledge_files')} if inspector.has_table('knowledge_files') else set()
        if inspector.has_table('knowledge_files'):
            if 'provider' not in knowledge_file_columns:
                db.session.execute(db.text("ALTER TABLE knowledge_files ADD COLUMN provider VARCHAR(50) DEFAULT 'local'"))
            if 'provider_doc_id' not in knowledge_file_columns:
                db.session.execute(db.text("ALTER TABLE knowledge_files ADD COLUMN provider_doc_id VARCHAR(200)"))
            if 'chunk_count' not in knowledge_file_columns:
                db.session.execute(db.text("ALTER TABLE knowledge_files ADD COLUMN chunk_count INTEGER DEFAULT 0"))
            if 'is_enabled' not in knowledge_file_columns:
                db.session.execute(db.text("ALTER TABLE knowledge_files ADD COLUMN is_enabled BOOLEAN DEFAULT 1"))
            if 'updated_at' not in knowledge_file_columns:
                db.session.execute(db.text("ALTER TABLE knowledge_files ADD COLUMN updated_at DATETIME"))
            if 'content_text' not in knowledge_file_columns:
                db.session.execute(db.text("ALTER TABLE knowledge_files ADD COLUMN content_text TEXT"))
            if 'parse_error_message' not in knowledge_file_columns:
                db.session.execute(db.text("ALTER TABLE knowledge_files ADD COLUMN parse_error_message TEXT"))

        db.session.commit()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
