# app/admin/routes.py
"""
Rotas do módulo administrativo — CR-NOVACAP.
Inclui painel consolidado de usuários, aprovação, bloqueio, desbloqueio,
gerenciamento de permissões (admin/operador) e exclusão segura com auditoria (US05 e US06).
"""

from datetime import datetime
from flask import render_template, redirect, url_for, flash, session, request
from flask_login import login_required, current_user
from sqlalchemy import or_

from app.ext import db
from app.models.modelos import Usuario, LogUsuario, Movimentacao, EntradaProcesso
from app.admin import admin_bp


# ==========================================================
# 1️⃣ Painel Administrativo Consolidado (US05)
# ==========================================================
@admin_bp.route('/painel')
@login_required
def painel_admin():
    """
    Exibe o painel consolidado com a lista de usuários cadastrados.
    Suporta filtros por status (ativos, pendentes, bloqueados), perfil e termo de busca.
    """
    if not session.get('is_admin'):
        flash("Acesso restrito ao administrador.", "error")
        return redirect(url_for('main_bp.login'))

    termo_busca = request.args.get('q', '').strip()
    status_filtro = request.args.get('status', 'todos')
    perfil_filtro = request.args.get('perfil', 'todos')

    query = Usuario.query

    # Filtro textual (nome, usuário ou e-mail)
    if termo_busca:
        query = query.filter(
            or_(
                Usuario.nome.ilike(f"%{termo_busca}%"),
                Usuario.usuario.ilike(f"%{termo_busca}%"),
                Usuario.email.ilike(f"%{termo_busca}%")
            )
        )

    # Filtro de Status
    if status_filtro == 'ativos':
        query = query.filter(Usuario.aprovado == True, Usuario.bloqueado == False)
    elif status_filtro == 'pendentes':
        query = query.filter(Usuario.aprovado == False)
    elif status_filtro == 'bloqueados':
        query = query.filter(Usuario.bloqueado == True)

    # Filtro de Perfil
    if perfil_filtro == 'admin':
        query = query.filter(Usuario.is_admin == True)
    elif perfil_filtro == 'operador':
        query = query.filter(Usuario.is_admin == False)

    # Contagens consolidadas para as abas
    total_todos = Usuario.query.count()
    total_ativos = Usuario.query.filter(Usuario.aprovado == True, Usuario.bloqueado == False).count()
    total_pendentes = Usuario.query.filter(Usuario.aprovado == False).count()
    total_bloqueados = Usuario.query.filter(Usuario.bloqueado == True).count()

    usuarios = query.order_by(Usuario.nome.asc()).all()

    return render_template(
        'painel_admin.html',
        usuarios=usuarios,
        status_filtro=status_filtro,
        perfil_filtro=perfil_filtro,
        total_todos=total_todos,
        total_ativos=total_ativos,
        total_pendentes=total_pendentes,
        total_bloqueados=total_bloqueados
    )


# ==========================================================
# 2️⃣ Aprovar Usuário
# ==========================================================
@admin_bp.route('/aprovar/<int:id_usuario>', methods=['POST'])
@login_required
def aprovar_usuario(id_usuario):
    """Aprova o cadastro de um novo usuário e registra auditoria"""
    if not session.get('is_admin'):
        flash("Acesso restrito ao administrador.", "error")
        return redirect(url_for('main_bp.login'))

    usuario = Usuario.query.get_or_404(id_usuario)

    if usuario.aprovado:
        flash(f"ℹ️ O usuário '{usuario.usuario}' já está aprovado.", "info")
    else:
        usuario.aprovado = True
        log = LogUsuario(
            id_usuario=current_user.id_usuario,
            acao="APROVACAO_USUARIO",
            tabela_afetada="usuarios",
            id_referencia=id_usuario,
            descricao_detalhada=f"Cadastro do usuário '{usuario.usuario}' aprovado por '{current_user.usuario}'.",
            ip_origem=request.remote_addr,
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        flash(f"✅ Usuário '{usuario.usuario}' aprovado com sucesso.", "success")

    return redirect(url_for('admin_bp.painel_admin'))


# ==========================================================
# 3️⃣ Bloquear / Inativar Usuário (US06)
# ==========================================================
@admin_bp.route('/bloquear/<int:id_usuario>', methods=['POST'])
@login_required
def bloquear_usuario(id_usuario):
    """Bloqueia/inativa um usuário e registra auditoria"""
    if not session.get('is_admin'):
        flash("Acesso restrito ao administrador.", "error")
        return redirect(url_for('main_bp.login'))

    usuario = Usuario.query.get_or_404(id_usuario)

    if usuario.id_usuario == current_user.id_usuario:
        flash("Você não pode bloquear sua própria conta.", "warning")
        return redirect(url_for('admin_bp.painel_admin'))

    if usuario.bloqueado:
        flash(f"ℹ️ O usuário '{usuario.usuario}' já está bloqueado/inativo.", "info")
    else:
        usuario.bloqueado = True
        log = LogUsuario(
            id_usuario=current_user.id_usuario,
            acao="BLOQUEIO_USUARIO",
            tabela_afetada="usuarios",
            id_referencia=id_usuario,
            descricao_detalhada=f"Usuário '{usuario.usuario}' bloqueado/inativado por '{current_user.usuario}'.",
            ip_origem=request.remote_addr,
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        flash(f"🚫 Usuário '{usuario.usuario}' inativado com sucesso.", "warning")

    return redirect(url_for('admin_bp.painel_admin'))


# ==========================================================
# 4️⃣ Desbloquear / Reativar Usuário
# ==========================================================
@admin_bp.route('/desbloquear/<int:id_usuario>', methods=['POST'])
@login_required
def desbloquear_usuario(id_usuario):
    """Desbloqueia um usuário previamente bloqueado"""
    if not session.get('is_admin'):
        flash("Acesso restrito ao administrador.", "error")
        return redirect(url_for('main_bp.login'))

    usuario = Usuario.query.get_or_404(id_usuario)

    if not usuario.bloqueado:
        flash(f"ℹ️ O usuário '{usuario.usuario}' já está desbloqueado.", "info")
    else:
        usuario.bloqueado = False
        log = LogUsuario(
            id_usuario=current_user.id_usuario,
            acao="DESBLOQUEIO_USUARIO",
            tabela_afetada="usuarios",
            id_referencia=id_usuario,
            descricao_detalhada=f"Usuário '{usuario.usuario}' desbloqueado/reativado por '{current_user.usuario}'.",
            ip_origem=request.remote_addr,
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        flash(f"✅ Usuário '{usuario.usuario}' desbloqueado com sucesso.", "success")

    return redirect(url_for('admin_bp.painel_admin'))


# ==========================================================
# 5️⃣ Atribuir Permissão de Administrador
# ==========================================================
@admin_bp.route('/atribuir-admin/<int:id_usuario>', methods=['POST'])
@login_required
def atribuir_admin(id_usuario):
    """Concede perfil de administrador a um usuário"""
    if not session.get('is_admin'):
        flash("Acesso restrito ao administrador.", "error")
        return redirect(url_for('main_bp.login'))

    usuario = Usuario.query.get_or_404(id_usuario)

    if usuario.is_admin:
        flash(f"ℹ️ O usuário '{usuario.usuario}' já é administrador.", "info")
    else:
        usuario.is_admin = True
        log = LogUsuario(
            id_usuario=current_user.id_usuario,
            acao="CONCESSAO_ADMIN",
            tabela_afetada="usuarios",
            id_referencia=id_usuario,
            descricao_detalhada=f"Perfil de administrador concedido a '{usuario.usuario}' por '{current_user.usuario}'.",
            ip_origem=request.remote_addr,
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        flash(f"👑 Usuário '{usuario.usuario}' promovido a Administrador.", "success")

    return redirect(url_for('admin_bp.painel_admin'))


# ==========================================================
# 6️⃣ Revogar Permissão de Administrador (US05)
# ==========================================================
@admin_bp.route('/remover-admin/<int:id_usuario>', methods=['POST'])
@login_required
def remover_admin(id_usuario):
    """Revoga o perfil de administrador de um usuário"""
    if not session.get('is_admin'):
        flash("Acesso restrito ao administrador.", "error")
        return redirect(url_for('main_bp.login'))

    usuario = Usuario.query.get_or_404(id_usuario)

    if usuario.id_usuario == current_user.id_usuario:
        flash("Você não pode revogar seus próprios privilégios de administrador.", "warning")
        return redirect(url_for('admin_bp.painel_admin'))

    if not usuario.is_admin:
        flash(f"ℹ️ O usuário '{usuario.usuario}' não é administrador.", "info")
    else:
        usuario.is_admin = False
        log = LogUsuario(
            id_usuario=current_user.id_usuario,
            acao="REVOGACAO_ADMIN",
            tabela_afetada="usuarios",
            id_referencia=id_usuario,
            descricao_detalhada=f"Perfil de administrador revogado de '{usuario.usuario}' por '{current_user.usuario}'.",
            ip_origem=request.remote_addr,
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        flash(f"👤 Usuário '{usuario.usuario}' agora possui perfil Operador.", "info")

    return redirect(url_for('admin_bp.painel_admin'))


# ==========================================================
# 7️⃣ Excluir Usuário com Checagem de Dependências (US06)
# ==========================================================
@admin_bp.route('/excluir/<int:id_usuario>', methods=['POST'])
@login_required
def excluir_usuario(id_usuario):
    """
    Exclui conta de usuário verificando previamente integridade de dependências.
    Usuários com processos ou movimentações vinculadas não podem ser excluídos, apenas inativados.
    Registra auditoria em logs_usuarios.
    """
    if not session.get('is_admin'):
        flash("Acesso restrito ao administrador.", "error")
        return redirect(url_for('main_bp.login'))

    usuario = Usuario.query.get_or_404(id_usuario)

    if usuario.id_usuario == current_user.id_usuario:
        flash("Você não pode excluir sua própria conta.", "warning")
        return redirect(url_for('admin_bp.painel_admin'))

    # Verificação de dependências em processos e movimentações
    total_movs = Movimentacao.query.filter_by(id_usuario=id_usuario).count()
    total_entradas = EntradaProcesso.query.filter_by(usuario_responsavel=id_usuario).count()

    if total_movs > 0 or total_entradas > 0:
        total_vinculos = total_movs + total_entradas
        flash(
            f"⚠ Operação não permitida: O usuário '{usuario.usuario}' possui {total_vinculos} "
            f"registro(s) histórico(s) vinculados (tramitações/entradas). "
            f"Para preservar a integridade das informações públicas, o usuário não pode ser excluído permanentemente. "
            f"Utilize a opção 'Bloquear' para suspender seu acesso.",
            "warning"
        )
        return redirect(url_for('admin_bp.painel_admin'))

    nome_usuario = usuario.usuario
    email_usuario = usuario.email

    try:
        # Registrar auditoria antes de deletar a entidade
        log = LogUsuario(
            id_usuario=current_user.id_usuario,
            acao="EXCLUSAO_USUARIO",
            tabela_afetada="usuarios",
            id_referencia=id_usuario,
            descricao_detalhada=(
                f"Usuário '{nome_usuario}' ({email_usuario}) excluído permanentemente "
                f"pelo administrador '{current_user.usuario}' após checagem de dependências."
            ),
            ip_origem=request.remote_addr,
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.delete(usuario)
        db.session.commit()

        flash(f"✅ Usuário '{nome_usuario}' excluído permanentemente com sucesso (auditoria registrada).", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"❌ Erro ao excluir usuário: {str(e)}", "danger")

    return redirect(url_for('admin_bp.painel_admin'))
