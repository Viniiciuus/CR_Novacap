"""
Rotas principais do sistema CR-NOVACAP.
Inclui: tela inicial, login, cadastro, redefinição de senha, logout e busca global.
"""
from flask import (
    render_template, request, redirect, url_for, flash, session, jsonify
)
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text, or_

from app.ext import db
from app.models.modelos import Usuario, Processo
from app.main import main_bp


# ==========================================================
# 1️⃣ Tela inicial
# ==========================================================
@main_bp.route('/')
def index():
    """Página inicial pública"""
    return render_template('index.html')


# ==========================================================
# 2️⃣ Login de usuários
# ==========================================================
@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Realiza login e direciona diretamente para o dashboard de tramitação de processos.
    Inclui verificações de credenciais, status de aprovação e bloqueio.
    """
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        senha = request.form.get('password')

        # 🔎 Busca case-insensitive
        usuario = Usuario.query.filter(
            db.func.lower(Usuario.usuario) == username.lower()
        ).first()

        # ⚠️ Validações básicas
        if not usuario:
            flash("Usuário não encontrado.", "error")
            return redirect(url_for('main_bp.login'))

        if not check_password_hash(usuario.senha_hash, senha):
            flash("Senha incorreta.", "error")
            return redirect(url_for('main_bp.login'))

        if not usuario.aprovado:
            flash("Acesso pendente de aprovação pelo administrador.", "warning")
            return redirect(url_for('main_bp.login'))

        if usuario.bloqueado:
            flash("Usuário bloqueado. Contate o administrador.", "error")
            return redirect(url_for('main_bp.login'))

        # ✅ Login bem-sucedido
        login_user(usuario)
        session['usuario'] = usuario.usuario
        session['is_admin'] = usuario.is_admin
        session['id_usuario'] = usuario.id_usuario

        flash(f"Bem-vindo, {usuario.nome}!", "success")

        # Sempre redireciona para tramitação de processos
        return redirect(url_for('processos_bp.dashboard_processos'))

    return render_template('login.html')


# ==========================================================
# 3️⃣ Cadastro de novos usuários
# ==========================================================
@main_bp.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    """Permite ao usuário solicitar cadastro no sistema"""
    if request.method == 'POST':
        nome = (request.form.get('nome_completo') or '').strip()
        email = (request.form.get('email') or '').strip()
        usuario = (request.form.get('username') or '').strip()
        senha = request.form.get('senha')
        confirmar = request.form.get('confirmar_senha')

        # ⚠️ Validações
        if senha != confirmar:
            flash("As senhas não coincidem.", "error")
            return redirect(url_for('main_bp.cadastro'))

        if not email.endswith('@novacap.df.gov.br'):
            flash("Utilize seu e-mail institucional (@novacap.df.gov.br).", "warning")
            return redirect(url_for('main_bp.cadastro'))

        existente = Usuario.query.filter(
            (Usuario.usuario == usuario) | (Usuario.email == email)
        ).first()

        if existente:
            flash("E-mail ou nome de usuário já cadastrado.", "error")
            return redirect(url_for('main_bp.cadastro'))

        # ✅ Cria novo usuário pendente
        novo_usuario = Usuario(
            nome=nome,
            email=email,
            usuario=usuario,
            senha_hash=generate_password_hash(senha),
            aprovado=False,
            bloqueado=False,
            is_admin=False
        )

        db.session.add(novo_usuario)
        db.session.commit()

        flash("✅ Cadastro enviado com sucesso. Aguarde aprovação do administrador.", "success")
        return redirect(url_for('main_bp.login'))

    return render_template('cadastro.html')


# ==========================================================
# 4️⃣ Redefinição de senha
# ==========================================================
@main_bp.route('/trocar-senha', methods=['GET', 'POST'])
def trocar_senha():
    """Permite redefinir senha a partir do nome e e-mail"""
    if request.method == 'POST':
        nome = (request.form.get('nome_completo') or '').strip()
        email = (request.form.get('email') or '').strip()
        nova_senha = request.form.get('nova_senha')
        confirmar = request.form.get('confirmar_senha')

        # ⚠️ Verificações
        if nova_senha != confirmar:
            flash("As senhas não coincidem.", "error")
            return redirect(url_for('main_bp.trocar_senha'))

        usuario = Usuario.query.filter_by(nome=nome, email=email).first()
        if not usuario:
            flash("Usuário não encontrado com os dados informados.", "error")
            return redirect(url_for('main_bp.trocar_senha'))

        # ✅ Atualiza senha
        usuario.senha_hash = generate_password_hash(nova_senha)
        db.session.commit()

        flash("Senha alterada com sucesso. Faça login novamente.", "success")
        return redirect(url_for('main_bp.login'))

    return render_template('trocar_senha.html')


# ==========================================================
# 5️⃣ Logout
# ==========================================================
@main_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """Encerra sessão do usuário"""
    logout_user()
    session.clear()
    flash("Sessão encerrada com sucesso.", "info")
    return redirect(url_for('main_bp.login'))


# ==========================================================
# 6️⃣ Busca Global Instantânea (US09)
# ==========================================================
@main_bp.route('/api/busca-global')
@login_required
def api_busca_global():
    """
    Retorna resultados dinâmicos para a barra de busca instantânea do cabeçalho.
    Inclui correspondências de processos SEI e atalhos de navegação rápida.
    """
    termo = (request.args.get('q') or '').strip()
    if not termo or len(termo) < 2:
        return jsonify({'processos': [], 'atalhos': []})

    # 1. Busca em Processos
    termo_limpo = termo.replace(' ', '')
    processos = (
        Processo.query
        .filter(
            or_(
                Processo.numero_processo.ilike(f"%{termo}%"),
                Processo.numero_processo.ilike(f"%{termo_limpo}%")
            )
        )
        .order_by(Processo.id_processo.desc())
        .limit(6)
        .all()
    )

    resultados_processos = []
    for p in processos:
        resultados_processos.append({
            'id': p.id_processo,
            'numero': p.numero_processo,
            'status': p.status_atual or 'Sem status',
            'diretoria': p.diretoria_destino or 'Não informada',
            'url_consulta': url_for('processos_bp.consultar_processos', numero_processo=p.numero_processo),
            'url_alterar': url_for('processos_bp.alterar_processo', id_processo=p.id_processo)
        })

    # 2. Atalhos de navegação rápida
    atalhos_base = [
        {
            'titulo': 'Cadastrar Novo Processo',
            'subtitulo': 'Iniciar nova tramitação SEI',
            'icone': 'fas fa-plus-circle',
            'url': url_for('processos_bp.cadastro_processo'),
            'tags': 'cadastrar novo processo sei entrada criar'
        },
        {
            'titulo': 'Consultar Processos',
            'subtitulo': 'Buscar e filtrar tabela unificada',
            'icone': 'fas fa-folder-open',
            'url': url_for('processos_bp.consultar_processos'),
            'tags': 'consultar listar pesquisar processos tabela busca'
        },
        {
            'titulo': 'Painel de Controle',
            'subtitulo': 'Indicadores e métricas de desempenho',
            'icone': 'fas fa-chart-pie',
            'url': url_for('processos_bp.dashboard_processos'),
            'tags': 'painel dashboard kpi totais metricas graficos tramitacao'
        },
        {
            'titulo': 'Relatórios Avançados',
            'subtitulo': 'Análise detalhada por RA, diretoria e status',
            'icone': 'fas fa-file-alt',
            'url': url_for('relatorios_bp.relatorios_avancados'),
            'tags': 'relatorios relatorio avancado bi exportar csv excel'
        }
    ]

    if session.get('is_admin'):
        atalhos_base.append({
            'titulo': 'Painel Administrativo',
            'subtitulo': 'Gerenciamento de usuários e permissões',
            'icone': 'fas fa-user-cog',
            'url': url_for('admin_bp.painel_admin'),
            'tags': 'admin administracao usuarios permissoes moderacao'
        })

    t_lower = termo.lower()
    atalhos_correspondentes = [
        a for a in atalhos_base
        if t_lower in a['titulo'].lower() or any(tag in t_lower for tag in a['tags'].split())
    ]

    return jsonify({
        'processos': resultados_processos,
        'atalhos': atalhos_correspondentes
    })


# ==========================================================
# 7️⃣ Teste de conexão com banco
# ==========================================================
@main_bp.route("/teste-db")
def testar_banco():
    try:
        resultado = db.session.execute(text("SELECT 1")).scalar()
        return jsonify({
            "status": "OK",
            "mensagem": "Conexão com o banco Neon funcionando!",
            "retorno": resultado
        }), 200
    except Exception as e:
        return jsonify({
            "status": "ERRO",
            "mensagem": "Falha ao conectar ao banco Neon",
            "detalhes": str(e)
        }), 500
