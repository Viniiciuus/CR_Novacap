import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_novacap_presentation(output_path):
    prs = Presentation()
    
    # 16:9 Widescreen dimensions
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    
    # Blank slide layout
    blank_layout = prs.slide_layouts[6]
    
    # Color Palette Definitions
    NAVY = RGBColor(15, 44, 89)        # #0F2C59 - Primary Header & Dark Slide BG
    TEAL = RGBColor(0, 168, 150)       # #00A896 - Primary Accent
    GOLD = RGBColor(245, 158, 11)      # #F59E0B - Highlight Accent
    DARK_TEXT = RGBColor(30, 41, 59)   # #1E293B - Body Text
    GRAY_BG = RGBColor(248, 250, 252)  # #F8FAFC - Card Background
    WHITE = RGBColor(255, 255, 255)
    LIGHT_BLUE = RGBColor(235, 243, 250)
    BORDER_GRAY = RGBColor(226, 232, 240)
    TEXT_MUTED = RGBColor(100, 116, 139)
    
    LOGO_PATH = os.path.join("app", "static", "images", "logo-novacap.png")
    has_logo = os.path.exists(LOGO_PATH)

    def set_slide_background(slide, color):
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = color

    def add_header(slide, category_tag, title_text):
        # Header banner area
        header_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.733), Inches(1.1))
        tf = header_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        # Category Tag
        p_tag = tf.paragraphs[0]
        p_tag.text = category_tag.upper()
        p_tag.font.size = Pt(11)
        p_tag.font.bold = True
        p_tag.font.color.rgb = TEAL
        p_tag.space_after = Pt(2)
        
        # Title Text
        p_title = tf.add_paragraph()
        p_title.text = title_text
        p_title.font.size = Pt(24)
        p_title.font.bold = True
        p_title.font.color.rgb = NAVY
        
        # Insert Logo if available
        if has_logo:
            try:
                slide.shapes.add_picture(LOGO_PATH, Inches(11.2), Inches(0.4), height=Inches(0.6))
            except Exception:
                pass
                
        # Decorative divider line under header
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.45), Inches(11.733), Inches(0.03))
        line.fill.solid()
        line.fill.fore_color.rgb = TEAL
        line.line.fill.background()

    def add_card(slide, left, top, width, height, bg_color=GRAY_BG, border_color=BORDER_GRAY):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = bg_color
        if border_color:
            shape.line.color.rgb = border_color
            shape.line.width = Pt(1)
        else:
            shape.line.fill.background()
        return shape

    # =========================================================================
    # SLIDE 1: CAPA (TITLE SLIDE) - DARK THEME
    # =========================================================================
    slide1 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide1, NAVY)
    
    # Decorative accent bar on left
    accent_bar = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.4), Inches(7.5))
    accent_bar.fill.solid()
    accent_bar.fill.fore_color.rgb = TEAL
    accent_bar.line.fill.background()

    # Logo on Title Slide
    if has_logo:
        try:
            slide1.shapes.add_picture(LOGO_PATH, Inches(1.0), Inches(0.8), height=Inches(0.9))
        except Exception:
            pass

    # Title Container
    title_box = slide1.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(11.0), Inches(4.5))
    tf1 = title_box.text_frame
    tf1.word_wrap = True
    
    p1 = tf1.paragraphs[0]
    p1.text = "CENTRAL DE RELACIONAMENTO – NOVACAP"
    p1.font.size = Pt(14)
    p1.font.bold = True
    p1.font.color.rgb = TEAL
    p1.space_after = Pt(10)
    
    p2 = tf1.add_paragraph()
    p2.text = "Sistema de Controle de Processos SEI"
    p2.font.size = Pt(36)
    p2.font.bold = True
    p2.font.color.rgb = WHITE
    p2.space_after = Pt(14)
    
    p3 = tf1.add_paragraph()
    p3.text = "Gestão, Tramitação e Inteligência de Dados para a NOVACAP"
    p3.font.size = Pt(18)
    p3.font.color.rgb = RGBColor(203, 213, 225)
    p3.space_after = Pt(40)
    
    p4 = tf1.add_paragraph()
    p4.text = "Apresentador: Anderson de Matos Guimarães | Central de Relacionamento - NOVACAP\nGoverno do Distrito Federal (GDF) • 2025/2026"
    p4.font.size = Pt(13)
    p4.font.color.rgb = RGBColor(148, 163, 184)


    # =========================================================================
    # SLIDE 2: CONTEXTO & DESAFIOS INSTITUCIONAIS
    # =========================================================================
    slide2 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide2, WHITE)
    add_header(slide2, "CONTEXTO & NECESSIDADE", "Contexto Institucional e Desafios de Gestão")
    
    col_w = Inches(3.64)
    gap = Inches(0.4)
    start_x = Inches(0.8)
    top_y = Inches(1.8)
    card_h = Inches(5.0)
    
    cards_data = [
        {
            "icon": "🏢",
            "title": "Escala do Atendimento",
            "bullets": [
                "Tramitações vinculadas às Regiões Administrativas (RAs) e órgãos do DF.",
                "Volume diário de chamados de obras, drenagem e serviços urbanos.",
                "Necessidade de comunicação ágil e padronizada."
            ],
            "accent": TEAL
        },
        {
            "icon": "⚙️",
            "title": "Modernização de Fluxos",
            "bullets": [
                "Substituição do trâmite manual de papéis.",
                "Eliminação de atrasos e extravios de documentação.",
                "Centralização do histórico completo de movimentações."
            ],
            "accent": GOLD
        },
        {
            "icon": "🎯",
            "title": "Objetivo do Sistema",
            "bullets": [
                "Autuação, acompanhamento e exportação de processos SEI.",
                "Visibilidade executiva do status de tramitação.",
                "Geração de dados consolidados para os gestores."
            ],
            "accent": NAVY
        }
    ]
    
    for i, c in enumerate(cards_data):
        x = start_x + i * (col_w + gap)
        add_card(slide2, x, top_y, col_w, card_h)
        
        # Header strip inside card
        header_shape = slide2.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, top_y, col_w, Inches(0.8))
        header_shape.fill.solid()
        header_shape.fill.fore_color.rgb = c["accent"]
        header_shape.line.fill.background()
        
        tf_h = header_shape.text_frame
        tf_h.word_wrap = True
        p = tf_h.paragraphs[0]
        p.text = f"{c['icon']}  {c['title']}"
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.CENTER
        
        tb = slide2.shapes.add_textbox(x + Inches(0.2), top_y + Inches(1.0), col_w - Inches(0.4), card_h - Inches(1.2))
        tf = tb.text_frame
        tf.word_wrap = True
        for idx, bullet in enumerate(c["bullets"]):
            p_b = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
            p_b.text = f"• {bullet}"
            p_b.font.size = Pt(13)
            p_b.font.color.rgb = DARK_TEXT
            p_b.space_after = Pt(12)


    # =========================================================================
    # SLIDE 3: VISÃO GERAL DA SOLUÇÃO
    # =========================================================================
    slide3 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide3, WHITE)
    add_header(slide3, "A SOLUÇÃO", "Visão Geral do Sistema CR-NOVACAP")
    
    # Left Box
    add_card(slide3, Inches(0.8), Inches(1.8), Inches(5.6), Inches(3.6))
    tb_left = slide3.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(5.2), Inches(3.2))
    tf_l = tb_left.text_frame
    tf_l.word_wrap = True
    
    p = tf_l.paragraphs[0]
    p.text = "💻 O que é o Sistema?"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = NAVY
    p.space_after = Pt(12)
    
    p_desc = tf_l.add_paragraph()
    p_desc.text = "Solução web centralizada desenvolvida para a Central de Relacionamento (CR).\n\nGerencia a recepção, autuação, distribuição, tramitação e encerramento de processos administrativos da NOVACAP com total rastreabilidade."
    p_desc.font.size = Pt(14)
    p_desc.font.color.rgb = DARK_TEXT
    
    # Right Box
    add_card(slide3, Inches(6.9), Inches(1.8), Inches(5.633), Inches(3.6))
    tb_right = slide3.shapes.add_textbox(Inches(7.1), Inches(2.0), Inches(5.233), Inches(3.2))
    tf_r = tb_right.text_frame
    tf_r.word_wrap = True
    
    p_r = tf_r.paragraphs[0]
    p_r.text = "👥 Público-Alvo & Usuários"
    p_r.font.size = Pt(18)
    p_r.font.bold = True
    p_r.font.color.rgb = NAVY
    p_r.space_after = Pt(12)
    
    bullets_r = [
        "Equipe da Central de Relacionamento (CR)",
        "Gestores e Administradores da NOVACAP",
        "Técnicos das Diretorias e Departamentos Operacionais"
    ]
    for idx, b in enumerate(bullets_r):
        p_b = tf_r.add_paragraph()
        p_b.text = f"✔ {b}"
        p_b.font.size = Pt(13)
        p_b.font.color.rgb = DARK_TEXT
        p_b.space_after = Pt(10)
        
    # Bottom Benefit Badges Grid
    metrics = [
        {"val": "100% Digital", "lbl": "Sem papéis ou perda de histórico"},
        {"val": "Rastreabilidade", "lbl": "Controle total das tramitações"},
        {"val": "Painéis BI", "lbl": "Métricas e estatísticas em tempo real"},
        {"val": "Exportações", "lbl": "CSV, Excel, PDF, DOCX e JSON"}
    ]
    
    b_w = Inches(2.78)
    b_gap = Inches(0.2)
    for i, m in enumerate(metrics):
        bx = Inches(0.8) + i * (b_w + b_gap)
        add_card(slide3, bx, Inches(5.7), b_w, Inches(1.2), bg_color=LIGHT_BLUE, border_color=TEAL)
        
        tb_m = slide3.shapes.add_textbox(bx, Inches(5.75), b_w, Inches(1.1))
        tf_m = tb_m.text_frame
        tf_m.word_wrap = True
        
        pm1 = tf_m.paragraphs[0]
        pm1.text = m["val"]
        pm1.font.size = Pt(16)
        pm1.font.bold = True
        pm1.font.color.rgb = NAVY
        pm1.alignment = PP_ALIGN.CENTER
        
        pm2 = tf_m.add_paragraph()
        pm2.text = m["lbl"]
        pm2.font.size = Pt(11)
        pm2.font.color.rgb = TEXT_MUTED
        pm2.alignment = PP_ALIGN.CENTER


    # =========================================================================
    # SLIDE 4: MÓDULOS PRINCIPAIS
    # =========================================================================
    slide4 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide4, WHITE)
    add_header(slide4, "FUNCIONALIDADES", "Módulos Principais do Sistema")
    
    m_w = Inches(2.75)
    m_gap = Inches(0.24)
    m_top = Inches(1.8)
    m_h = Inches(5.0)
    
    modulos = [
        {
            "icon": "📁",
            "name": "Processos Administrativos",
            "items": [
                "Autuação e protocolo unificado",
                "Registro de nº SEI e RA de origem",
                "Observações e anexos",
                "Histórico completo de trâmites",
                "Encaminhamento por diretoria"
            ]
        },
        {
            "icon": "📊",
            "name": "Dashboard & Indicadores",
            "items": [
                "Cards de totais em tempo real",
                "Visão por status atual",
                "Métricas por tipo de demanda",
                "Filtros por diretoria e RA",
                "Identificação de gargalos"
            ]
        },
        {
            "icon": "🧾",
            "name": "Relatórios & Exportação",
            "items": [
                "Filtros combináveis dinâmicos",
                "Exportação em Excel (.xlsx)",
                "Exportação em CSV",
                "Suporte a PDF e DOCX",
                "Dados analíticos consolidados"
            ]
        },
        {
            "icon": "🔐",
            "name": "Painel Administrativo",
            "items": [
                "Gestão de usuários (Admin/Padrão)",
                "Aprovação prévia de cadastros",
                "Bloqueio/desbloqueio de acesso",
                "Troca segura de senha",
                "Controle de perfis de permissão"
            ]
        }
    ]
    
    for i, m in enumerate(modulos):
        mx = Inches(0.8) + i * (m_w + m_gap)
        add_card(slide4, mx, m_top, m_w, m_h)
        
        banner = slide4.shapes.add_shape(MSO_SHAPE.RECTANGLE, mx, m_top, m_w, Inches(1.0))
        banner.fill.solid()
        banner.fill.fore_color.rgb = NAVY
        banner.line.fill.background()
        
        tf_b = banner.text_frame
        tf_b.word_wrap = True
        p = tf_b.paragraphs[0]
        p.text = f"{m['icon']}\n{m['name']}"
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.CENTER
        
        tb = slide4.shapes.add_textbox(mx + Inches(0.15), m_top + Inches(1.15), m_w - Inches(0.3), m_h - Inches(1.3))
        tf = tb.text_frame
        tf.word_wrap = True
        for idx, item in enumerate(m["items"]):
            p_item = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
            p_item.text = f"• {item}"
            p_item.font.size = Pt(12)
            p_item.font.color.rgb = DARK_TEXT
            p_item.space_after = Pt(8)


    # =========================================================================
    # SLIDE 5: FLUXO DE TRAMITAÇÃO
    # =========================================================================
    slide5 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide5, WHITE)
    add_header(slide5, "FLUXO DE TRABALHO", "Ciclo de Vida do Processo Administrativo")
    
    # Top banner explanation
    add_card(slide5, Inches(0.8), Inches(1.8), Inches(11.733), Inches(0.9), bg_color=LIGHT_BLUE, border_color=TEAL)
    tb_top = slide5.shapes.add_textbox(Inches(1.0), Inches(1.85), Inches(11.333), Inches(0.8))
    tf_top = tb_top.text_frame
    tf_top.word_wrap = True
    p = tf_top.paragraphs[0]
    p.text = "🔄 Fluxo Estruturado e Transparente:"
    p.font.bold = True
    p.font.size = Pt(14)
    p.font.color.rgb = NAVY
    
    p_sub = tf_top.add_paragraph()
    p_sub.text = "Cada processo flui da solicitação inicial até a análise e conclusão pelo setor técnico competente."
    p_sub.font.size = Pt(12)
    p_sub.font.color.rgb = DARK_TEXT
    
    steps = [
        {"step": "01", "title": "Entrada / Protocolo", "desc": "Registro da demanda com RA e dados do processo SEI"},
        {"step": "02", "title": "Triagem CR", "desc": "Autuação, conferência e validação na Central de Relacionamento"},
        {"step": "03", "title": "Diretoria", "desc": "Encaminhamento para a Diretoria responsável (ex: DE, DU)"},
        {"step": "04", "title": "Análise Técnica", "desc": "Tramitação no departamento com registro de observações"},
        {"step": "05", "title": "Conclusão", "desc": "Parecer final, atualização de status e relatórios de encerramento"}
    ]
    
    step_w = Inches(2.18)
    step_gap = Inches(0.2)
    step_top = Inches(3.1)
    step_h = Inches(3.6)
    
    for i, s in enumerate(steps):
        sx = Inches(0.8) + i * (step_w + step_gap)
        add_card(slide5, sx, step_top, step_w, step_h)
        
        num_box = slide5.shapes.add_shape(MSO_SHAPE.OVAL, sx + Inches(0.74), step_top + Inches(0.2), Inches(0.7), Inches(0.7))
        num_box.fill.solid()
        num_box.fill.fore_color.rgb = TEAL if i < 4 else GOLD
        num_box.line.fill.background()
        
        tf_n = num_box.text_frame
        p_n = tf_n.paragraphs[0]
        p_n.text = s["step"]
        p_n.font.size = Pt(16)
        p_n.font.bold = True
        p_n.font.color.rgb = WHITE
        p_n.alignment = PP_ALIGN.CENTER
        
        tb_s = slide5.shapes.add_textbox(sx + Inches(0.1), step_top + Inches(1.1), step_w - Inches(0.2), step_h - Inches(1.2))
        tf_s = tb_s.text_frame
        tf_s.word_wrap = True
        
        p_t = tf_s.paragraphs[0]
        p_t.text = s["title"]
        p_t.font.size = Pt(14)
        p_t.font.bold = True
        p_t.font.color.rgb = NAVY
        p_t.alignment = PP_ALIGN.CENTER
        p_t.space_after = Pt(8)
        
        p_d = tf_s.add_paragraph()
        p_d.text = s["desc"]
        p_d.font.size = Pt(12)
        p_d.font.color.rgb = DARK_TEXT
        p_d.alignment = PP_ALIGN.CENTER


    # =========================================================================
    # SLIDE 6: DASHBOARDS, BI E EXPORTAÇÃO DE DADOS
    # =========================================================================
    slide6 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide6, WHITE)
    add_header(slide6, "INTELIGÊNCIA DE DADOS", "Painéis Gerenciais e Exportação de Relatórios")
    
    # Left Block - BI
    add_card(slide6, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0))
    tb_bi = slide6.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(5.2), Inches(4.6))
    tf_bi = tb_bi.text_frame
    tf_bi.word_wrap = True
    
    p = tf_bi.paragraphs[0]
    p.text = "📈 Painel Gerencial BI"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = NAVY
    p.space_after = Pt(12)
    
    bi_points = [
        "Cards de Indicadores (KPIs) com contadores em tempo real.",
        "Métricas por Status: Atendido, Em Atendimento, Improcedente, Devolvido.",
        "Filtros dinâmicos por período, Região Administrativa (RA) e diretoria.",
        "Monitoramento visual de demandas urgentes e volumetria."
    ]
    for b in bi_points:
        p_b = tf_bi.add_paragraph()
        p_b.text = f"✔ {b}"
        p_b.font.size = Pt(12)
        p_b.font.color.rgb = DARK_TEXT
        p_b.space_after = Pt(10)

    # Right Block - Exportações
    add_card(slide6, Inches(6.9), Inches(1.8), Inches(5.633), Inches(5.0))
    tb_exp = slide6.shapes.add_textbox(Inches(7.1), Inches(2.0), Inches(5.233), Inches(4.6))
    tf_exp = tb_exp.text_frame
    tf_exp.word_wrap = True
    
    p_e = tf_exp.paragraphs[0]
    p_e.text = "🧾 Formatos de Exportação Suportados"
    p_e.font.size = Pt(17)
    p_e.font.bold = True
    p_e.font.color.rgb = NAVY
    p_e.space_after = Pt(12)
    
    formats = [
        "📊 Excel (.xlsx) – Planilhas completas com filtros para análise de dados",
        "📄 CSV – Exportação leve para cruzamento e integração de dados",
        "📑 PDF – Relatórios oficiais prontos para impressão e arquivo",
        "📝 DOCX – Documentos editáveis para pareceres administrativos",
        "🔌 JSON – Formato para comunicação e APIs de dados"
    ]
    for f in formats:
        p_f = tf_exp.add_paragraph()
        p_f.text = f"• {f}"
        p_f.font.size = Pt(12)
        p_f.font.color.rgb = DARK_TEXT
        p_f.space_after = Pt(8)


    # =========================================================================
    # SLIDE 7: SEGURANÇA E AUDITORIA
    # =========================================================================
    slide7 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide7, WHITE)
    add_header(slide7, "SEGURANÇA & AUDITORIA", "Proteção de Dados e Gestão de Perfis")
    
    sec_w = Inches(3.64)
    sec_gap = Inches(0.4)
    
    sec_cards = [
        {
            "icon": "🔐",
            "title": "Autenticação Segura",
            "bullets": [
                "Senhas criptografadas com hash seguro (Werkzeug).",
                "Sessões protegidas contra acessos não autorizados.",
                "Variáveis de ambiente protegidas (`.env`)."
            ]
        },
        {
            "icon": "🛡️",
            "title": "Controle de Perfis",
            "bullets": [
                "Separação entre Administrador e Usuários Padrão.",
                "Aprovação prévia obrigatória de novos cadastros via Painel Admin.",
                "Bloqueio e liberação rápida de contas de usuário."
            ]
        },
        {
            "icon": "🔒",
            "title": "Integridade de Dados",
            "bullets": [
                "Validação rigorosa de formulários e rotas.",
                "Garantia de consistência no banco de dados relacional.",
                "Prevenção contra alterações indevidas ou dados órfãos."
            ]
        }
    ]
    
    for i, s in enumerate(sec_cards):
        sx = Inches(0.8) + i * (sec_w + sec_gap)
        add_card(slide7, sx, Inches(1.8), sec_w, Inches(5.0))
        
        tb = slide7.shapes.add_textbox(sx + Inches(0.2), Inches(2.0), sec_w - Inches(0.4), Inches(4.6))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = f"{s['icon']} {s['title']}"
        p.font.size = Pt(17)
        p.font.bold = True
        p.font.color.rgb = NAVY
        p.space_after = Pt(14)
        
        for b in s["bullets"]:
            p_b = tf.add_paragraph()
            p_b.text = f"• {b}"
            p_b.font.size = Pt(12)
            p_b.font.color.rgb = DARK_TEXT
            p_b.space_after = Pt(12)


    # =========================================================================
    # SLIDE 8: STACK TECNOLÓGICO
    # =========================================================================
    slide8 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide8, WHITE)
    add_header(slide8, "ENGENHARIA DE SOFTWARE", "Tecnologias e Arquitetura do Sistema")
    
    t_w = Inches(5.6)
    t_h = Inches(2.35)
    t_gap_x = Inches(0.533)
    t_gap_y = Inches(0.3)
    
    techs = [
        {
            "cat": "🐍 Backend Python & Flask",
            "items": ["Python 3.11+", "Flask Framework (Blueprints Modulares)", "SQLAlchemy ORM & Flask-Migrate", "Segurança via Werkzeug / Flask-Login"]
        },
        {
            "cat": "🗄️ Banco de Dados Relacional",
            "items": ["MySQL (Ambiente de Produção)", "SQLite (Desenvolvimento Local)", "Modelagem relacional normalizada"]
        },
        {
            "cat": "🎨 Frontend & Interface (UI/UX)",
            "items": ["HTML5 Semântico & CSS3 Moderno (Flexbox)", "JavaScript ES6+ para interatividade", "Layout Responsivo (Dark / Light Mode)"]
        },
        {
            "cat": "⚙️ Práticas & DevOps",
            "items": ["Controle de versão Git + GitHub", "Variáveis de ambiente (.env) para credenciais", "Gestão de tarefas com GitHub Projects (Kanban)"]
        }
    ]
    
    positions = [
        (Inches(0.8), Inches(1.8)),
        (Inches(0.8) + t_w + t_gap_x, Inches(1.8)),
        (Inches(0.8), Inches(1.8) + t_h + t_gap_y),
        (Inches(0.8) + t_w + t_gap_x, Inches(1.8) + t_h + t_gap_y)
    ]
    
    for i, t in enumerate(techs):
        pos_x, pos_y = positions[i]
        add_card(slide8, pos_x, pos_y, t_w, t_h)
        
        tb = slide8.shapes.add_textbox(pos_x + Inches(0.2), pos_y + Inches(0.15), t_w - Inches(0.4), t_h - Inches(0.3))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = t["cat"]
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = NAVY
        p.space_after = Pt(8)
        
        for item in t["items"]:
            p_i = tf.add_paragraph()
            p_i.text = f"• {item}"
            p_i.font.size = Pt(12)
            p_i.font.color.rgb = DARK_TEXT
            p_i.space_after = Pt(4)


    # =========================================================================
    # SLIDE 9: RESULTADOS & IMPACTO
    # =========================================================================
    slide9 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide9, WHITE)
    add_header(slide9, "RESULTADOS & IMPACTO", "Benefícios Alcançados para a NOVACAP")
    
    card_metric_w = Inches(3.64)
    gap_metric = Inches(0.4)
    
    impacts = [
        {
            "metric": "+60%",
            "title": "Agilidade Operacional",
            "desc": "Redução no tempo de tramitação e resposta às demandas administrativas."
        },
        {
            "metric": "100%",
            "title": "Rastreabilidade",
            "desc": "Histórico completo de cada processo sem perda de dados ou informações."
        },
        {
            "metric": "🌿 0 Papel",
            "title": "Ecoeficiência",
            "desc": "Digitalização completa dos fluxos, economizando impressões e papel."
        }
    ]
    
    for i, imp in enumerate(impacts):
        ix = Inches(0.8) + i * (card_metric_w + gap_metric)
        add_card(slide9, ix, Inches(1.8), card_metric_w, Inches(5.0), bg_color=GRAY_BG)
        
        m_box = slide9.shapes.add_shape(MSO_SHAPE.RECTANGLE, ix, Inches(1.8), card_metric_w, Inches(1.5))
        m_box.fill.solid()
        m_box.fill.fore_color.rgb = NAVY if i != 2 else TEAL
        m_box.line.fill.background()
        
        tf_mb = m_box.text_frame
        tf_mb.word_wrap = True
        p_m = tf_mb.paragraphs[0]
        p_m.text = imp["metric"]
        p_m.font.size = Pt(32)
        p_m.font.bold = True
        p_m.font.color.rgb = WHITE
        p_m.alignment = PP_ALIGN.CENTER
        
        tb = slide9.shapes.add_textbox(ix + Inches(0.2), Inches(3.5), card_metric_w - Inches(0.4), Inches(3.1))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p_t = tf.paragraphs[0]
        p_t.text = imp["title"]
        p_t.font.size = Pt(18)
        p_t.font.bold = True
        p_t.font.color.rgb = NAVY
        p_t.alignment = PP_ALIGN.CENTER
        p_t.space_after = Pt(12)
        
        p_d = tf.add_paragraph()
        p_d.text = imp["desc"]
        p_d.font.size = Pt(13)
        p_d.font.color.rgb = DARK_TEXT
        p_d.alignment = PP_ALIGN.CENTER


    # =========================================================================
    # SLIDE 10: CONCLUSÃO E ENCERRAMENTO - DARK THEME
    # =========================================================================
    slide10 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide10, NAVY)
    
    # Left Column - Speaker Highlights
    tb_road = slide10.shapes.add_textbox(Inches(0.8), Inches(1.0), Inches(6.0), Inches(5.5))
    tf_road = tb_road.text_frame
    tf_road.word_wrap = True
    
    p = tf_road.paragraphs[0]
    p.text = "📌 SÍNTESE DA APRESENTAÇÃO"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = TEAL
    p.space_after = Pt(14)
    
    p_t = tf_road.add_paragraph()
    p_t.text = "Pontos-Chave para o Gestor"
    p_t.font.size = Pt(26)
    p_t.font.bold = True
    p_t.font.color.rgb = WHITE
    p_t.space_after = Pt(20)
    
    highlights = [
        "✅ Modernização completa do fluxo de tramitação da NOVACAP",
        "✅ Transparência e rastreabilidade total de cada processo SEI",
        "✅ Dashboards em tempo real e exportações simplificadas (Excel/CSV/PDF)",
        "✅ Arquitetura segura, leve e pronta para evolução contínua"
    ]
    for h in highlights:
        p_r = tf_road.add_paragraph()
        p_r.text = h
        p_r.font.size = Pt(14)
        p_r.font.color.rgb = RGBColor(226, 232, 240)
        p_r.space_after = Pt(14)

    # Right Card - Contact & Thanks
    add_card(slide10, Inches(7.3), Inches(1.2), Inches(5.233), Inches(5.1), bg_color=RGBColor(24, 59, 107), border_color=TEAL)
    tb_c = slide10.shapes.add_textbox(Inches(7.5), Inches(1.5), Inches(4.833), Inches(4.5))
    tf_c = tb_c.text_frame
    tf_c.word_wrap = True
    
    p_th = tf_c.paragraphs[0]
    p_th.text = "Obrigado!"
    p_th.font.size = Pt(36)
    p_th.font.bold = True
    p_th.font.color.rgb = GOLD
    p_th.space_after = Pt(16)
    
    p_subth = tf_c.add_paragraph()
    p_subth.text = "Central de Relacionamento (CR)\nCompanhia Urbanizadora da Nova Capital do Brasil - NOVACAP"
    p_subth.font.size = Pt(15)
    p_subth.font.bold = True
    p_subth.font.color.rgb = WHITE
    p_subth.space_after = Pt(20)
    
    contacts = [
        "👤 Responsável: Anderson de Matos Guimarães",
        "🏛️ Órgão: NOVACAP / GDF",
        "📍 Brasília / DF - 2025/2026",
        "💬 Perguntas & Respostas (Q&A)"
    ]
    for c in contacts:
        p_cnt = tf_c.add_paragraph()
        p_cnt.text = c
        p_cnt.font.size = Pt(13)
        p_cnt.font.color.rgb = RGBColor(203, 213, 225)
        p_cnt.space_after = Pt(10)

    # Save presentation
    prs.save(output_path)
    print(f"Apresentação gerada com sucesso em: {output_path}")

if __name__ == "__main__":
    out_file = os.path.join(os.getcwd(), "Apresentacao_Sistema_CR_NOVACAP.pptx")
    create_novacap_presentation(out_file)
