"""
Inicialização principal do sistema CR-NOVACAP — Controle de Processos e Atendimentos.
Configurações globais, registro de extensões e blueprints institucionais.
"""

import os
from datetime import timedelta, datetime
from dotenv import load_dotenv
from flask import Flask, redirect, url_for

# ==========================================================
# 🔒 Carrega variáveis de ambiente (.env)
# ==========================================================
load_dotenv()

# ==========================================================
# ⚙ Extensões principais
# ==========================================================
from app.ext import db, migrate, login_manager, csrf
from app.models.modelos import Usuario

# ==========================================================
# 📦 Importação dos Blueprints (módulos principais)
# ==========================================================
from app.main import main_bp
from app.processos import processos_bp
from app.relatorios import relatorios_bp
from app.admin import admin_bp


# ==========================================================
# 🏗 Factory principal do sistema CR-NOVACAP
# ==========================================================
def create_app():
    """Cria e configura a aplicação Flask principal."""
    app = Flask(__name__)

    # ------------------------------------------------------
    # 🔧 Configurações básicas do sistema
    # ------------------------------------------------------
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY', 'chave-secreta-padrao'),
        SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'sqlite:///cr.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        PERMANENT_SESSION_LIFETIME=timedelta(hours=1),
    )

    # ------------------------------------------------------
    # 🚀 Inicialização das extensões
    # ------------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # ------------------------------------------------------
    # 🔐 Configuração de autenticação (Flask-Login)
    # ------------------------------------------------------
    login_manager.login_view = 'main_bp.login'
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        """Carrega o usuário autenticado na sessão."""
        return Usuario.query.get(int(user_id))

    # ------------------------------------------------------
    # 📦 Registro de Blueprints institucionais e API REST
    # ------------------------------------------------------
    from app.api import api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(processos_bp, url_prefix='/processos')
    app.register_blueprint(relatorios_bp, url_prefix='/relatorios')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')

    # Exentar apenas a API REST de verificação CSRF (usa autenticação baseada em token/JSON)
    csrf.exempt(api_bp)

    # ------------------------------------------------------
    # 🏠 Rota padrão (redireciona para login)
    # ------------------------------------------------------
    @app.route('/')
    def home_redirect():
        return redirect(url_for('main_bp.login'))

    # ------------------------------------------------------
    # 🎨 Contexto global (Whitelabel & Ano Atual no rodapé)
    # ------------------------------------------------------
    @app.context_processor
    def inject_global_context():
        """Adiciona o ano atual e configurações de Whitelabel/Tenant ao contexto global."""
        from flask_login import current_user
        current_tenant = current_user.tenant if current_user and hasattr(current_user, 'tenant') and current_user.is_authenticated else None
        
        return {
            'current_year': datetime.now().year,
            'app_title': current_tenant.nome_empresa if current_tenant else "Sistema de Gestão de Processos e Chamados",
            'brand_color': current_tenant.cor_primaria if current_tenant else "#0d6efd",
            'brand_logo': current_tenant.logo_url if current_tenant else None,
            'current_tenant': current_tenant
        }

    return app
