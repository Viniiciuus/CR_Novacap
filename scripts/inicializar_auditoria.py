# scripts/inicializar_auditoria.py
"""
Script de inicialização da tabela de auditoria (US08)
e povoamento do histórico inicial a partir das movimentações existentes.
"""
import sys
import os
from datetime import datetime

# Garante path para importação da aplicação
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.ext import db
from app.models.modelos import Processo, EntradaProcesso, Movimentacao, AuditoriaProcesso, Usuario

def inicializar_auditoria():
    app = create_app()
    with app.app_context():
        print("[INFO] Criando tabela de auditoria se nao existir...")
        db.create_all()
        
        # Verifica quantos registros de auditoria ja existem
        total_auditorias = AuditoriaProcesso.query.count()
        print(f"[INFO] Registros atuais na trilha de auditoria: {total_auditorias}")

        processos = Processo.query.all()
        print(f"[INFO] Total de processos no sistema: {len(processos)}")

        # Identificar processos que ainda nao possuem nenhum registro de auditoria
        processos_com_auditoria = set(
            r[0] for r in db.session.query(AuditoriaProcesso.id_processo).distinct().all()
        )
        processos_sem_auditoria = [p for p in processos if p.id_processo not in processos_com_auditoria]
        print(f"[INFO] Processos que necessitam de historico de auditoria: {len(processos_sem_auditoria)}")

        if processos_sem_auditoria:
            registros_para_inserir = []
            
            for p in processos_sem_auditoria:
                entradas = EntradaProcesso.query.filter_by(id_processo=p.id_processo).all()
                
                if entradas:
                    for entrada in entradas:
                        movs = Movimentacao.query.filter_by(id_entrada=entrada.id_entrada).order_by(
                            Movimentacao.data.asc(), Movimentacao.id_movimentacao.asc()
                        ).all()

                        if movs:
                            status_anterior = "---"
                            for idx, m in enumerate(movs):
                                if idx == 0:
                                    acao = "Cadastro Inicial"
                                    campo = "Criação do Processo"
                                    val_ant = "---"
                                    val_novo = f"Status Inicial: {m.novo_status} | Destino: {p.diretoria_destino or 'Não informado'}"
                                    justificativa = m.observacao or "Cadastro e autuação inicial do processo no sistema."
                                else:
                                    acao = "Alteração de Status"
                                    campo = "Status Atual"
                                    val_ant = status_anterior
                                    val_novo = m.novo_status
                                    justificativa = m.observacao or "Atualização de tramitação e despacho do processo."

                                dt = m.data if m.data else (entrada.data_entrada_novacap or datetime(2025, 1, 1))
                                auditoria = AuditoriaProcesso(
                                    id_processo=p.id_processo,
                                    id_usuario=m.id_usuario or entrada.usuario_responsavel,
                                    campo_alterado=campo,
                                    valor_anterior=val_ant,
                                    valor_novo=val_novo,
                                    acao=acao,
                                    justificativa=justificativa,
                                    data_hora=dt,
                                    ip_origem="127.0.0.1 (Migração Histórica)"
                                )
                                registros_para_inserir.append(auditoria)
                                status_anterior = m.novo_status
                        else:
                            # Entrada sem movimentações explícitas - cria auditoria de cadastro inicial
                            dt = entrada.data_entrada_novacap or entrada.data_documento or datetime(2025, 1, 1)
                            auditoria = AuditoriaProcesso(
                                id_processo=p.id_processo,
                                id_usuario=entrada.usuario_responsavel or 1,
                                campo_alterado="Criação do Processo",
                                valor_anterior="---",
                                valor_novo=f"Status: {entrada.status_inicial or p.status_atual or 'Não informado'} | Destino: {p.diretoria_destino or 'Não informado'}",
                                acao="Cadastro Inicial",
                                justificativa=p.observacoes or "Autuação e registro cadastral do processo na base.",
                                data_hora=dt,
                                ip_origem="127.0.0.1 (Migração Histórica)"
                            )
                            registros_para_inserir.append(auditoria)
                else:
                    # Processo sem entrada vinculada
                    auditoria = AuditoriaProcesso(
                        id_processo=p.id_processo,
                        id_usuario=1,
                        campo_alterado="Criação do Processo",
                        valor_anterior="---",
                        valor_novo=f"Status: {p.status_atual or 'Não informado'} | Destino: {p.diretoria_destino or 'Não informado'}",
                        acao="Cadastro Inicial",
                        justificativa=p.observacoes or "Autuação direta de processo.",
                        data_hora=datetime(2025, 1, 1),
                        ip_origem="127.0.0.1 (Migração Histórica)"
                    )
                    registros_para_inserir.append(auditoria)

            if registros_para_inserir:
                print(f"[INFO] Inserindo {len(registros_para_inserir)} novos registros na trilha de auditoria...")
                db.session.bulk_save_objects(registros_para_inserir)
                db.session.commit()
                print("[SUCESSO] Todos os processos agora possuem histórico de auditoria completo!")
        else:
            print("[INFO] Todos os processos já possuem trilha de auditoria cadastrada.")

if __name__ == '__main__':
    inicializar_auditoria()
