# app/models/modelos.py
"""
Modelos do sistema CR-NOVACAP.
Contém entidades de usuários, processos, protocolo, status, demandas, logs e alertas.
Atualizado para incluir a hierarquia Diretoria → Departamento → Demanda (corrigido).
"""

from datetime import datetime
from flask_login import UserMixin
from app.ext import db


# ==========================================================
# 🌐 TENANTS (MULTI-TENANCY / EMPRESAS)
# ==========================================================
class Tenant(db.Model):
    __tablename__ = 'tenants'

    id_tenant = db.Column(db.Integer, primary_key=True)
    nome_empresa = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    logo_url = db.Column(db.String(255))
    cor_primaria = db.Column(db.String(7), default="#0d6efd")
    cor_secundaria = db.Column(db.String(7), default="#6c757d")
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Tenant {self.nome_empresa}>"


# ==========================================================
# 👤 USUÁRIOS DO SISTEMA
# ==========================================================
class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'

    id_usuario = db.Column(db.Integer, primary_key=True)
    id_tenant = db.Column(db.Integer, db.ForeignKey('tenants.id_tenant'), nullable=True)
    nome = db.Column(db.String(100), nullable=False)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column(db.Text, nullable=False)
    aprovado = db.Column(db.Boolean, default=False)
    bloqueado = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)

    tenant = db.relationship('Tenant', backref='usuarios', lazy=True)

    def get_id(self):
        return str(self.id_usuario)


# ==========================================================
# 🧭 DIRETORIAS / SETORES ORGANIZACIONAIS
# ==========================================================
class Diretoria(db.Model):
    __tablename__ = 'diretorias'

    id_diretoria = db.Column(db.Integer, primary_key=True)
    id_tenant = db.Column(db.Integer, db.ForeignKey('tenants.id_tenant'), nullable=True)
    nome_completo = db.Column(db.String(100), nullable=False, unique=True)
    sigla = db.Column(db.String(10))
    descricao_exibicao = db.Column(db.String(120))

    tenant = db.relationship('Tenant', backref='setores', lazy=True)

    # 🔁 Relação 1:N com Departamentos
    departamentos = db.relationship(
        'Departamento',
        backref='diretoria',
        lazy=True,
        cascade="all, delete"
    )

    def __repr__(self):
        return f"<Diretoria {self.sigla or ''} - {self.nome_completo}>"


# Alias genérico
SetorOrganizacional = Diretoria


# ==========================================================
# 🏢 DEPARTAMENTOS / SUB-SETORES
# ==========================================================
class Departamento(db.Model):
    __tablename__ = 'departamentos'

    id_departamento = db.Column(db.Integer, primary_key=True)
    id_tenant = db.Column(db.Integer, db.ForeignKey('tenants.id_tenant'), nullable=True)
    nome = db.Column(db.String(150), nullable=False)
    id_diretoria = db.Column(
        db.Integer,
        db.ForeignKey('diretorias.id_diretoria'),
        nullable=False
    )

    # 🔁 Relação 1:N com Demandas
    demandas = db.relationship(
        'Demanda',
        back_populates='departamento',
        cascade="all, delete-orphan",
        lazy=True
    )

    def __repr__(self):
        return f"<Departamento {self.nome}>"


# ==========================================================
# 🧾 DEMANDAS
# ==========================================================
class Demanda(db.Model):
    __tablename__ = 'demandas'

    id_demanda = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(100), nullable=False)

    # 🔗 Vinculações hierárquicas
    id_diretoria = db.Column(
        db.Integer,
        db.ForeignKey('diretorias.id_diretoria'),
        nullable=True
    )
    id_departamento = db.Column(
        db.Integer,
        db.ForeignKey('departamentos.id_departamento'),
        nullable=True
    )

    diretoria = db.relationship("Diretoria", backref="demandas", lazy=True)
    departamento = db.relationship("Departamento", back_populates="demandas", lazy=True)

    def __repr__(self):
        return f"<Demanda {self.descricao}>"


# ==========================================================
# 🧩 TIPOS DE DEMANDA
# ==========================================================
class TipoDemanda(db.Model):
    __tablename__ = 'tipos_demanda'

    id_tipo = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(50), nullable=False)


# ==========================================================
# 📑 PROCESSOS / CHAMADOS (CHAMADO É O ALIAS GENÉRICO)
# ==========================================================
class Processo(db.Model):
    __tablename__ = 'processos'

    id_processo = db.Column(db.Integer, primary_key=True)
    id_tenant = db.Column(db.Integer, db.ForeignKey('tenants.id_tenant'), nullable=True)
    numero_processo = db.Column(db.String(25), unique=True, nullable=False)
    status_atual = db.Column(db.String(100))
    observacoes = db.Column(db.Text)
    diretoria_destino = db.Column(db.String(100), nullable=False)
    dados_customizados = db.Column(db.JSON, nullable=True)

    tenant = db.relationship('Tenant', backref='processos', lazy=True)

    entradas = db.relationship(
        'EntradaProcesso',
        backref='processo',
        cascade="all, delete-orphan",
        lazy=True
    )


# Alias genérico para novo padrão de chamados
Chamado = Processo


# ==========================================================
# 🔁 ENTRADAS DE PROCESSO
# ==========================================================
class EntradaProcesso(db.Model):
    __tablename__ = 'entradas_processo'

    id_entrada = db.Column(db.Integer, primary_key=True)
    id_processo = db.Column(
        db.Integer,
        db.ForeignKey('processos.id_processo'),
        nullable=False
    )
    data_criacao_ra = db.Column(db.Date, nullable=False)
    data_entrada_novacap = db.Column(db.Date, nullable=False)
    data_documento = db.Column(db.Date, nullable=False)
    ra_origem = db.Column(db.String(100), nullable=False)

    id_demanda = db.Column(
        db.Integer,
        db.ForeignKey('demandas.id_demanda'),
        nullable=False
    )
    demanda = db.relationship('Demanda', foreign_keys=[id_demanda], lazy=True)
    usuario_responsavel = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id_usuario'),
        nullable=False
    )
    responsavel = db.relationship("Usuario", foreign_keys=[usuario_responsavel])


    status_inicial = db.Column(
        db.String(100),
        db.ForeignKey('status.descricao'),
        nullable=False
    )

    movimentacoes = db.relationship(
        'Movimentacao',
        backref='entrada',
        cascade="all, delete-orphan",
        lazy=True
    )

    alertas = db.relationship(
        'Alerta',
        backref='entrada',
        cascade="all, delete-orphan",
        lazy=True
    )


# ==========================================================
# 🔄 MOVIMENTAÇÕES DE PROCESSOS
# ==========================================================
class Movimentacao(db.Model):
    __tablename__ = 'movimentacoes'

    id_movimentacao = db.Column(db.Integer, primary_key=True)
    id_entrada = db.Column(
        db.Integer,
        db.ForeignKey('entradas_processo.id_entrada'),
        nullable=False
    )
    id_usuario = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id_usuario'),
        nullable=False
    )
    novo_status = db.Column(
        db.String(100),
        db.ForeignKey('status.descricao'),
        nullable=False
    )
    data = db.Column(db.DateTime, default=datetime.utcnow)
    observacao = db.Column(db.Text)

    usuario = db.relationship("Usuario", backref="movimentacoes", lazy=True)


# ==========================================================
# 🏷️ STATUS
# ==========================================================
class Status(db.Model):
    __tablename__ = 'status'

    id_status = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(100), unique=True, nullable=False)
    ordem_exibicao = db.Column(db.Integer)
    finaliza_processo = db.Column(db.Boolean, default=False)


# ==========================================================
# 🗺️ UNIDADES SOLICITANTES (EX-REGIÕES ADMINISTRATIVAS / FILIAIS)
# ==========================================================
class UnidadeSolicitante(db.Model):
    __tablename__ = 'unidades_solicitantes'

    id_unidade = db.Column(db.Integer, primary_key=True)
    id_tenant = db.Column(db.Integer, db.ForeignKey('tenants.id_tenant'), nullable=True)
    codigo = db.Column(db.String(20), nullable=False)
    nome_unidade = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(150))

    tenant = db.relationship('Tenant', backref='unidades_solicitantes', lazy=True)


# Alias para compatibilidade com a versão legada
RegiaoAdministrativa = UnidadeSolicitante


# ==========================================================
# 📋 LOGS DE USUÁRIOS
# ==========================================================
class LogUsuario(db.Model):
    __tablename__ = 'logs_usuarios'

    id_log = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id_usuario'),
        nullable=False
    )
    acao = db.Column(db.String(100), nullable=False)
    tabela_afetada = db.Column(db.String(100))
    id_referencia = db.Column(db.Integer)
    descricao_detalhada = db.Column(db.Text)
    ip_origem = db.Column(db.String(45))
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)


# ==========================================================
# 🚨 ALERTAS
# ==========================================================
class Alerta(db.Model):
    __tablename__ = 'alertas'

    id_alerta = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id_usuario'),
        nullable=False
    )
    tipo_alerta = db.Column(db.String(100), nullable=False)
    numero_processo = db.Column(db.String(25), nullable=False)
    id_entrada = db.Column(
        db.Integer,
        db.ForeignKey('entradas_processo.id_entrada'),
        nullable=False
    )
    mensagem = db.Column(db.Text, nullable=False)
    data_alerta = db.Column(db.DateTime, default=datetime.utcnow)
    respondido = db.Column(db.Boolean, default=False)
    data_resposta = db.Column(db.DateTime)
    forma_resposta = db.Column(db.String(50))


# ==========================================================
# ⚙️ MOTOR DE WORKFLOW (TRANSIÇÕES DE STATUS DINÂMICAS)
# ==========================================================
class TransicaoWorkflow(db.Model):
    __tablename__ = 'transicoes_workflow'

    id_transicao = db.Column(db.Integer, primary_key=True)
    id_tenant = db.Column(db.Integer, db.ForeignKey('tenants.id_tenant'), nullable=True)
    status_origem = db.Column(db.String(100), nullable=False)
    status_destino = db.Column(db.String(100), nullable=False)
    permissao_requerida = db.Column(db.String(50), default="padrao")

    tenant = db.relationship('Tenant', backref='transicoes_workflow', lazy=True)


# ==========================================================
# ⏱️ CONFIGURAÇÃO DE SLA (SERVICE LEVEL AGREEMENT)
# ==========================================================
class SLAConfig(db.Model):
    __tablename__ = 'sla_configs'

    id_sla = db.Column(db.Integer, primary_key=True)
    id_tenant = db.Column(db.Integer, db.ForeignKey('tenants.id_tenant'), nullable=True)
    prioridade = db.Column(db.String(20), nullable=False)  # Baixa, Média, Alta, Crítica
    prazo_horas = db.Column(db.Integer, nullable=False, default=48)
    notificar_antes_horas = db.Column(db.Integer, default=4)

    tenant = db.relationship('Tenant', backref='sla_configs', lazy=True)


# ==========================================================
# 🔍 TRILHA DE AUDITORIA DE PROCESSOS (US08)
# ==========================================================
class AuditoriaProcesso(db.Model):
    __tablename__ = 'auditoria_processos'

    id_auditoria = db.Column(db.Integer, primary_key=True)
    id_processo = db.Column(
        db.Integer,
        db.ForeignKey('processos.id_processo', ondelete='CASCADE'),
        nullable=False
    )
    id_usuario = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id_usuario'),
        nullable=True
    )
    campo_alterado = db.Column(db.String(100), nullable=False)
    valor_anterior = db.Column(db.Text, nullable=True)
    valor_novo = db.Column(db.Text, nullable=True)
    acao = db.Column(db.String(100), default='Alteração')
    justificativa = db.Column(db.Text, nullable=True)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ip_origem = db.Column(db.String(45), nullable=True)

    # Relacionamentos
    processo = db.relationship(
        'Processo',
        backref=db.backref('historico_auditoria', lazy=True, cascade='all, delete-orphan', order_by='desc(AuditoriaProcesso.data_hora)')
    )
    usuario = db.relationship('Usuario', backref='auditorias_realizadas', lazy=True)

    def to_dict(self):
        return {
            'id_auditoria': self.id_auditoria,
            'id_processo': self.id_processo,
            'usuario': self.usuario.nome if self.usuario else (self.usuario.usuario if self.usuario else 'Sistema / Auditoria Automática'),
            'campo_alterado': self.campo_alterado,
            'valor_anterior': self.valor_anterior or '---',
            'valor_novo': self.valor_novo or '---',
            'acao': self.acao,
            'justificativa': self.justificativa or '',
            'data_hora': self.data_hora.strftime('%d/%m/%Y %H:%M:%S') if self.data_hora else '---',
            'ip_origem': self.ip_origem or '---'
        }