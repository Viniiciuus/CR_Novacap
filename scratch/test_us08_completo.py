import re
import sys
import os
import unittest
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
from app.ext import db
from app.models.modelos import Usuario, Processo, EntradaProcesso, Movimentacao, AuditoriaProcesso

class TestUS08Auditoria(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def login_client(self, client, usuario_id=2):
        with client.session_transaction() as sess:
            u = db.session.get(Usuario, usuario_id)
            sess['_user_id'] = str(u.id_usuario)
            sess['is_admin'] = u.is_admin
            sess['usuario'] = u.usuario

    def test_criterio1_cronologico_e_ordenacao(self):
        """Critério 1: Exibição cronológica de todas as alterações sofridas pelo processo."""
        with self.app.app_context():
            self.login_client(self.client)

            # Testar ordem desc (padrão)
            res_desc = self.client.get('/processos/detalhes/1?ordem=desc')
            self.assertEqual(res_desc.status_code, 200)
            html_desc = res_desc.get_data(as_text=True)
            self.assertIn("Trilha de Auditoria e Histórico de Alterações", html_desc)
            self.assertIn("Mais Recentes no Topo", html_desc)

            # Testar ordem asc (cronológica crescente)
            res_asc = self.client.get('/processos/detalhes/1?ordem=asc')
            self.assertEqual(res_asc.status_code, 200)
            html_asc = res_asc.get_data(as_text=True)
            self.assertIn("Cronológica (Crescente)", html_asc)

    def test_criterio2_detalhamento_antes_depois_e_metadados(self):
        """Critério 2: Detalhamento contendo data/hora, responsável e valores antes/depois."""
        with self.app.app_context():
            self.login_client(self.client)

            # Obter token csrf da tela de alteração
            res_form = self.client.get('/processos/alterar/1')
            match = re.search(r'name="csrf_token" value="([^"]+)"', res_form.get_data(as_text=True))
            token = match.group(1) if match else ''

            p = db.session.get(Processo, 1)
            st_antigo = p.status_atual
            novo_st = "Em análise técnica pela Diretoria" if st_antigo != "Em análise técnica pela Diretoria" else "Atendido"

            post_data = {
                'csrf_token': token,
                'novo_status': novo_st,
                'observacao': 'Teste automatizado de verificação do Critério 2 da US08',
                'data_movimentacao': datetime.now().strftime('%Y-%m-%d'),
                'responsavel_tecnico': '2'
            }

            res_post = self.client.post('/processos/alterar/1', data=post_data, follow_redirects=True)
            self.assertEqual(res_post.status_code, 200)

            # Verificar no banco se os metadados de auditoria foram persistidos para status
            aud_status = AuditoriaProcesso.query.filter_by(id_processo=1, campo_alterado='Status Atual').order_by(AuditoriaProcesso.id_auditoria.desc()).first()
            self.assertIsNotNone(aud_status)
            self.assertEqual(aud_status.valor_novo, novo_st)
            self.assertEqual(aud_status.valor_anterior, st_antigo)
            self.assertIsNotNone(aud_status.data_hora)
            self.assertIsNotNone(aud_status.usuario)

            # Verificar auditoria de observação / despacho
            aud_obs = AuditoriaProcesso.query.filter_by(id_processo=1, campo_alterado='Despacho / Observação').order_by(AuditoriaProcesso.id_auditoria.desc()).first()
            self.assertIsNotNone(aud_obs)
            self.assertIn("Teste automatizado", aud_obs.justificativa)


            # Verificar na página de detalhes HTML
            res_det = self.client.get('/processos/detalhes/1')
            html_det = res_det.get_data(as_text=True)
            self.assertIn("Valor Anterior", html_det)
            self.assertIn("Valor Novo", html_det)
            self.assertIn(novo_st, html_det)

    def test_criterio3_modo_somente_leitura(self):
        """Critério 3: Visualização em modo somente leitura acessível a partir do detalhamento do processo."""
        with self.app.app_context():
            self.login_client(self.client)
            res = self.client.get('/processos/detalhes/1')
            self.assertEqual(res.status_code, 200)
            html = res.get_data(as_text=True)
            self.assertIn("MODO SOMENTE LEITURA", html)
            self.assertIn("Visualização Protegida", html)
            # Confirma que não há tags <form method="post" com inputs editáveis para alterar o processo nesta tela
            self.assertNotIn('<input type="text" id="status_atual" name="status_atual"', html)

    def test_exportacoes_auditoria_csv_json_pdf(self):
        """Verifica exportação da trilha de auditoria em JSON, CSV e inclusão no PDF institucional."""
        with self.app.app_context():
            self.login_client(self.client)

            # JSON API
            res_json = self.client.get('/processos/api/auditoria/1')
            self.assertEqual(res_json.status_code, 200)
            data = res_json.get_json()
            self.assertIsInstance(data, list)
            self.assertGreater(len(data), 0)
            self.assertIn('campo_alterado', data[0])
            self.assertIn('valor_anterior', data[0])
            self.assertIn('valor_novo', data[0])

            # CSV
            res_csv = self.client.get('/processos/auditoria/csv/1')
            self.assertEqual(res_csv.status_code, 200)
            self.assertIn("text/csv", res_csv.headers.get("Content-Type", ""))
            csv_text = res_csv.get_data(as_text=True)
            self.assertIn("ID Auditoria", csv_text)
            self.assertIn("Valor Anterior", csv_text)
            self.assertIn("Valor Novo", csv_text)

            # PDF com seção de auditoria
            res_pdf = self.client.get('/processos/exportar-processo/1')
            self.assertEqual(res_pdf.status_code, 200)
            self.assertIn("application/pdf", res_pdf.headers.get("Content-Type", ""))
            self.assertGreater(len(res_pdf.data), 1000)

if __name__ == '__main__':
    unittest.main()
