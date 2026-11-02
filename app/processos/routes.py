# app/processos/routes.py
"""
Rotas do módulo de Processos (Tramitação SEI) — CR-NOVACAP.
Inclui: dashboard com atualização dinâmica, cadastro, alteração,
consulta unificada com ordenação em tempo real e exportações (CSV, XLSX, PDF).
"""

import os
import csv
import io
from datetime import datetime
from io import BytesIO
import pandas as pd

from flask import (
    render_template, request, redirect, url_for, flash,
    send_file, jsonify, current_app, Response
)
from flask_login import login_required, current_user

from app.ext import db, csrf
from app.models.modelos import (
    Processo, EntradaProcesso, Demanda, RegiaoAdministrativa,
    Status, Usuario, Movimentacao, Diretoria, Alerta,
    AuditoriaProcesso, LogUsuario
)
from app.processos import processos_bp

# Bibliotecas para PDF
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


# ==========================================================
# 📊 CÁLCULO CONSOLIDADO DE MÉTRICAS (US03)
# ==========================================================
def calcular_metricas_dashboard():
    """Calcula e retorna as métricas consolidadas dos processos em tramitação"""
    # === Totais Gerais ===
    total_processos = Processo.query.count()

    # === Diretoria de Destino ===
    processos_dc = Processo.query.filter(Processo.diretoria_destino.like('%Cidades%')).count()
    processos_do = Processo.query.filter(Processo.diretoria_destino.like('%Obras%')).count()
    processos_dp = Processo.query.filter(Processo.diretoria_destino.like('%Planejamento%')).count()
    processos_ds = Processo.query.filter(Processo.diretoria_destino.like('%Suporte%')).count()
    processos_sgia = Processo.query.filter(Processo.diretoria_destino.like('%SGIA%')).count()
    processos_ext = Processo.query.filter(Processo.diretoria_destino.like('%EXT%')).count()

    # === Situação dos Processos ===
    processos_atendidos = Processo.query.filter_by(status_atual='Atendido').count()
    devolvidos_ra = Processo.query.filter(Processo.status_atual.like('Devolvido à RA%')).count()
    processos_improcedentes = Processo.query.filter(Processo.status_atual.like('Improcedente%')).count()

    # === Especiais ===
    processos_urgentes = Processo.query.filter_by(status_atual='Solicitação de urgência').count()
    processos_prazo_execucao = Processo.query.filter_by(status_atual='Solicitação de prazo de execução').count()
    processos_ouvidoria = Processo.query.filter_by(status_atual='Processo oriundo de Ouvidoria').count()

    # === Em atendimento (ativos na NOVACAP) ===
    processos_em_atendimento = Processo.query.filter(
        Processo.status_atual.in_([
            'Enviado à Diretoria das Cidades',
            'Enviado à Diretoria de Obras',
            'Enviado à Diretoria de Planejamento e Projetos',
            'Enviado à Diretoria de Suporte',
            'Solicitação de urgência',
            'Solicitação de prazo de execução'
        ])
    ).count()

    # === Encerrados (resultado final) ===
    processos_encerrados = processos_atendidos + processos_improcedentes + devolvidos_ra

    return {
        'total_processos': total_processos,
        'total_em_atendimento': processos_em_atendimento,
        'processos_dc': processos_dc,
        'processos_do': processos_do,
        'processos_dp': processos_dp,
        'processos_ds': processos_ds,
        'processos_sgia': processos_sgia,
        'processos_ext': processos_ext,
        'processos_atendidos': processos_atendidos,
        'devolvidos_ra': devolvidos_ra,
        'processos_improcedentes': processos_improcedentes,
        'processos_encerrados': processos_encerrados,
        'processos_urgentes': processos_urgentes,
        'processos_prazo_execucao': processos_prazo_execucao,
        'processos_ouvidoria': processos_ouvidoria,
        'timestamp': datetime.now().strftime('%H:%M:%S')
    }


# ==========================================================
# 1️⃣ DASHBOARD DE PROCESSOS
# ==========================================================
@processos_bp.route('/dashboard')
@login_required
def dashboard_processos():
    """Painel de Controle — Processos SEI tramitando pela CR/NOVACAP"""
    metricas = calcular_metricas_dashboard()
    return render_template('dashboard_processos.html', **metricas)


@processos_bp.route('/api/stats')
@login_required
def api_dashboard_stats():
    """API para atualização dinâmica em tempo real dos cards de indicadores (US03)"""
    return jsonify(calcular_metricas_dashboard())


# ==========================================================
# 2️⃣ CADASTRO DE PROCESSO
# ==========================================================
@processos_bp.route('/cadastro', methods=['GET', 'POST'])
@login_required
def cadastro_processo():
    """Cadastra um novo processo SEI"""
    if request.method == 'POST':
        numero = request.form.get('numero_processo', '').strip().replace(' ', '').replace('\u200b', '')

        # Verifica duplicidade
        existente = Processo.query.filter(
            db.func.replace(Processo.numero_processo, ' ', '') == numero
        ).first()

        if existente:
            flash(f"⚠ O processo {numero} já está cadastrado no sistema.", "warning")
            return redirect(url_for('processos_bp.consultar_processos', numero_processo=numero))

        try:
            data_criacao_ra = datetime.strptime(request.form.get('data_criacao_ra'), "%Y-%m-%d").date()
            data_entrada_novacap = datetime.strptime(request.form.get('data_entrada_novacap'), "%Y-%m-%d").date()
            data_documento = datetime.strptime(request.form.get('data_documento'), "%Y-%m-%d").date()

            novo = Processo(
                numero_processo=numero,
                status_atual=request.form.get('status_inicial'),
                observacoes=request.form.get('observacoes'),
                diretoria_destino=request.form.get('diretoria_destino')
            )
            db.session.add(novo)
            db.session.flush()

            entrada = EntradaProcesso(
                id_processo=novo.id_processo,
                data_criacao_ra=data_criacao_ra,
                data_entrada_novacap=data_entrada_novacap,
                data_documento=data_documento,
                ra_origem=request.form.get('ra_origem'),
                id_demanda=int(request.form.get('id_demanda')),
                usuario_responsavel=int(request.form.get('usuario_responsavel')),
                status_inicial=request.form.get('status_inicial')
            )
            db.session.add(entrada)
            db.session.flush()

            primeira_mov = Movimentacao(
                id_entrada=entrada.id_entrada,
                id_usuario=entrada.usuario_responsavel,
                novo_status=entrada.status_inicial,
                observacao="Cadastro inicial do processo.",
                data=data_documento
            )
            db.session.add(primeira_mov)

            # 🔍 Trilha de Auditoria (US08)
            ip_origem = request.headers.get('X-Forwarded-For', request.remote_addr)
            id_autor = current_user.id_usuario if current_user.is_authenticated else entrada.usuario_responsavel
            auditoria_inicial = AuditoriaProcesso(
                id_processo=novo.id_processo,
                id_usuario=id_autor,
                campo_alterado='Criação do Processo',
                valor_anterior='---',
                valor_novo=f"Status: {novo.status_atual} | Destino: {novo.diretoria_destino}",
                acao='Cadastro Inicial',
                justificativa=novo.observacoes or 'Cadastro inicial e autuação do processo.',
                data_hora=datetime.now(),
                ip_origem=ip_origem
            )
            db.session.add(auditoria_inicial)

            # Sincronização com log de usuário
            if id_autor:
                log_u = LogUsuario(
                    id_usuario=id_autor,
                    acao="Cadastro de Processo",
                    tabela_afetada="processos",
                    id_referencia=novo.id_processo,
                    descricao_detalhada=f"Processo {numero} autuado no sistema.",
                    ip_origem=ip_origem,
                    data_hora=datetime.now()
                )
                db.session.add(log_u)

            db.session.commit()

            flash(f"✅ Processo {numero} cadastrado com sucesso!", "success")
            return redirect(url_for('processos_bp.detalhes_processo', id_processo=novo.id_processo))

        except Exception as e:
            db.session.rollback()
            flash(f"❌ Erro ao cadastrar processo: {str(e)}", "danger")
            return redirect(url_for('processos_bp.cadastro_processo'))

    regioes = RegiaoAdministrativa.query.order_by(RegiaoAdministrativa.descricao_ra.asc()).all()
    demandas = Demanda.query.order_by(Demanda.descricao.asc()).all()
    status = Status.query.order_by(Status.descricao.asc()).all()
    usuarios = Usuario.query.filter_by(aprovado=True, bloqueado=False).order_by(Usuario.usuario.asc()).all()
    diretorias = Diretoria.query.order_by(Diretoria.nome_completo.asc()).all()

    return render_template(
        'cadastro_processo.html',
        regioes=regioes,
        demandas=demandas,
        status=status,
        usuarios=usuarios,
        diretorias=[d.nome_completo for d in diretorias]
    )


# ==========================================================
# 3️⃣ ALTERAR PROCESSO
# ==========================================================
@processos_bp.route('/alterar/<int:id_processo>', methods=['GET', 'POST'])
@login_required
def alterar_processo(id_processo):
    """Atualiza o status, responsável e registra movimentação com trilha de auditoria (US08)"""
    processo = Processo.query.get_or_404(id_processo)
    entrada = EntradaProcesso.query.filter_by(id_processo=id_processo).first()

    if request.method == 'POST':
        try:
            status_anterior = processo.status_atual or "---"
            obs_anterior = processo.observacoes or "---"
            resp_anterior = entrada.responsavel if (entrada and entrada.responsavel) else None
            resp_anterior_nome = resp_anterior.nome if resp_anterior else (f"ID {entrada.usuario_responsavel}" if (entrada and entrada.usuario_responsavel) else "Não definido")

            novo_status = request.form.get('novo_status')
            observacao = request.form.get('observacao', '').strip()
            data_movimentacao = datetime.strptime(request.form.get('data_movimentacao'), "%Y-%m-%d")
            responsavel_id = int(request.form.get('responsavel_tecnico'))
            novo_resp = Usuario.query.get(responsavel_id)
            novo_resp_nome = novo_resp.nome if novo_resp else f"ID {responsavel_id}"

            # 1. Cria nova movimentação
            if entrada:
                nova_mov = Movimentacao(
                    id_entrada=entrada.id_entrada,
                    id_usuario=responsavel_id,
                    novo_status=novo_status,
                    observacao=observacao,
                    data=data_movimentacao
                )
                db.session.add(nova_mov)

            # 2. Metadados de auditoria (US08)
            ip_origem = request.headers.get('X-Forwarded-For', request.remote_addr)
            id_autor = current_user.id_usuario if current_user.is_authenticated else responsavel_id

            # Registra auditoria: Alteração de Status
            if status_anterior != novo_status:
                db.session.add(AuditoriaProcesso(
                    id_processo=processo.id_processo,
                    id_usuario=id_autor,
                    campo_alterado='Status Atual',
                    valor_anterior=status_anterior,
                    valor_novo=novo_status,
                    acao='Alteração de Status',
                    justificativa=observacao or 'Atualização periódica de tramitação.',
                    data_hora=datetime.now(),
                    ip_origem=ip_origem
                ))

            # Registra auditoria: Alteração de Responsável Técnico
            if entrada and entrada.usuario_responsavel != responsavel_id:
                db.session.add(AuditoriaProcesso(
                    id_processo=processo.id_processo,
                    id_usuario=id_autor,
                    campo_alterado='Responsável Técnico',
                    valor_anterior=resp_anterior_nome,
                    valor_novo=novo_resp_nome,
                    acao='Reatribuição de Responsável',
                    justificativa=observacao or 'Transferência de responsabilidade técnica.',
                    data_hora=datetime.now(),
                    ip_origem=ip_origem
                ))
                entrada.usuario_responsavel = responsavel_id

            # Registra auditoria: Despacho / Observações
            if observacao and observacao != obs_anterior:
                db.session.add(AuditoriaProcesso(
                    id_processo=processo.id_processo,
                    id_usuario=id_autor,
                    campo_alterado='Despacho / Observação',
                    valor_anterior=obs_anterior,
                    valor_novo=observacao,
                    acao='Novo Despacho Registrado',
                    justificativa=observacao,
                    data_hora=datetime.now(),
                    ip_origem=ip_origem
                ))

            # Atualiza objeto Processo
            processo.status_atual = novo_status
            processo.observacoes = observacao

            # Sincroniza log geral de auditoria
            if id_autor:
                db.session.add(LogUsuario(
                    id_usuario=id_autor,
                    acao="Alteração de Processo",
                    tabela_afetada="processos",
                    id_referencia=processo.id_processo,
                    descricao_detalhada=f"Processo {processo.numero_processo} atualizado para status '{novo_status}' com responsável '{novo_resp_nome}'.",
                    ip_origem=ip_origem,
                    data_hora=datetime.now()
                ))

            db.session.commit()

            flash("✅ Movimentação registrada e trilha de auditoria atualizada com sucesso!", "success")
            return redirect(url_for('processos_bp.detalhes_processo', id_processo=processo.id_processo))

        except Exception as e:
            db.session.rollback()
            flash(f"❌ Erro ao atualizar processo: {str(e)}", "danger")
            return redirect(url_for('processos_bp.alterar_processo', id_processo=id_processo))

    usuarios = Usuario.query.filter_by(aprovado=True, bloqueado=False).order_by(Usuario.usuario.asc()).all()
    status = Status.query.order_by(Status.descricao.asc()).all()

    return render_template(
        'alterar_processo.html',
        processo=processo,
        entrada=entrada,
        usuarios=usuarios,
        status=status
    )


# ==========================================================
# 🔍 DETALHAMENTO DO PROCESSO & TRILHA DE AUDITORIA (US08)
# ==========================================================
@processos_bp.route('/detalhes/<int:id_processo>', methods=['GET'])
@login_required
def detalhes_processo(id_processo):
    """
    Visualização de detalhamento do processo e trilha de auditoria (US08).
    Modo estritamente somente leitura acessível a partir da consulta de processos.
    Exibe dados consolidados e histórico cronológico completo de todas as alterações com
    data/hora, responsável e valores antes/depois.
    """
    processo = Processo.query.get_or_404(id_processo)
    entrada = EntradaProcesso.query.filter_by(id_processo=id_processo).first()
    
    # Ordem cronológica (padrão: mais recentes primeiro; permite alternar para mais antigos primeiro)
    ordem = request.args.get('ordem', 'desc').lower()
    if ordem == 'asc':
        historico = AuditoriaProcesso.query.filter_by(id_processo=id_processo)\
            .order_by(AuditoriaProcesso.data_hora.asc(), AuditoriaProcesso.id_auditoria.asc()).all()
    else:
        historico = AuditoriaProcesso.query.filter_by(id_processo=id_processo)\
            .order_by(AuditoriaProcesso.data_hora.desc(), AuditoriaProcesso.id_auditoria.desc()).all()
    
    # Auto-recuperação de conformidade US08: se não houver histórico, cria o registro inicial
    if not historico:
        ip_origem = request.headers.get('X-Forwarded-For', request.remote_addr)
        id_autor = entrada.usuario_responsavel if (entrada and entrada.usuario_responsavel) else (current_user.id_usuario if current_user.is_authenticated else 1)
        dt_inicial = entrada.data_entrada_novacap if (entrada and entrada.data_entrada_novacap) else datetime.now()
        base_aud = AuditoriaProcesso(
            id_processo=processo.id_processo,
            id_usuario=id_autor,
            campo_alterado='Criação do Processo',
            valor_anterior='---',
            valor_novo=f"Status: {processo.status_atual or 'Não informado'} | Destino: {processo.diretoria_destino or 'Não definido'}",
            acao='Cadastro Inicial',
            justificativa=processo.observacoes or 'Registro cadastral inicial do processo no sistema.',
            data_hora=dt_inicial,
            ip_origem=ip_origem or '127.0.0.1 (Registro Automático)'
        )
        db.session.add(base_aud)
        db.session.commit()
        historico = [base_aud]

    demanda = Demanda.query.get(entrada.id_demanda) if (entrada and entrada.id_demanda) else None
    responsavel = Usuario.query.get(entrada.usuario_responsavel) if (entrada and entrada.usuario_responsavel) else None
    movimentacoes = Movimentacao.query.filter_by(id_entrada=entrada.id_entrada).order_by(Movimentacao.data.desc()).all() if entrada else []

    return render_template(
        'detalhes_processo.html',
        processo=processo,
        entrada=entrada,
        demanda=demanda,
        responsavel=responsavel,
        historico=historico,
        movimentacoes=movimentacoes,
        ordem=ordem
    )


# ==========================================================
# 🔍 API JSON - TRILHA DE AUDITORIA (US08)
# ==========================================================
@processos_bp.route('/api/auditoria/<int:id_processo>', methods=['GET'])
@login_required
def api_auditoria_processo(id_processo):
    """Retorna a trilha de auditoria do processo em formato JSON"""
    historico = AuditoriaProcesso.query.filter_by(id_processo=id_processo)\
        .order_by(AuditoriaProcesso.data_hora.desc(), AuditoriaProcesso.id_auditoria.desc()).all()
    return jsonify([h.to_dict() for h in historico])


# ==========================================================
# 🔍 EXPORTAR TRILHA DE AUDITORIA EM CSV (US08)
# ==========================================================
@processos_bp.route('/auditoria/csv/<int:id_processo>', methods=['GET'])
@login_required
def exportar_auditoria_csv(id_processo):
    """Exporta a trilha de auditoria completa do processo em formato CSV (US08)"""
    processo = Processo.query.get_or_404(id_processo)
    historico = AuditoriaProcesso.query.filter_by(id_processo=id_processo)\
        .order_by(AuditoriaProcesso.data_hora.asc(), AuditoriaProcesso.id_auditoria.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow([
        'ID Auditoria',
        'Nº Processo',
        'Data e Hora',
        'Responsável',
        'Ação',
        'Campo Alterado',
        'Valor Anterior',
        'Valor Novo',
        'Justificativa / Despacho',
        'IP Origem'
    ])

    for h in historico:
        writer.writerow([
            h.id_auditoria,
            processo.numero_processo,
            h.data_hora.strftime('%d/%m/%Y %H:%M:%S') if h.data_hora else '',
            h.usuario.nome if h.usuario else 'Sistema / Auditoria Automática',
            h.acao or 'Alteração',
            h.campo_alterado,
            h.valor_anterior or '',
            h.valor_novo or '',
            h.justificativa or '',
            h.ip_origem or ''
        ])

    output.seek(0)
    nome_arquivo = f"auditoria_{processo.numero_processo.replace('/', '_')}.csv"
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={nome_arquivo}"}
    )


# ==========================================================
# 4️⃣ EXCLUIR PROCESSO
# ==========================================================
@processos_bp.route('/excluir/<int:id_processo>', methods=['POST'])
@login_required
def excluir_processo(id_processo):
    """Exclui um processo e seus registros vinculados"""
    processo = Processo.query.get_or_404(id_processo)

    try:
        entradas = EntradaProcesso.query.filter_by(id_processo=id_processo).all()

        for entrada in entradas:
            Alerta.query.filter_by(id_entrada=entrada.id_entrada).delete()
            Movimentacao.query.filter_by(id_entrada=entrada.id_entrada).delete()
            db.session.delete(entrada)

        AuditoriaProcesso.query.filter_by(id_processo=id_processo).delete()
        numero_processo = processo.numero_processo
        db.session.delete(processo)
        db.session.commit()

        flash(f"✅ Processo {numero_processo} excluído com sucesso!", "success")
        return redirect(url_for('processos_bp.consultar_processos'))

    except Exception as e:
        db.session.rollback()
        flash(f"❌ Erro ao excluir processo: {str(e)}", "danger")
        return redirect(url_for('processos_bp.alterar_processo', id_processo=id_processo))


# ==========================================================
# 5️⃣ CONSULTA UNIFICADA (US04 - Ordenação por Colunas)
# ==========================================================
@processos_bp.route('/consultar', methods=['GET'])
@login_required
def consultar_processos():
    """Consulta unificada de processos com ordenação e carregamento otimizado"""
    numero = request.args.get('numero_processo', '').strip()
    status_filtro = request.args.get('status')
    ra = request.args.get('ra')
    diretoria = request.args.get('diretoria')
    demanda = request.args.get('demanda')
    inicio = request.args.get('inicio')
    fim = request.args.get('fim')

    query = db.session.query(Processo).join(EntradaProcesso)

    if numero:
        query = query.filter(Processo.numero_processo.like(f"%{numero}%"))
    if status_filtro:
        query = query.filter(Processo.status_atual == status_filtro)
    if ra:
        query = query.filter(EntradaProcesso.ra_origem == ra)
    if diretoria:
        query = query.filter(Processo.diretoria_destino == diretoria)
    if demanda:
        query = query.filter(EntradaProcesso.id_demanda == demanda)
    if inicio and fim:
        inicio_dt = datetime.strptime(inicio, "%Y-%m-%d")
        fim_dt = datetime.strptime(fim, "%Y-%m-%d")
        query = query.filter(EntradaProcesso.data_entrada_novacap.between(inicio_dt, fim_dt))
    elif inicio:
        inicio_dt = datetime.strptime(inicio, "%Y-%m-%d")
        query = query.filter(EntradaProcesso.data_entrada_novacap >= inicio_dt)
    elif fim:
        fim_dt = datetime.strptime(fim, "%Y-%m-%d")
        query = query.filter(EntradaProcesso.data_entrada_novacap <= fim_dt)

    # 🔀 Ordenação dinâmica das colunas (US04)
    sort_by = request.args.get('sort_by', 'id').strip()
    order = request.args.get('order', 'desc').strip().lower()
    if order not in ['asc', 'desc']:
        order = 'desc'

    order_map = {
        'numero': Processo.numero_processo,
        'ra': EntradaProcesso.ra_origem,
        'diretoria': Processo.diretoria_destino,
        'status': Processo.status_atual,
        'data': EntradaProcesso.data_documento,
        'id': Processo.id_processo
    }
    coluna_ordenacao = order_map.get(sort_by, Processo.id_processo)
    if order == 'asc':
        query = query.order_by(coluna_ordenacao.asc())
    else:
        query = query.order_by(coluna_ordenacao.desc())

    # Paginação / Carregamento sob demanda (Otimização de Performance)
    try:
        limit = int(request.args.get('limit', 25))
        if limit < 1:
            limit = 25
    except (ValueError, TypeError):
        limit = 25

    total_processos = query.count()
    processos = query.limit(limit).all()

    if not processos and total_processos == 0:
        flash("Nenhum processo encontrado com os filtros aplicados.", "warning")

    for p in processos:
        entrada = EntradaProcesso.query.filter_by(id_processo=p.id_processo).first()
        p.entrada = entrada
        if entrada:
            entrada.demanda = Demanda.query.get(entrada.id_demanda)
            ultima_mov = Movimentacao.query.filter_by(id_entrada=entrada.id_entrada).order_by(Movimentacao.data.desc()).first()
            p.ultima_data = ultima_mov.data if ultima_mov else entrada.data_documento

    todas_ras = RegiaoAdministrativa.query.order_by(RegiaoAdministrativa.nome_unidade).all()
    todos_status = Status.query.order_by(Status.ordem_exibicao).all()
    demandas = Demanda.query.order_by(Demanda.descricao.asc()).all()
    diretorias = [d.nome_completo for d in Diretoria.query.order_by(Diretoria.nome_completo.asc()).all()]

    return render_template(
        "consultar_processos.html",
        processos=processos,
        total_processos=total_processos,
        limit=limit,
        sort_by=sort_by,
        order=order,
        todas_ras=todas_ras,
        todos_status=todos_status,
        demandas=demandas,
        diretorias=diretorias
    )


# ==========================================================
# 6️⃣ EXPORTAR PROCESSO PDF
# ==========================================================
@processos_bp.route('/exportar-processo/<int:id_processo>')
@login_required
def exportar_processo_pdf(id_processo):
    """Gera PDF institucional com os dados completos do processo"""
    processo = Processo.query.get_or_404(id_processo)
    entrada = EntradaProcesso.query.filter_by(id_processo=id_processo).first()
    movimentacoes = Movimentacao.query.filter_by(id_entrada=entrada.id_entrada).order_by(Movimentacao.data.asc()).all() if entrada else []

    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    logo_path = os.path.join(current_app.root_path, "static", "images", "logo-novacap.png")
    if os.path.exists(logo_path):
        try:
            elements.append(Image(logo_path, width=120, height=35))
            elements.append(Spacer(1, 8))
        except Exception:
            pass


    elements.append(Paragraph("<b>Relatório Institucional de Processo</b>", styles['Title']))
    elements.append(Spacer(1, 12))

    info_table = [
        ["Número do Processo", processo.numero_processo],
        ["Status Atual", processo.status_atual or "---"],
        ["Diretoria de Destino", processo.diretoria_destino or "---"],
        ["Observações", processo.observacoes or "---"],
    ]
    table = Table(info_table, colWidths=[160, 370])
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))

    if entrada:
        entrada_table = [
            ["RA de Origem", entrada.ra_origem or "---"],
            ["Data de Entrada", entrada.data_entrada_novacap.strftime("%d/%m/%Y") if entrada.data_entrada_novacap else "---"],
            ["Demanda", entrada.demanda.descricao if entrada.demanda else "---"],
        ]
        elements.append(Paragraph("<b>Informações da Entrada</b>", styles['Heading2']))
        t2 = Table(entrada_table, colWidths=[200, 330])
        t2.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.25, colors.grey)]))
        elements.append(t2)
        elements.append(Spacer(1, 12))

    elements.append(Paragraph("<b>Histórico de Movimentações</b>", styles['Heading2']))
    if movimentacoes:
        mov_table = [["Data", "Status", "Responsável", "Observação"]]
        for m in movimentacoes:
            usuario = Usuario.query.get(m.id_usuario)
            mov_table.append([
                m.data.strftime("%d/%m/%Y") if m.data else "---",
                m.novo_status or "---",
                usuario.nome if usuario else "---",
                m.observacao or "---"
            ])
        t3 = Table(mov_table, repeatRows=1, colWidths=[80, 120, 120, 210])
        t3.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#004A8F")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ]))
        elements.append(t3)
    else:
        elements.append(Paragraph("Nenhuma movimentação registrada.", styles['Normal']))

    # 🔍 Trilha de Auditoria e Histórico de Alterações (US08)
    elements.append(Spacer(1, 14))
    elements.append(Paragraph("<b>Trilha de Auditoria e Histórico de Alterações (US08)</b>", styles['Heading2']))
    
    auditorias = AuditoriaProcesso.query.filter_by(id_processo=id_processo)\
        .order_by(AuditoriaProcesso.data_hora.asc(), AuditoriaProcesso.id_auditoria.asc()).all()

    if auditorias:
        aud_table = [["Data/Hora", "Ação", "Campo Alterado", "Valor Anterior -> Novo", "Responsável"]]
        for a in auditorias:
            resp_nome = a.usuario.nome if a.usuario else "Sistema / Auditoria"
            v_ant = (a.valor_anterior or '---')[:35]
            v_novo = (a.valor_novo or '---')[:35]
            transicao = f"{v_ant} -> {v_novo}"
            aud_table.append([
                a.data_hora.strftime("%d/%m/%Y %H:%M") if a.data_hora else "---",
                a.acao or "Alteração",
                a.campo_alterado or "Geral",
                transicao,
                resp_nome
            ])
        t_aud = Table(aud_table, repeatRows=1, colWidths=[80, 95, 95, 160, 100])
        t_aud.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#002D62")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(t_aud)
    else:
        elements.append(Paragraph("Nenhum registro de auditoria disponível.", styles['Normal']))

    doc.build(elements)
    output.seek(0)
    nome_arquivo = f"Processo_{processo.numero_processo.replace('/', '_')}.pdf"
    return send_file(output, as_attachment=True, download_name=nome_arquivo, mimetype='application/pdf')


# ==========================================================
# 7️⃣ VERIFICAR PROCESSO VIA AJAX
# ==========================================================
@csrf.exempt
@processos_bp.route("/verificar-processo", methods=["POST"])
@login_required
def verificar_processo():
    """Verifica se um número de processo SEI já existe (AJAX)"""
    data = request.get_json()
    numero = data.get("numero_processo", "").strip()
    if not numero:
        return jsonify({"erro": "Número do processo não informado."}), 400

    numero_limpo = ''.join(filter(str.isdigit, numero))
    processos = Processo.query.all()
    for p in processos:
        existente = ''.join(filter(str.isdigit, p.numero_processo or ''))
        if existente == numero_limpo:
            return jsonify({"existe": True, "id": p.id_processo})
    return jsonify({"existe": False})


# ==========================================================
# 8️⃣ EXPORTAR TRAMITAÇÕES (CSV / XLSX / PDF)
# ==========================================================
@processos_bp.route('/exportar-tramitacoes', methods=['GET'])
@login_required
def exportar_tramitacoes():
    """Exporta lista de processos filtrados (CSV, XLSX ou PDF)"""
    formato = request.args.get('formato', 'csv')
    status = request.args.get('status')
    ra = request.args.get('ra')
    diretoria = request.args.get('diretoria')
    demanda = request.args.get('demanda')
    inicio = request.args.get('inicio')
    fim = request.args.get('fim')

    query = Processo.query.join(EntradaProcesso, isouter=True)

    if status:
        query = query.filter(Processo.status_atual == status)
    if ra:
        query = query.filter(EntradaProcesso.ra_origem == ra)
    if diretoria:
        query = query.filter(Processo.diretoria_destino == diretoria)
    if demanda:
        query = query.filter(EntradaProcesso.id_demanda == demanda)
    if inicio and fim:
        try:
            inicio_dt = datetime.strptime(inicio, "%Y-%m-%d")
            fim_dt = datetime.strptime(fim, "%Y-%m-%d")
            query = query.filter(EntradaProcesso.data_entrada_novacap.between(inicio_dt, fim_dt))
        except Exception:
            pass

    processos = query.order_by(Processo.id_processo.desc()).all()
    if not processos:
        flash("Nenhum processo encontrado para exportação.", "warning")
        return redirect(url_for('processos_bp.consultar_processos'))

    dados = []
    for p in processos:
        entrada = EntradaProcesso.query.filter_by(id_processo=p.id_processo).first()
        dados.append({
            "Número do Processo": p.numero_processo,
            "Status Atual": p.status_atual,
            "Diretoria de Destino": p.diretoria_destino,
            "RA de Origem": entrada.ra_origem if entrada else "---",
            "Data de Entrada": entrada.data_entrada_novacap.strftime("%d/%m/%Y") if entrada and entrada.data_entrada_novacap else "---",
        })

    df = pd.DataFrame(dados)

    if formato == 'xlsx':
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        return send_file(
            output,
            as_attachment=True,
            download_name='processos.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    if formato == 'pdf':
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        elements.append(Paragraph("<b>Relatório de Processos</b>", styles['Title']))
        elements.append(Spacer(1, 12))
        tabela = Table([df.columns.to_list()] + df.values.tolist(), repeatRows=1)
        tabela.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#004A8F")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ]))
        elements.append(tabela)
        doc.build(elements)
        output.seek(0)
        return send_file(
            output,
            as_attachment=True,
            download_name='processos.pdf',
            mimetype='application/pdf'
        )

    output = BytesIO()
    df.to_csv(output, index=False, sep=';', encoding='utf-8-sig')
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name='processos.csv',
        mimetype='text/csv'
    )
