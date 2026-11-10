import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.ext import db
from app.models.modelos import Usuario

app = create_app()

with app.app_context():
    ativos = Usuario.query.filter_by(bloqueado=False).all()
    
    if not ativos:
        print("✅ Nenhum usuário ativo disponível para bloqueio.")
    else:
        print("Usuários ativos:\n")
        for usuario in ativos:
            print(f"ID: {usuario.id_usuario} | Nome: {usuario.nome} | Usuário: {usuario.usuario} | Email: {usuario.email}")
            escolha = input("Deseja bloquear este usuário? (s/n): ").strip().lower()
            if escolha == 's':
                usuario.bloqueado = True
                print(f"⛔ Usuário {usuario.usuario} bloqueado.")
            else:
                print(f"⏭️ Usuário {usuario.usuario} mantido ativo.")
        db.session.commit()
        print("\n✔️ Processo de bloqueio concluído.")
