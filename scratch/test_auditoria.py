import re
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
from app.ext import db
from app.models.modelos import Usuario, Processo, AuditoriaProcesso

app = create_app()
with app.app_context():
    with app.test_client() as client:
        with client.session_transaction() as sess:
            u = db.session.get(Usuario, 2)
            sess['_user_id'] = str(u.id_usuario)
            sess['is_admin'] = u.is_admin
            sess['usuario'] = u.usuario

        res = client.get('/processos/alterar/1')
        match = re.search(r'name="csrf_token" value="([^"]+)"', res.get_data(as_text=True))
        token = match.group(1) if match else ''

        p_before = db.session.get(Processo, 1)
        st_before = p_before.status_atual
        print('Status anterior do processo 1:', st_before)

        novo_st = 'Atendido' if st_before != 'Atendido' else 'Devolvido à RA de origem – adequação de requisitos'
        post_data = {
            'csrf_token': token,
            'novo_status': novo_st,
            'observacao': 'Teste de auditoria automatizado US08 - Validação de Conformidade',
            'data_movimentacao': '2026-10-26',
            'responsavel_tecnico': '2'
        }
        res_post = client.post('/processos/alterar/1', data=post_data, follow_redirects=True)
        print('Status code pós-alteração:', res_post.status_code)
        print('Redirecionou para detalhes:', '/processos/detalhes/1' in res_post.request.path)

        # Checar auditoria gravada
        ult_aud = AuditoriaProcesso.query.filter_by(id_processo=1).order_by(AuditoriaProcesso.id_auditoria.desc()).all()
        print(f'Total de registros de auditoria para processo 1: {len(ult_aud)}')
        for a in ult_aud[:4]:
            print(f'  - Ação: {a.acao} | Campo: {a.campo_alterado} | De: [{a.valor_anterior}] -> Para: [{a.valor_novo}] | Autor: {a.usuario.nome if a.usuario else "Sistema"} | Data: {a.data_hora}')
