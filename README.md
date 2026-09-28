# 🏗 Sistema da Central de Relacionamento – NOVACAP

Este sistema foi desenvolvido para atender à Central de Relacionamento (CR) da Companhia Urbanizadora da Nova Capital (NOVACAP), com o objetivo de registrar, acompanhar, tramitar e exportar processos administrativos.

---

## ⚙️ Tecnologias utilizadas

- Python 3.11+
- Flask
- SQLAlchemy
- Flask-Migrate
- HTML + CSS (Flexbox)
- MySQL (produção e testes)
- Git + GitHub

---

## 🧱 Estrutura do projeto

CR_NOVACAP/ ├── app/ │ ├── static/ │ │ └── css/ │ │ └── styles.css │ ├── templates/ │ │ ├── *.html # (todos os templates da interface) │ ├── models/ │ │ └── modelos.py │ ├── docs/ │ │ ├── MERs, checklist de testes etc. │ └── ext.py │ ├── scripts/ ├── venv/ # ambiente virtual (não versionado) ├── run.py # ponto de entrada da aplicação ├── configuracoes.py # configuração de ambiente e credenciais ├── requirements.txt ├── .env ├── .env.example ├── .gitignore ├── LICENSE └── README.md

---

## 🚀 Como rodar localmente

```bash
git clone https://github.com/PadawanXXVI/cr_novacap.git
cd cr_novacap

# Criar ambiente virtual
python -m venv venv
source venv/Scripts/activate  # (Windows Git Bash)

# Instalar dependências
pip install -r requirements.txt

# Criar arquivo .env a partir do modelo
cp .env.example .env

# Editar .env com sua SECRET_KEY e URL do banco de dados
```

---

## 🔑 Exemplo de .env

```env
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=sua_chave_secreta
DATABASE_URL=mysql+pymysql://usuario:senha@localhost/nome_do_banco
```
Para gerar uma SECRET_KEY segura, execute no terminal:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
---

## ▶️ Para rodar a aplicação:

```bash
flask run
```

Acesse: http://127.0.0.1:5000/

---

## 🧭 Objetivos do sistema

- Registrar e acompanhar processos administrativos da CR
- Facilitar tramitações internas com histórico e responsável técnico
- Gerar relatórios estratégicos para gestão
- Exportar dados em diferentes formatos

---

## 🧩 Módulos do sistema

- 📁 Processos administrativos  
Registro, tramitação e histórico de processos internos da CR

- 📊 Dashboard e Painel Gerencial  
Cards com indicadores por status, tipo de protocolo e área responsável

- 🧾 Exportação de relatórios  
Exportação para CSV, Excel, PDF, DOCX e JSON (em desenvolvimento)

---

## 🎯 Funcionalidades

- Autenticação de usuários com permissões (admin, padrão)
- Cadastro e atualização de processos
- Visualização do histórico completo de tramitação
- Dashboards estatísticos
- Filtros e relatórios gerenciais e avançados
- Exportação de dados (CSV, Excel)
- Troca de senha com validação
- Aprovação e bloqueio de usuários via painel admin

---

## 📦 Exportações suportadas

- ✅ CSV
- ✅ Excel
- 🔄 PDF (em desenvolvimento)
- 🔄 DOCX (em desenvolvimento)
- 🔄 JSON (em desenvolvimento)

---

## 🧪 Testes

- Testes manuais em ambiente local
- Checklist de funcionalidades por tela
- Planejamento de testes automatizados (pytest/unittest)

---

## 🔐 Segurança

- Senhas criptografadas com hash seguro (Werkzeug)
- Variáveis de ambiente protegidas (.env)
- Acesso restrito por login
- Restrições por perfil de usuário

---

## 🔄 Fluxo de desenvolvimento

- Clonar repositório
- Ativar venv e instalar dependências
- Executar flask run
- Enviar alterações via Git
- Gerenciar tarefas com GitHub Projects (Kanban)

---

## 👤 Autor

Anderson de Matos Guimarães  
Central de Relacionamento – NOVACAP  
Brasília/DF – 2025

---
