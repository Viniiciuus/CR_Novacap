"""
API RESTful Genérica para Abertura e Consulta de Chamados/Processos
"""
from flask import jsonify, request
from app.api import api_bp
from app.ext import db
from app.models.modelos import Processo, EntradaProcesso, Usuario
from datetime import datetime

@api_bp.route('/v1/chamados', methods=['GET'])
def listar_chamados():
    """Retorna a lista de chamados/processos cadastrados."""
    processos = Processo.query.all()
    resultado = []
    for p in processos:
        resultado.append({
            'id': p.id_processo,
            'numero_processo': p.numero_processo,
            'status_atual': p.status_atual,
            'diretoria_destino': p.diretoria_destino,
            'observacoes': p.observacoes
        })
    return jsonify({'sucesso': True, 'chamados': resultado})

@api_bp.route('/v1/chamados', methods=['POST'])
def criar_chamado():
    """Cria um novo chamado via API JSON."""
    dados = request.get_json() or {}
    
    numero_processo = dados.get('numero_processo')
    diretoria_destino = dados.get('diretoria_destino')
    observacoes = dados.get('observacoes', '')

    if not numero_processo or not diretoria_destino:
        return jsonify({'sucesso': False, 'erro': 'Campos numero_processo e diretoria_destino sao obrigatorios'}), 400

    processo_existente = Processo.query.filter_by(numero_processo=numero_processo).first()
    if processo_existente:
        return jsonify({'sucesso': False, 'erro': 'Numero de processo ja cadastrado'}), 409

    novo_processo = Processo(
        numero_processo=numero_processo,
        status_atual='Novo',
        diretoria_destino=diretoria_destino,
        observacoes=observacoes
    )
    db.session.add(novo_processo)
    db.session.commit()

    return jsonify({
        'sucesso': True,
        'mensagem': 'Chamado criado com sucesso',
        'id_processo': novo_processo.id_processo,
        'numero_processo': novo_processo.numero_processo
    }), 201
