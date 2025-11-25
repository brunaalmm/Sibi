from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Livro, Agendamento
from sqlalchemy.exc import IntegrityError
import os
from werkzeug.utils import secure_filename

gerenciar_livros_bp = Blueprint('gerenciar_livros', __name__)

# Configurações para upload de imagens
UPLOAD_FOLDER = 'static/uploads/capas'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@gerenciar_livros_bp.route('/bibliotecario/gerenciar_livros')
def gerenciar_livros():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Bibliotecario':
        flash('Acesso negado! Faça login como bibliotecário.', 'error')
        return redirect(url_for('login'))
    
    unidade_bibliotecario = session.get('unidade')
    livros_lista = Livro.query.filter_by(unidade=unidade_bibliotecario).all()
    
    return render_template('bibliotecario/gerenciar_livros.html', livros=livros_lista)

@gerenciar_livros_bp.route('/bibliotecario/livros/novo')
def novo_livro():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Bibliotecario':
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    unidade_bibliotecario = session.get('unidade')
    generos = [
        "Romance", "Aventura", "Mistério", "Fantasia", "Ficção Científica", "Poesia",
        "Terror", "Comédia", "Biografia", "Infantil", "Juvenil"
    ]
    
    return render_template('bibliotecario/livro_form.html', livro=None, unidade_bibliotecario=unidade_bibliotecario, generos=generos)

@gerenciar_livros_bp.route('/bibliotecario/livros/salvar', methods=['POST'])
def salvar_livro():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Bibliotecario':
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    titulo = request.form.get('titulo', '').strip()
    autor = request.form.get('autor', '').strip()
    isbn = request.form.get('isbn', '').strip()
    genero = request.form.get('genero', '').strip()
    descricao = request.form.get('descricao', '')
    try:
        quantidade = int(request.form.get('quantidade', 1))
    except ValueError:
        quantidade = 1
    unidade = session.get('unidade')
    
    # Verificar campos mínimos
    if not titulo or not autor or not isbn:
        flash('Título, autor e ISBN são obrigatórios.', 'error')
        return redirect(url_for('gerenciar_livros.novo_livro'))
    
    # Verificar se ISBN já existe
    livro_existente = Livro.query.filter_by(isbn=isbn).first()
    if livro_existente:
        flash('Este ISBN já está cadastrado!', 'error')
        return redirect(url_for('gerenciar_livros.novo_livro'))
    
    # Processar upload da capa
    capa_filename = None
    if 'capa' in request.files:
        file = request.files['capa']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            capa_filename = filename
    
    novo_livro = Livro(
        titulo=titulo,
        autor=autor,
        isbn=isbn,
        genero=genero,
        descricao=descricao,
        quantidade=quantidade,
        unidade=unidade,
        capa=capa_filename
    )
    
    db.session.add(novo_livro)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash('Erro ao salvar: ISBN já existente (condição de corrida).', 'error')
        return redirect(url_for('gerenciar_livros.novo_livro'))
    
    flash('Livro cadastrado com sucesso!', 'success')
    return redirect(url_for('gerenciar_livros.gerenciar_livros'))

@gerenciar_livros_bp.route('/bibliotecario/livros/editar/<int:id>')
def editar_livro(id):
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Bibliotecario':
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    livro = Livro.query.get_or_404(id)
    if livro.unidade != session.get('unidade'):
        flash('Acesso negado! Você só pode editar livros da sua unidade.', 'error')
        return redirect(url_for('gerenciar_livros.gerenciar_livros'))
    
    unidade_bibliotecario = session.get('unidade')
    generos = [
        "Romance", "Aventura", "Mistério", "Fantasia", "Ficção Científica", "Poesia",
        "Terror", "Comédia", "Biografia", "Infantil", "Juvenil"
    ]
    
    return render_template('bibliotecario/livro_form.html', livro=livro, unidade_bibliotecario=unidade_bibliotecario, generos=generos)

@gerenciar_livros_bp.route('/bibliotecario/livros/atualizar', methods=['POST'])
def atualizar_livro():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Bibliotecario':
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    id = request.form.get('id')
    livro = Livro.query.get_or_404(id)
    if livro.unidade != session.get('unidade'):
        flash('Acesso negado! Você só pode editar livros da sua unidade.', 'error')
        return redirect(url_for('gerenciar_livros.gerenciar_livros'))
    
    novo_isbn = request.form.get('isbn', '').strip()
    # Se o ISBN mudou, verificar duplicidade
    if novo_isbn and novo_isbn != livro.isbn:
        if Livro.query.filter(Livro.isbn == novo_isbn, Livro.id != livro.id).first():
            flash('Este ISBN já pertence a outro livro!', 'error')
            return redirect(url_for('gerenciar_livros.editar_livro', id=livro.id))
        livro.isbn = novo_isbn
    
    livro.titulo = request.form.get('titulo', livro.titulo)
    livro.autor = request.form.get('autor', livro.autor)
    livro.genero = request.form.get('genero', livro.genero)
    livro.descricao = request.form.get('descricao', livro.descricao)
    try:
        livro.quantidade = int(request.form.get('quantidade', livro.quantidade))
    except ValueError:
        pass
    
    # Processar upload da nova capa
    if 'capa' in request.files:
        file = request.files['capa']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            livro.capa = filename
    
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash('Erro ao atualizar: ISBN duplicado.', 'error')
        return redirect(url_for('gerenciar_livros.editar_livro', id=livro.id))
    
    flash('Livro atualizado com sucesso!', 'success')
    return redirect(url_for('gerenciar_livros.gerenciar_livros'))

@gerenciar_livros_bp.route('/bibliotecario/livros/excluir/<int:id>', methods=['POST', 'GET'])
def excluir_livro(id):
    """
    Se houver qualquer agendamento registrado para o livro, NÃO alteramos nada no DB — apenas informamos o usuário.
    """
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Bibliotecario':
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    livro = Livro.query.get_or_404(id)
    if livro.unidade != session.get('unidade'):
        flash('Acesso negado! Você só pode excluir livros da sua unidade.', 'error')
        return redirect(url_for('gerenciar_livros.gerenciar_livros'))
    
    # Contar qualquer agendamento para esse livro
    agendamento_count = Agendamento.query.filter_by(livro_id=id).count()
    if agendamento_count > 0:
        # NÃO ALTERAR NADA NO BANCO — só avisar
        flash('Este livro não pode ser apagado pois possui agendamentos registrados.', 'error')
        return redirect(url_for('gerenciar_livros.gerenciar_livros'))
    
    # Sem agendamentos: pode excluir com segurança
    db.session.delete(livro)
    db.session.commit()
    flash('Livro excluído com sucesso!', 'success')
    return redirect(url_for('gerenciar_livros.gerenciar_livros'))