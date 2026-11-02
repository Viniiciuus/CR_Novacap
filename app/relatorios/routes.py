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
        query = query.filter(Diretoria.descricao_exibicao.ilike(f"%{diretoria_sel}%"))  # ILIKE + PARCIAL

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
    total_atendidos = 0

    for mov, user, entrada, processo, demanda, departamento, diretoria in resultados:
        dt_str = mov.data.strftime("%d/%m/%Y %H:%M") if mov.data else "—"
        dt_iso = mov.data.strftime("%Y-%m-%d") if mov.data else ""
        mes_ano = mov.data.strftime("%m/%Y") if mov.data else ""

        st = mov.novo_status if mov and mov.novo_status else "Não informado"
        dir_nome = diretoria.descricao_exibicao if diretoria and diretoria.descricao_exibicao else "Não informado"

        dados.append({
            "Data": dt_str,
            "DataISO": dt_iso,
            "MesAno": mes_ano,
            "Número do Processo": processo.numero_processo if processo else "—",
            "RA": entrada.ra_origem if entrada else "—",
            "Status": st,
            "Diretoria": dir_nome,
            "Departamento": departamento.nome if departamento else "Não informado",
            "Serviço": demanda.descricao if demanda else "—",
            "Responsável": user.usuario if user else "—",
            "Observação": mov.observacao if mov else ""
        })

        if st in ["Atendido", "Concluído", "Deferido"]:
            total_atendidos += 1

        status_count[st] = status_count.get(st, 0) + 1
        diretoria_count[dir_nome] = diretoria_count.get(dir_nome, 0) + 1

        if entrada and entrada.ra_origem:
            ras_distintas.add(entrada.ra_origem)
        if demanda and demanda.descricao:
            demandas_distintas.add(demanda.descricao)

    df = pd.DataFrame(dados)
    dados_relatorio = df.to_dict(orient="records")  # PASSA DIRETO PRO TEMPLATE

    total_resultados = len(df)
    total_ras = len(ras_distintas)
    total_demandas = len(demandas_distintas)

    taxa_atendimento = round((total_atendidos / total_resultados * 100), 1) if total_resultados > 0 else 0.0

    # Diretoria e Status Predominante
    diretoria_destaque = max(diretoria_count, key=diretoria_count.get) if diretoria_count else "—"
    status_predominante = max(status_count, key=status_count.get) if status_count else "—"

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
    print(f"Diretoria Destaque: {diretoria_destaque}")
    print(f"Status Predominante: {status_predominante}")
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
        taxa_atendimento=taxa_atendimento,
        diretoria_destaque=diretoria_destaque,
        status_predominante=status_predominante,
        demandas_mapeadas=demandas_mapeadas,
        dados_relatorio=dados_relatorio
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
        query = query.filter(Diretoria.descricao_exibicao.ilike(f"%{diretoria_sel}%"))
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
        dados.append({
            "Data": mov.data.strftime("%d/%m/%Y %H:%M") if mov.data else "—",
            "Número do Processo": processo.numero_processo if processo else "—",
            "RA": entrada.ra_origem if entrada else "—",
            "Status": mov.novo_status if mov else "—",
            "Diretoria": diretoria.descricao_exibicao if diretoria else "Não informado",
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
