import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
from app.ext import db
from app.models.modelos import Usuario

class TestUS02VisualizacoesGraficas(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def login_client(self, client):
        with client.session_transaction() as sess:
            u = Usuario.query.first()
            sess['_user_id'] = str(u.id_usuario)
            sess['is_admin'] = u.is_admin
            sess['usuario'] = u.usuario

    def test_criterio1_graficos_intuitivos_legendas_rotulos(self):
        """
        Critério 1: Apresentação de gráficos intuitivos com legendas e rótulos claros.
        Verifica presença de Plotly, containers de gráficos e definições de rótulos e legendas.
        """
        with self.app.app_context():
            self.login_client(self.client)
            res = self.client.get('/relatorios/avancados')
            self.assertEqual(res.status_code, 200)
            html = res.get_data(as_text=True)

            # Biblioteca gráfica Plotly
            self.assertIn('plotly', html.lower())

            # Containers de gráficos
            self.assertIn('id="grafico_temporal"', html)
            self.assertIn('id="grafico_status"', html)
            self.assertIn('id="grafico_ra"', html)
            self.assertIn('id="grafico_diretoria"', html)
            self.assertIn('id="grafico_servico"', html)

            # Rótulos claros e legendas intuitivas configurados no script
            self.assertIn('textposition', html)
            self.assertIn('hovertemplate', html)
            self.assertIn('paletaCoresStatus', html)
            self.assertIn('showlegend', html)

    def test_criterio2_alternancia_periodos_e_categorias(self):
        """
        Critério 2: Possibilidade de alternar a exibição de dados por períodos ou categorias.
        Verifica a disponibilização de controles interativos para alternar visões.
        """
        with self.app.app_context():
            self.login_client(self.client)
            res = self.client.get('/relatorios/avancados')
            self.assertEqual(res.status_code, 200)
            html = res.get_data(as_text=True)

            # Barra de controle interativa
            self.assertIn('chart-controls-wrapper', html)

            # Alternância de categorias (Status, RAs, Diretoria, Demandas, Período, Todas)
            self.assertIn('id="category-pills"', html)
            self.assertIn('data-category="todas"', html)
            self.assertIn('data-category="status"', html)
            self.assertIn('data-category="ra"', html)
            self.assertIn('data-category="diretoria"', html)
            self.assertIn('data-category="servico"', html)
            self.assertIn('data-category="periodo"', html)

            # Alternância de agrupamento temporal (Períodos: Mês a Mês vs Ano a Ano)
            self.assertIn('id="period-pills"', html)
            self.assertIn('data-period="mes"', html)
            self.assertIn('data-period="ano"', html)

            # Alternância de tipo de gráfico em cada card (Barras vs Rosca / Linha)
            self.assertIn('chart-type-btn', html)
            self.assertIn('data-chart-type="bar"', html)
            self.assertIn('data-chart-type="pie"', html)
            self.assertIn('data-chart-type="line"', html)

    def test_criterio3_indicadores_visuais_dados_consolidados(self):
        """
        Critério 3: Inclusão de indicadores visuais de destaque para dados consolidados.
        Verifica os KPI cards com totalizações, taxas de atendimento, barra de progresso e destaques.
        """
        with self.app.app_context():
            self.login_client(self.client)
            res = self.client.get('/relatorios/avancados')
            self.assertEqual(res.status_code, 200)
            html = res.get_data(as_text=True)

            # Grid de KPIs consolidados
            self.assertIn('kpi-grid', html)
            self.assertIn('kpi-card', html)

            # Indicadores obrigatórios
            self.assertIn('Total de Processos', html)
            self.assertIn('Taxa de Conclusão / Atendimento', html)
            self.assertIn('kpi-progress-bar', html)
            self.assertIn('kpi-progress-fill', html)
            self.assertIn('Status Predominante', html)
            self.assertIn('Diretoria Mais Demandada', html)
            self.assertIn('RA com Maior Volume', html)

            # Recálculo coerente com filtros aplicados
            res_filtro = self.client.get('/relatorios/avancados?diretoria=Cidades')
            self.assertEqual(res_filtro.status_code, 200)
            html_filtro = res_filtro.get_data(as_text=True)
            self.assertIn('Diretoria das Cidades', html_filtro)

if __name__ == '__main__':
    unittest.main()

