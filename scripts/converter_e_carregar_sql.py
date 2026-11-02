import sqlite3
import re
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app

app = create_app()

SQL_FILE = os.path.join(os.path.dirname(__file__), '..', 'BD_novacap_info.sql')
DB_FILE = os.path.join(os.path.dirname(__file__), '..', 'instance', 'cr.db')

def carregar_dump_mysql():
    print(f"Lendo {SQL_FILE}...")
    with open(SQL_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        sql = f.read()

    # Remove comandos especificos do MySQL
    sql = re.sub(r'/\*!.*?\*/;', '', sql, flags=re.DOTALL)
    sql = re.sub(r'/\*!.*?\*/', '', sql, flags=re.DOTALL)
    sql = re.sub(r'LOCK TABLES `?\w+`? WRITE;', '', sql)
    sql = re.sub(r'UNLOCK TABLES;', '', sql)
    sql = re.sub(r'ENGINE=InnoDB.*?;', ';', sql)
    sql = re.sub(r'AUTO_INCREMENT=\d+', '', sql)
    sql = re.sub(r'CHARACTER SET \w+', '', sql)
    sql = re.sub(r'COLLATE \w+', '', sql)
    sql = re.sub(r'GENERATED ALWAYS AS \(.*?\) STORED', '', sql)

    # Garante a pasta instance
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

    # Se a base ja existe, faz backup/remove para carregar limpa
    if os.path.exists(DB_FILE):
        try:
            os.remove(DB_FILE)
            print("Base antiga removida para carga limpa.")
        except Exception as e:
            print(f"Aviso ao remover db antiga: {e}")

    # Cria todas as tabelas via Flask SQLAlchemy primeiro
    with app.app_context():
        from app.ext import db
        db.create_all()
        print("Tabelas padrao do Flask criadas.")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = OFF;")

    # Extrai cada INSERT INTO
    inserts = re.findall(r"(INSERT INTO `?(\w+)`?\s*(?:\([^)]+\))?\s*VALUES\s*\(.*?\);)", sql, re.DOTALL | re.IGNORECASE)

    # Mapeamento de colunas especificas de cada tabela no MySQL Dump
    dump_columns = {
        'alertas': ['id_alerta', 'id_usuario', 'tipo_alerta', 'numero_processo', 'id_entrada', 'mensagem', 'data_alerta', 'respondido', 'data_resposta', 'forma_resposta'],
        'demandas': ['id_demanda', 'descricao', 'id_diretoria', 'id_departamento', 'ativo', 'versao_catalogo', 'substitui_id_demanda'],
        'departamentos': ['id_departamento', 'nome', 'id_diretoria'],
        'diretorias': ['id_diretoria', 'nome_completo', 'sigla', 'tipo', 'ativo', 'ordem_exibicao'],
        'entradas_processo': ['id_entrada', 'id_processo', 'data_criacao_ra', 'data_entrada_novacap', 'data_documento', 'ra_origem', 'id_demanda', 'usuario_responsavel', 'status_inicial'],
        'logs_usuarios': ['id_log', 'id_usuario', 'acao', 'tabela_afetada', 'id_referencia', 'descricao_detalhada', 'ip_origem', 'data_hora'],
        'movimentacoes': ['id_movimentacao', 'id_entrada', 'id_usuario', 'novo_status', 'data', 'observacao'],
        'processos': ['id_processo', 'numero_processo', 'status_atual', 'observacoes', 'diretoria_destino'],
        'protocolo_atendimento': ['id_protocolo', 'numero_protocolo', 'data_atendimento', 'canal_atendimento', 'id_ra_origem', 'solicitante_nome', 'solicitante_cpf_cnpj', 'solicitante_telefone', 'solicitante_email', 'id_demanda', 'detalhamento_solicitacao', 'bairro_localidade', 'endereco_completo', 'ponto_referencia', 'id_diretoria_responsavel', 'id_departamento_responsavel', 'status_atual', 'prazo_resposta_dias', 'data_limite_resposta', 'usuario_registro_id', 'dados_customizados', 'criado_em', 'atualizado_em'],
        'regioes_administrativas': ['id_unidade', 'codigo', 'nome_unidade', 'descricao'],
        'status': ['id_status', 'descricao', 'ordem_exibicao', 'finaliza_processo'],
        'tipos_demanda': ['id_tipo', 'descricao'],
        'usuarios': ['id_usuario', 'nome', 'usuario', 'email', 'senha_hash', 'aprovado', 'bloqueado', 'is_admin']
    }

    # Verifica quais colunas reais existem nas tabelas do SQLite
    table_real_cols = {}
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cursor.fetchall()]
    for t in tables:
        cursor.execute(f"PRAGMA table_info('{t}');")
        table_real_cols[t] = [row[1] for row in cursor.fetchall()]

    # Adiciona colunas que possam faltar no SQLite para compatibilidade total com o dump
    colunas_para_adicionar = [
        ('demandas', 'ativo', 'INTEGER DEFAULT 1'),
        ('demandas', 'versao_catalogo', 'TEXT DEFAULT "V1"'),
        ('demandas', 'substitui_id_demanda', 'INTEGER'),
        ('diretorias', 'tipo', 'TEXT DEFAULT "INTERNA"'),
        ('diretorias', 'ativo', 'INTEGER DEFAULT 1'),
        ('diretorias', 'ordem_exibicao', 'INTEGER DEFAULT 0')
    ]
    for tbl, col, col_type in colunas_para_adicionar:
        if tbl in table_real_cols and col not in table_real_cols[tbl]:
            try:
                cursor.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} {col_type};")
                table_real_cols[tbl].append(col)
                print(f"Coluna '{col}' adicionada a tabela '{tbl}'.")
            except Exception as e:
                print(f"Aviso ao alterar {tbl}: {e}")

    # Processa os INSERTS do dump
    sucesso = 0
    erros = 0

    for stmt_raw, table_name in inserts:
        target_table = table_name
        if target_table == 'regioes_administrativas' and 'unidades_solicitantes' in table_real_cols:
            target_table = 'unidades_solicitantes'

        if target_table not in table_real_cols:
            print(f"Tabela '{target_table}' nao encontrada no SQLite. Ignorando...")
            continue

        cols = dump_columns.get(table_name, [])
        if not cols:
            continue

        # Injeta o nome explicito das colunas no INSERT INTO
        # Exemplo: INSERT INTO `demandas` VALUES (...) -> INSERT INTO `demandas` (`col1`, `col2`...) VALUES (...)
        match_values = re.search(r"VALUES\s*(.*);", stmt_raw, re.DOTALL | re.IGNORECASE)
        if not match_values:
            continue

        values_part = match_values.group(1)
        cols_str = ", ".join([f"`{c}`" for c in cols])
        new_stmt = f"INSERT INTO `{target_table}` ({cols_str}) VALUES {values_part};"

        # Limpeza de caracteres e datas
        # Trata aspas escapadas no MySQL: \' e \"
        new_stmt = re.sub(r"(?<!\\)\\'", "''", new_stmt)
        new_stmt = new_stmt.replace('\\"', '"').replace("\\\\", "\\")
        new_stmt = re.sub(r"'00(\d\d)-", r"'20\1-", new_stmt)

        try:
            cursor.execute(new_stmt)
            sucesso += 1
        except Exception as e:
            # Se falhou, tenta executar os registros individualmente em sub-instruções
            sub_matches = re.findall(r"\((.*?)\)(?:,|\s*;)", values_part, re.DOTALL)
            sub_sucesso = 0
            for sub_val in sub_matches:
                sub_stmt = f"INSERT INTO `{target_table}` ({cols_str}) VALUES ({sub_val});"
                sub_stmt = re.sub(r"(?<!\\)\\'", "''", sub_stmt).replace('\\"', '"').replace("\\\\", "\\")
                sub_stmt = re.sub(r"'00(\d\d)-", r"'20\1-", sub_stmt)
                try:
                    cursor.execute(sub_stmt)
                    sub_sucesso += 1
                except Exception:
                    pass
            if sub_sucesso > 0:
                print(f"Sucesso parcial em '{target_table}': {sub_sucesso} linhas inseridas individualmente.")
                sucesso += 1
            else:
                err_msg = str(e).encode('ascii', errors='replace').decode('ascii')
                print(f"Erro em '{target_table}': {err_msg[:120]}")
                erros += 1

    conn.commit()
    conn.close()
    print(f"\nCarga de dados concluida! Inserts executados com sucesso: {sucesso}. Falhas: {erros}")

if __name__ == '__main__':
    carregar_dump_mysql()
