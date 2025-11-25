from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from models import db, bcrypt, Usuario, Login, Livro, Agendamento
from gerenciar_usuarios import gerenciar_usuarios_bp
from gerenciar_livros import gerenciar_livros_bp
from agendamento import agendamento_bp
from relatorios import relatorios_bp
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Senai%40118@localhost/sibi_biblioteca'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'

# Configurações para upload
app.config['UPLOAD_FOLDER'] = 'static/uploads/perfis'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

# Criar diretório de uploads se não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)
bcrypt.init_app(app)

# Registrar Blueprints
app.register_blueprint(gerenciar_usuarios_bp)
app.register_blueprint(gerenciar_livros_bp)
app.register_blueprint(agendamento_bp)
app.register_blueprint(relatorios_bp, url_prefix='/relatorios')

with app.app_context():
    db.create_all()

# Função para verificar extensões permitidas
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

# Context Processor para disponibilizar user_data em todos os templates
@app.context_processor
def inject_user_data():
    if session.get('logged_in') and session.get('usuario_id'):
        usuario = Usuario.query.get(session.get('usuario_id'))
        return {'user_data': usuario}
    return {'user_data': None}

# ================= ROTA RAIZ =================
@app.route('/')
def home():
    if session.get('logged_in'):
        # Se já está logado, vai direto para a home apropriada
        if session.get('tipo_usuario') == 'Bibliotecario':
            return redirect(url_for('home_bibliotecario'))
        else:
            return redirect(url_for('home_aluno'))
    return redirect(url_for('login'))

# ================= SPLASH SCREEN =================
@app.route('/splash')
def splash():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Determina para qual home redirecionar após o splash
    destino = 'home_bibliotecario' if session.get('tipo_usuario') == 'Bibliotecario' else 'home_aluno'
    destino_url = url_for(destino)
    
    return render_template('splash.html', destino_url=destino_url)

# ================= LOGIN =================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        tipo_usuario = request.form['tipo_usuario']
        
        user = Usuario.query.filter_by(email=email, tipo_usuario=tipo_usuario).first()
        
        if user and bcrypt.check_password_hash(user.senha, senha):
            session['logged_in'] = True
            session['usuario_id'] = user.id
            session['nome_completo'] = user.nome
            session['nome'] = user.nome
            session['tipo_usuario'] = user.tipo_usuario
            session['unidade'] = user.unidade
            session['email'] = user.email
            session['foto_perfil'] = user.foto_perfil
            
            login_registro = Login(usuario_id=user.id)
            db.session.add(login_registro)
            db.session.commit()
            
            # Em vez de redirect, renderiza a splash diretamente
            destino = 'home_bibliotecario' if user.tipo_usuario == 'Bibliotecario' else 'home_aluno'
            destino_url = url_for(destino)
            return render_template('splash.html', destino_url=destino_url)
        else:
            flash('Usuário ou senha inválidos', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

# ================= CADASTRO =================  
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    unidades = [
        "CE SESI 265 - Jd. Santo Alberto",
        "CE SESI 094 - Vila Clarice",
        "CE SESI 166 - Santa Terezinha",
        "CE SESI 221 - Parque Jaçatuba"
    ]
    
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        tipo_usuario = request.form['tipo_usuario']
        unidade = request.form['unidade']
        
        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            flash('Este email já está cadastrado!', 'error')
            return render_template('cadastro.html', unidades=unidades)
        
        senha_hash = bcrypt.generate_password_hash(senha).decode('utf-8')
        
        novo_usuario = Usuario(
            nome=nome,
            email=email,
            senha=senha_hash,
            tipo_usuario=tipo_usuario,
            unidade=unidade,
            foto_perfil=None
        )
        
        db.session.add(novo_usuario)
        db.session.commit()
        
        # ✅ MANTÉM: Mostra mensagem de sucesso no login
        flash('Usuário cadastrado com sucesso!', 'success')
        return redirect(url_for('login'))
    
    return render_template('cadastro.html', unidades=unidades)

# ================= PÁGINAS DO BIBLIOTECÁRIO =================
@app.route('/bibliotecario/home')
def home_bibliotecario():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Bibliotecario':
        flash('Acesso negado! Faça login como bibliotecário.', 'error')
        return redirect(url_for('login'))

    # Obter a unidade do bibliotecário logado
    unidade_bibliotecario = session.get('unidade')

    # TOTAL DE ALUNOS (apenas da mesma unidade)
    total_alunos = Usuario.query.filter_by(
        tipo_usuario="Aluno", 
        unidade=unidade_bibliotecario
    ).count()

    # TOTAL DE LIVROS (apenas da mesma unidade)
    total_livros = Livro.query.filter_by(unidade=unidade_bibliotecario).count()

    # TOTAL DE LIVROS EMPRESTADOS (apenas os livros DA UNIDADE que estão emprestados)
    total_emprestados = Agendamento.query\
        .join(Livro)\
        .filter(
            Agendamento.status == 'emprestado',
            Livro.unidade == unidade_bibliotecario
        )\
        .count()

    # ÚLTIMOS EMPRÉSTIMOS (todos os empréstimos - gerais)
    ultimos_emprestimos = (
        Agendamento.query
        .join(Livro)
        .join(Usuario)
        .filter(Agendamento.status == 'emprestado')
        .order_by(Agendamento.data_emprestimo.desc())
        .limit(5)
        .all()
    )

    # ATRASADOS (todos os atrasos - gerais)
    hoje = datetime.now().date()
    atrasados = (
        Agendamento.query
        .join(Livro)
        .join(Usuario)
        .filter(
            Agendamento.status == 'emprestado',
            Agendamento.data_devolucao_prevista < hoje
        )
        .all()
    )

    # Buscar dados completos do usuário para o template
    usuario = Usuario.query.get(session.get('usuario_id'))

    return render_template(
        'bibliotecario/home_bibliotecario.html',
        nome=session.get('nome_completo'),
        total_alunos=total_alunos,
        total_livros=total_livros,
        total_emprestados=total_emprestados,
        ultimos_emprestimos=ultimos_emprestimos,
        atrasados=atrasados,
        user_data=usuario  # Passar dados completos do usuário
    )

@app.route('/bibliotecario/livros')
def gerenciar_livros():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Bibliotecario':
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    # Passar a unidade para o blueprint de gerenciar livros
    session['unidade_bibliotecario'] = session.get('unidade')
    return redirect(url_for('gerenciar_livros.gerenciar_livros'))

@app.route('/bibliotecario/usuarios')
def gerenciar_usuarios():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Bibliotecario':
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    # Passar a unidade para o blueprint de gerenciar usuários
    session['unidade_bibliotecario'] = session.get('unidade')
    return redirect(url_for('gerenciar_usuarios.gerenciar_usuarios'))

@app.route('/bibliotecario/agenda')
def agenda_bibliotecario():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Bibliotecario':
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    # Passar a unidade para o blueprint de agendamento
    session['unidade_bibliotecario'] = session.get('unidade')
    return redirect(url_for('agendamento.agenda_bibliotecario'))

# ================= CONFIGURAÇÕES DO BIBLIOTECÁRIO =================
@app.route('/bibliotecario/configuracoes', methods=['GET', 'POST'])
def configuracoes_bibliotecario():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Bibliotecario':
        flash('Acesso negado! Faça login como bibliotecário.', 'error')
        return redirect(url_for('login'))

    usuario = Usuario.query.get(session.get('usuario_id'))

    if not usuario:
        flash("Usuário não encontrado.", "error")
        return redirect(url_for('logout'))

    if request.method == 'POST':
        novo_nome = request.form['nome']
        novo_email = request.form['email']
        senha_atual = request.form.get('senha_atual', "")
        nova_senha = request.form.get('senha', "")

        # Flags
        atualizou_info = False

        # FOTO
        if 'foto_perfil' in request.files:
            file = request.files['foto_perfil']
            if file and file.filename != '' and allowed_file(file.filename):
                if file.content_length > app.config['MAX_CONTENT_LENGTH']:
                    flash('Arquivo muito grande. Máximo 5MB.', 'error')
                    return render_template('bibliotecario/configuracoes_bibliotecario.html', usuario=usuario)

                filename = secure_filename(file.filename)
                unique_filename = f"{usuario.id}_{int(datetime.now().timestamp())}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

                file.save(filepath)
                usuario.foto_perfil = f"uploads/perfis/{unique_filename}"
                session['foto_perfil'] = usuario.foto_perfil
                atualizou_info = True

        # EMAIL ÚNICO
        email_existente = Usuario.query.filter(
            Usuario.email == novo_email,
            Usuario.id != usuario.id
        ).first()

        if email_existente:
            flash("Este e-mail já está cadastrado para outro usuário.", "error")
            return render_template('bibliotecario/configuracoes_bibliotecario.html', usuario=usuario)

        # SENHA
        if nova_senha.strip() != "":
            if senha_atual.strip() == "":
                flash("Digite a senha atual para alterar a senha.", "error")
                return render_template('bibliotecario/configuracoes_bibliotecario.html', usuario=usuario)

            if nova_senha == senha_atual:
                flash("A nova senha não pode ser igual à senha atual.", "error")
                return render_template('bibliotecario/configuracoes_bibliotecario.html', usuario=usuario)

            if not bcrypt.check_password_hash(usuario.senha, senha_atual):
                flash("Senha atual incorreta!", "error")
                return render_template('bibliotecario/configuracoes_bibliotecario.html', usuario=usuario)

            if len(nova_senha) < 3:
                flash("A nova senha deve ter pelo menos 3 caracteres.", "error")
                return render_template('bibliotecario/configuracoes_bibliotecario.html', usuario=usuario)

            usuario.senha = bcrypt.generate_password_hash(nova_senha).decode('utf-8')
            atualizou_info = True  # senha é tratada como atualização geral

        # NOME / EMAIL
        if usuario.nome != novo_nome or usuario.email != novo_email:
            usuario.nome = novo_nome
            usuario.email = novo_email
            atualizou_info = True

        db.session.commit()

        # Sessão
        session['nome'] = novo_nome
        session['nome_completo'] = novo_nome
        session['email'] = novo_email

        # MENSAGEM FINAL (SEMPRE UMA)
        if atualizou_info:
            flash("Informações atualizadas com sucesso!", "success")

        return redirect(url_for('configuracoes_bibliotecario'))

    return render_template('bibliotecario/configuracoes_bibliotecario.html', usuario=usuario)

@app.route('/bibliotecario/perfil')
def perfil_bibliotecario():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Bibliotecario':
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    usuario = Usuario.query.get(session.get('usuario_id'))
    return render_template('bibliotecario/perfil_bibliotecario.html', usuario=usuario)

@app.route('/debug/endpoints')
def debug_endpoints():
    endpoints = []
    for rule in app.url_map.iter_rules():
        endpoints.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'path': rule.rule
        })
    return jsonify(endpoints)

# ================= PÁGINAS DO ALUNO =================
@app.route('/aluno/home_aluno')
def home_aluno():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Aluno':
        flash('Acesso negado! Faça login como aluno.', 'error')
        return redirect(url_for('login'))
    
    # Buscar dados completos do usuário para o template
    usuario = Usuario.query.get(session.get('usuario_id'))
    
    # Buscar livros da unidade do aluno
    # Usamos o atributo 'unidade' do objeto 'usuario' para garantir a consistência
    unidade_aluno = usuario.unidade
    livros_unidade = Livro.query.filter_by(unidade=unidade_aluno).limit(4).all() # Limitar a 4 para exibição na home
    
    return render_template('aluno/home_aluno.html', 
                         nome=session.get('nome_completo'),
                         livros_unidade=livros_unidade,
                         user_data=usuario) # user_data já é injetado pelo context processor, mas mantive por segurança

@app.route('/aluno/catalogo')
def catalogo():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Aluno':
        flash('Acesso negado! Faça login como aluno.', 'error')
        return redirect(url_for('login'))
   
    livros = Livro.query.all()
    
    # Buscar dados do usuário para o template
    usuario = Usuario.query.get(session.get('usuario_id'))
    
    return render_template('aluno/catalogo.html', 
                         livros=livros,
                         user_data=usuario)

@app.route('/aluno/catalogo/<int:livro_id>')
def detalhes_livro(livro_id):
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Aluno':
        flash('Acesso negado! Faça login como aluno.', 'error')
        return redirect(url_for('login'))
   
    livro = Livro.query.get_or_404(livro_id)
   
    livro_emprestado_para_aluno = None
    if session.get('usuario_id'):
        livro_emprestado_para_aluno = Agendamento.query.filter_by(
            aluno_id=session.get('usuario_id'),
            livro_id=livro_id,
            status='emprestado'
        ).first()
   
    today = datetime.now().date()
    
    # Buscar dados do usuário para o template
    usuario = Usuario.query.get(session.get('usuario_id'))
   
    return render_template(
        'aluno/detalhes_livro.html',
        livro=livro,
        livro_emprestado_para_aluno=livro_emprestado_para_aluno,
        today=today,
        user_data=usuario
    )

@app.route('/aluno/agendamento/<int:livro_id>')
def agendamento_livro(livro_id):
    return redirect(url_for('agendamento.agendamento_emprestimo', livro_id=livro_id))

@app.route('/aluno/agenda')
def agenda():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Aluno':
        flash('Acesso negado! Faça login como aluno.', 'error')
        return redirect(url_for('login'))
    return redirect(url_for('agendamento.minha_agenda'))

@app.route('/aluno/estante')
def estante():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Aluno':
        flash('Acesso negado! Faça login como aluno.', 'error')
        return redirect(url_for('login'))
    return redirect(url_for('agendamento.estante_aluno'))

# ================= CONFIGURAÇÕES DO ALUNO =================
@app.route('/aluno/configuracoes', methods=['GET', 'POST'])
def configuracoes_aluno():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Aluno':
        flash('Acesso negado! Faça login como aluno.', 'error')
        return redirect(url_for('login'))

    usuario = Usuario.query.get(session.get('usuario_id'))

    if not usuario:
        flash("Usuário não encontrado.", "error")
        return redirect(url_for('logout'))

    unidades = [
        "CE SESI 265 - Jd. Santo Alberto",
        "CE SESI 094 - Vila Clarice",
        "CE SESI 166 - Santa Terezinha",
        "CE SESI 221 - Parque Jaçatuba"
    ]

    if request.method == 'POST':
        novo_nome = request.form['nome']
        novo_email = request.form['email']
        nova_unidade = request.form['unidade']
        senha_atual = request.form.get('senha_atual', "")
        nova_senha = request.form.get('senha', "")

        atualizou_info = False

        # FOTO
        if 'foto_perfil' in request.files:
            file = request.files['foto_perfil']
            if file and file.filename != '' and allowed_file(file.filename):
                if file.content_length > app.config['MAX_CONTENT_LENGTH']:
                    flash('Arquivo muito grande. Máximo 5MB.', 'error')
                    return render_template('aluno/configuracoes.html', usuario=usuario, unidades=unidades)

                filename = secure_filename(file.filename)
                unique_filename = f"{usuario.id}_{int(datetime.now().timestamp())}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

                file.save(filepath)
                usuario.foto_perfil = f"uploads/perfis/{unique_filename}"
                session['foto_perfil'] = usuario.foto_perfil
                atualizou_info = True

        # NOME EXISTENTE
        nome_existente = Usuario.query.filter(
            Usuario.nome == novo_nome,
            Usuario.id != usuario.id
        ).first()
        if nome_existente:
            flash("Este nome já está sendo usado por outro usuário.", "error")
            return render_template('aluno/configuracoes.html', usuario=usuario, unidades=unidades)

        # EMAIL EXISTENTE
        email_existente = Usuario.query.filter(
            Usuario.email == novo_email,
            Usuario.id != usuario.id
        ).first()
        if email_existente:
            flash("Este e-mail já está cadastrado para outro usuário.", "error")
            return render_template('aluno/configuracoes.html', usuario=usuario, unidades=unidades)

        # SENHA
        if nova_senha.strip() != "":
            if senha_atual.strip() == "":
                flash("Digite a senha atual para alterar a senha.", "error")
                return render_template('aluno/configuracoes.html', usuario=usuario, unidades=unidades)

            if nova_senha == senha_atual:
                flash("A nova senha não pode ser igual à senha atual.", "error")
                return render_template('aluno/configuracoes.html', usuario=usuario, unidades=unidades)

            if not bcrypt.check_password_hash(usuario.senha, senha_atual):
                flash("Senha atual incorreta!", "error")
                return render_template('aluno/configuracoes.html', usuario=usuario, unidades=unidades)

            if len(nova_senha) < 3:
                flash("A nova senha deve ter pelo menos 3 caracteres.", "error")
                return render_template('aluno/configuracoes.html', usuario=usuario, unidades=unidades)

            usuario.senha = bcrypt.generate_password_hash(nova_senha).decode('utf-8')
            atualizou_info = True

        # NOME/EMAIL/UNIDADE
        if usuario.nome != novo_nome or usuario.email != novo_email or usuario.unidade != nova_unidade:
            usuario.nome = novo_nome
            usuario.email = novo_email
            usuario.unidade = nova_unidade
            atualizou_info = True

        db.session.commit()

        # Sessão
        session['nome'] = novo_nome
        session['nome_completo'] = novo_nome
        session['email'] = novo_email
        session['unidade'] = nova_unidade

        if atualizou_info:
            flash("Informações atualizadas com sucesso!", "success")

        return redirect(url_for('configuracoes_aluno'))

    return render_template('aluno/configuracoes.html', usuario=usuario, unidades=unidades)

@app.route('/aluno/perfil')
def perfil_aluno():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Aluno':
        flash('Acesso negado! Faça login como aluno.', 'error')
        return redirect(url_for('login'))
    usuario = Usuario.query.get(session.get('usuario_id'))
    return render_template('aluno/perfil_aluno.html', usuario=usuario)

# ================= LOGOUT =================
@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('login'))

# ================= MAIN =================
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5001, use_reloader=False)