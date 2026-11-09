# app/relatorios/routes.py
from datetime import datetime
from io import BytesIO
import pandas as pd

from flask import (
    render_template, request, redirect, url_for, flash, session,
    send_file, make_response
)
from flask_login import login_required

from app.ext import db
from app.models.modelos import (
    Movimentacao,
    Usuario,
    EntradaProcesso,
    Processo,
    Demanda,
    Status,
    RegiaoAdministrativa,
    Diretoria,
    Departamento
)

from app.relatorios import relatorios_bp


# ==========================================================
# 🔎 RELATÓRIO AVANÇADO COMPLETO
# ==========================================================
@relatorios_bp.route('/avancados')
@login_required
def relatorios_avancados():
    todos_status = Status.query.order_by(Status.ordem_exibicao).all()
    todas_ras = RegiaoAdministrativa.query.order_by(RegiaoAdministrativa.nome_unidade).all()
    todas_demandas = Demanda.query.order_by(Demanda.descricao.asc()).all()
    todas_diretorias = Diretoria.query.order_by(Diretoria.descricao_exibicao).all()
    todos_departamentos = Departamento.query.order_by(Departamento.nome).all()

    status_sel = request.args.get("status")
    ra_sel = request.args.get("ra")
    diretoria_sel = request.args.get("diretoria")
    departamento_sel = request.args.get("departamento")
    demanda_sel = request.args.get("servico")
    inicio = request.args.get("inicio")
    fim = request.args.get("fim")

    query = (
        db.session.query(
            Movimentacao,
            Usuario,
            EntradaProcesso,
            Processo,
            Demanda,
            Departamento,
            Diretoria
        )
        .outerjoin(Usuario, Movimentacao.id_usuario == Usuario.id_usuario)
        .outerjoin(EntradaProcesso, Movimentacao.id_entrada == EntradaProcesso.id_entrada)
        .outerjoin(Processo, EntradaProcesso.id_processo == Processo.id_processo)
        .outerjoin(Demanda, EntradaProcesso.id_demanda == Demanda.id_demanda)
        .outerjoin(Departamento, Demanda.id_departamento == Departamento.id_departamento)
        .outerjoin(Diretoria, Departamento.id_diretoria == Diretoria.id_diretoria)
    )

    if diretoria_sel:
        query = query.filter(
            db.or_(
                Diretoria.descricao_exibicao.ilike(f"%{diretoria_sel}%"),
                Processo.diretoria_destino.ilike(f"%{diretoria_sel}%")
            )
        )

    if departamento_sel:
        query = query.filter(Departamento.nome == departamento_sel)

    if demanda_sel:
        query = query.filter(Demanda.descricao == demanda_sel)

    if ra_sel:
        query = query.filter(EntradaProcesso.ra_origem == ra_sel)

    if status_sel:
        query = query.filter(Movimentacao.novo_status == status_sel)

    if inicio and fim:
        try:
            dt_inicio = datetime.strptime(inicio, "%Y-%m-%d")
            dt_fim = datetime.strptime(fim, "%Y-%m-%d")
            query = query.filter(Movimentacao.data.between(dt_inicio, dt_fim))
        except ValueError:
            flash("Formato de data inválido. Use AAAA-MM-DD.", "warning")

    resultados = query.order_by(Movimentacao.data.desc()).all()

    dados = []
    ras_distintas = set()
    demandas_distintas = set()
    status_count = {}
    diretoria_count = {}
    ra_count = {}
    total_atendidos = 0

    for mov, user, entrada, processo, demanda, departamento, diretoria in resultados:
        dt_str = mov.data.strftime("%d/%m/%Y %H:%M") if mov and mov.data else "—"
        dt_iso = mov.data.strftime("%Y-%m-%d") if mov and mov.data else ""
        mes_ano = mov.data.strftime("%m/%Y") if mov and mov.data else ""
        ano = mov.data.strftime("%Y") if mov and mov.data else ""
        mes_sort = mov.data.strftime("%Y-%m") if mov and mov.data else ""

        st = mov.novo_status if mov and mov.novo_status else "Não informado"

        # Prioriza diretoria associada ou fallback na diretoria_destino registrada no processo
        if diretoria and diretoria.descricao_exibicao:
            dir_nome = diretoria.descricao_exibicao
        elif processo and processo.diretoria_destino:
            dir_nome = processo.diretoria_destino
        else:
            dir_nome = "Não informado"

        ra_origem = entrada.ra_origem if entrada and entrada.ra_origem else "Não informado"
        servico_nome = demanda.descricao if demanda and demanda.descricao else "—"
        dep_nome = departamento.nome if departamento and departamento.nome else "Não informado"
        num_processo = processo.numero_processo if processo else "—"
        resp_usuario = user.usuario if user else "—"
        observacao = mov.observacao if mov and mov.observacao else ""

        dados.append({
            "Data": dt_str,
            "DataISO": dt_iso,
            "MesAno": mes_ano,
            "Ano": ano,
            "MesSort": mes_sort,
            "Número do Processo": num_processo,
            "RA": ra_origem,
            "Status": st,
            "Diretoria": dir_nome,
            "Departamento": dep_nome,
            "Serviço": servico_nome,
            "Responsável": resp_usuario,
            "Observação": observacao
        })

        if st in ["Atendido", "Concluído", "Deferido"]:
            total_atendidos += 1

        status_count[st] = status_count.get(st, 0) + 1
        diretoria_count[dir_nome] = diretoria_count.get(dir_nome, 0) + 1
        ra_count[ra_origem] = ra_count.get(ra_origem, 0) + 1

        if entrada and entrada.ra_origem:
            ras_distintas.add(entrada.ra_origem)
        if demanda and demanda.descricao:
            demandas_distintas.add(demanda.descricao)

    total_resultados = len(dados)
    total_ras = len(ras_distintas)
    total_demandas = len(demandas_distintas)

    taxa_atendimento = round((total_atendidos / total_resultados * 100), 1) if total_resultados > 0 else 0.0

    # Diretoria, Status e RA em destaque para indicadores consolidados (US02)
    diretoria_destaque = max(diretoria_count, key=diretoria_count.get) if diretoria_count else "—"
    diretoria_destaque_qtd = diretoria_count.get(diretoria_destaque, 0)
    diretoria_destaque_pct = round((diretoria_destaque_qtd / total_resultados * 100), 1) if total_resultados > 0 else 0.0

    status_predominante = max(status_count, key=status_count.get) if status_count else "—"
    status_predominante_qtd = status_count.get(status_predominante, 0)
    status_predominante_pct = round((status_predominante_qtd / total_resultados * 100), 1) if total_resultados > 0 else 0.0

    ra_destaque = max(ra_count, key=ra_count.get) if ra_count else "—"
    ra_destaque_qtd = ra_count.get(ra_destaque, 0)
    ra_destaque_pct = round((ra_destaque_qtd / total_resultados * 100), 1) if total_resultados > 0 else 0.0

    if any(term in status_predominante for term in ["Atendido", "Concluído", "Deferido"]):
        status_badge_class = "success"
    elif "Devolvido" in status_predominante:
        status_badge_class = "warning"
    elif "Improcedente" in status_predominante:
        status_badge_class = "danger"
    else:
        status_badge_class = "info"

    demandas_mapeadas = [
        {
            "descricao": d.descricao,
            "departamento": d.departamento.nome if d.departamento else "",
            "diretoria": (
                d.departamento.diretoria.descricao_exibicao
                if d.departamento and d.departamento.diretoria else ""
            )
        }
        for d in todas_demandas
    ]

    print("\n=== DEBUG RELATÓRIOS AVANÇADOS ===")
    print(f"URL acessada: {request.url}")
    print(f"Filtros recebidos: {dict(request.args)}")
    print(f"Resultados encontrados: {total_resultados}")
    print(f"Taxa de Atendimento: {taxa_atendimento}%")
    print(f"Diretoria Destaque: {diretoria_destaque} ({diretoria_destaque_qtd})")
    print(f"Status Predominante: {status_predominante} ({status_predominante_qtd})")
    print(f"RA Destaque: {ra_destaque} ({ra_destaque_qtd})")
    print("==================================\n")

    # Paginação / Carregamento fracionado da tabela (Otimização de Performance)
    try:
        limit = int(request.args.get('limit', 25))
        if limit < 1:
            limit = 25
    except (ValueError, TypeError):
        limit = 25

    tabela_resultados = resultados[:limit]

    return render_template(
        "relatorios_avancados.html",
        todos_status=todos_status,
        todas_ras=todas_ras,
        todas_demandas=todas_demandas,
        todas_diretorias=todas_diretorias,
        todos_departamentos=todos_departamentos,
        resultados=tabela_resultados,
        total_resultados=total_resultados,
        limit=limit,
        total_ras=total_ras,
        total_demandas=total_demandas,
        total_atendidos=total_atendidos,
        taxa_atendimento=taxa_atendimento,
        diretoria_destaque=diretoria_destaque,
        diretoria_destaque_qtd=diretoria_destaque_qtd,
        diretoria_destaque_pct=diretoria_destaque_pct,
        status_predominante=status_predominante,
        status_predominante_qtd=status_predominante_qtd,
        status_predominante_pct=status_predominante_pct,
        status_badge_class=status_badge_class,
        ra_destaque=ra_destaque,
        ra_destaque_qtd=ra_destaque_qtd,
        ra_destaque_pct=ra_destaque_pct,
        demandas_mapeadas=demandas_mapeadas,
        dados_relatorio=dados
    )


# ==========================================================
# 📄 EXPORTAÇÃO CSV / XLSX
# ==========================================================
@relatorios_bp.route('/exportar')
@login_required
def exportar_relatorios():
    status_sel = request.args.get("status")
    ra_sel = request.args.get("ra")
    diretoria_sel = request.args.get("diretoria")
    departamento_sel = request.args.get("departamento")
    demanda_sel = request.args.get("servico")
    inicio = request.args.get("inicio")
    fim = request.args.get("fim")

    query = (
        db.session.query(
            Movimentacao,
            Usuario,
            EntradaProcesso,
            Processo,
            Demanda,
            Departamento,
            Diretoria
        )
        .outerjoin(Usuario, Movimentacao.id_usuario == Usuario.id_usuario)
        .outerjoin(EntradaProcesso, Movimentacao.id_entrada == EntradaProcesso.id_entrada)
        .outerjoin(Processo, EntradaProcesso.id_processo == Processo.id_processo)
        .outerjoin(Demanda, EntradaProcesso.id_demanda == Demanda.id_demanda)
        .outerjoin(Departamento, Demanda.id_departamento == Departamento.id_departamento)
        .outerjoin(Diretoria, Departamento.id_diretoria == Diretoria.id_diretoria)
    )

    if diretoria_sel:
        query = query.filter(
            db.or_(
                Diretoria.descricao_exibicao.ilike(f"%{diretoria_sel}%"),
                Processo.diretoria_destino.ilike(f"%{diretoria_sel}%")
            )
        )
    if departamento_sel:
        query = query.filter(Departamento.nome == departamento_sel)
    if demanda_sel:
        query = query.filter(Demanda.descricao == demanda_sel)
    if ra_sel:
        query = query.filter(EntradaProcesso.ra_origem == ra_sel)
    if status_sel:
        query = query.filter(Movimentacao.novo_status == status_sel)
    if inicio and fim:
        try:
            dt_inicio = datetime.strptime(inicio, "%Y-%m-%d")
            dt_fim = datetime.strptime(fim, "%Y-%m-%d")
            query = query.filter(Movimentacao.data.between(dt_inicio, dt_fim))
        except ValueError:
            pass

    resultados = query.all()

    dados = []
    for mov, user, entrada, processo, demanda, departamento, diretoria in resultados:
        if diretoria and diretoria.descricao_exibicao:
            dir_nome = diretoria.descricao_exibicao
        elif processo and processo.diretoria_destino:
            dir_nome = processo.diretoria_destino
        else:
            dir_nome = "Não informado"

        dados.append({
            "Data": mov.data.strftime("%d/%m/%Y %H:%M") if mov and mov.data else "—",
            "Número do Processo": processo.numero_processo if processo else "—",
            "RA": entrada.ra_origem if entrada else "—",
            "Status": mov.novo_status if mov else "—",
            "Diretoria": dir_nome,
            "Departamento": departamento.nome if departamento else "Não informado",
            "Serviço": demanda.descricao if demanda else "—",
            "Responsável": user.usuario if user else "—",
            "Observação": mov.observacao or ""
        })

    df = pd.DataFrame(dados)

    formato = request.args.get("formato", "csv").lower()
    nome = f"Relatorio_Avancado_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    if formato == "xlsx":
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Relatório")
        output.seek(0)
        return send_file(output, as_attachment=True, download_name=f"{nome}.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    csv = df.to_csv(index=False, sep=";", encoding="utf-8-sig")
    response = make_response(csv)
    response.headers["Content-Disposition"] = f"attachment; filename={nome}.csv"
    response.headers["Content-Type"] = "text/csv"
    return response
