import re
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
from app.ext import db
from sqlalchemy import text

app = create_app()

SQL_FILE = os.path.join(os.path.dirname(__file__), '..', 'BD_novacap_info.sql')

def importar_sql():
    print(f"Lendo o arquivo SQL: {SQL_FILE}")
    with open(SQL_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        sql_content = f.read()

    with app.app_context():
        # Cria todas as tabelas caso nao existam
        db.create_all()
        print("Tabelas preparadas no banco de dados!")

        inspector = db.inspect(db.engine)
        tables_in_db = set(inspector.get_table_names())
        print(f"Tabelas ativas: {sorted(tables_in_db)}")

        insert_statements = re.findall(r"(INSERT INTO `?(\w+)`?[^;]+;)", sql_content, re.DOTALL | re.IGNORECASE)

        sucesso = 0
        erros = 0

        for stmt, table_name in insert_statements:
            target_table = table_name
            if target_table not in tables_in_db:
                if target_table == 'regioes_administrativas' and 'unidades_solicitantes' in tables_in_db:
                    target_table = 'unidades_solicitantes'
                    stmt = stmt.replace('`regioes_administrativas`', '`unidades_solicitantes`')
                else:
                    print(f"Aviso: Tabela '{table_name}' nao existe. Ignorando...")
                    continue

            # Ajusta delimitadores de string para SQL padrão
            stmt_clean = stmt.replace('\\"', '"').replace("\\'", "''")
            # Corrige datas malformadas como '0025-08-22' -> '2025-08-22'
            stmt_clean = re.sub(r"'00(\d\d)-", r"'20\1-", stmt_clean)

            try:
                with db.engine.begin() as connection:
                    connection.execute(text(stmt_clean))
                sucesso += 1
            except Exception as e:
                err_str = str(e).encode('ascii', errors='replace').decode('ascii')
                print(f"Erro ao inserir na tabela '{target_table}': {err_str[:120]}")
                erros += 1

        print(f"\nImportacao concluida! {sucesso} blocos inseridos com sucesso. Erros: {erros}")

if __name__ == '__main__':
    importar_sql()
