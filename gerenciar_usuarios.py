from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Usuario
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

gerenciar_usuarios_bp = Blueprint('gerenciar_usuarios', __name__)

@gerenciar_usuarios_bp.route('/bibliotecario/gerenciar_usuarios')
def gerenciar_usuarios():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Bibliotecario':
        flash('Acesso negado! Faça login como bibliotecário.', 'error')
        return redirect(url_for('login'))
    
    # Buscar apenas usuários da mesma unidade do bibliotecário logado
    unidade_bibliotecario = session.get('unidade')
    usuarios_lista = Usuario.query.filter_by(unidade=unidade_bibliotecario).all()
    
    return render_template('bibliotecario/gerenciar_usuarios.html', usuarios=usuarios_lista)

@gerenciar_usuarios_bp.route('/bibliotecario/usuarios/novo')
def novo_usuario():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Bibliotecario':
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    unidades = [
        "CE SESI 265 - Jd. Santo Alberto",
        "CE SESI 094 - Vila Clarice",
        "CE SESI 166 - Santa Terezinha",
        "CE SESI 221 - Parque Jaçatuba"
    ]
    
    return render_template('bibliotecario/usuario_form.html', usuario=None, unidades=unidades)

@gerenciar_usuarios_bp.route('/bibliotecario/usuarios/salvar', methods=['POST'])
def salvar_usuario():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Bibliotecario':
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    nome = request.form['nome']
    email = request.form['email']
    senha = request.form['senha']
    tipo_usuario = request.form['tipo_usuario']
    unidade = request.form['unidade']
    
    # Verificar se email já existe
    usuario_existente = Usuario.query.filter_by(email=email).first()
    if usuario_existente:
        flash('Este email já está cadastrado!', 'error')
        unidades = [
            "CE SESI 265 - Jd. Santo Alberto",
            "CE SESI 094 - Vila Clarice",
            "CE SESI 166 - Santa Terezinha",
            "CE SESI 221 - Parque Jaçatuba"
        ]
        return render_template('bibliotecario/usuario_form.html', usuario=None, unidades=unidades)
    
    senha_hash = bcrypt.generate_password_hash(senha).decode('utf-8')
    
    novo_usuario = Usuario(
        nome=nome,
        email=email,
        senha=senha_hash,
        tipo_usuario=tipo_usuario,
        unidade=unidade
    )
    
    db.session.add(novo_usuario)
    db.session.commit()
    
    flash('Usuário cadastrado com sucesso!', 'success')
    return redirect(url_for('gerenciar_usuarios.gerenciar_usuarios'))

@gerenciar_usuarios_bp.route('/bibliotecario/usuarios/editar/<int:id>')
def editar_usuario(id):
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Bibliotecario':
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    usuario = Usuario.query.get_or_404(id)
    
    # Verificar se o usuário pertence à mesma unidade do bibliotecário
    if usuario.unidade != session.get('unidade'):
        flash('Acesso negado! Você só pode editar usuários da sua unidade.', 'error')
        return redirect(url_for('gerenciar_usuarios.gerenciar_usuarios'))
    
    unidades = [
        "CE SESI 265 - Jd. Santo Alberto",
        "CE SESI 094 - Vila Clarice",
        "CE SESI 166 - Santa Terezinha",
        "CE SESI 221 - Parque Jaçatuba"
    ]
    
    return render_template('bibliotecario/usuario_form.html', usuario=usuario, unidades=unidades)

@gerenciar_usuarios_bp.route('/bibliotecario/usuarios/atualizar', methods=['POST'])
def atualizar_usuario():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Bibliotecario':
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    id = request.form['id']
    usuario = Usuario.query.get_or_404(id)
    
    # Verificar se o usuário pertence à mesma unidade do bibliotecário
    if usuario.unidade != session.get('unidade'):
        flash('Acesso negado! Você só pode editar usuários da sua unidade.', 'error')
        return redirect(url_for('gerenciar_usuarios.gerenciar_usuarios'))
    
    usuario.nome = request.form['nome']
    usuario.email = request.form['email']
    usuario.tipo_usuario = request.form['tipo_usuario']
    usuario.unidade = request.form['unidade']
    
    # Apenas atualiza a senha se preenchida
    if request.form['senha']:
        usuario.senha = bcrypt.generate_password_hash(request.form['senha']).decode('utf-8')
    
    db.session.commit()
    flash('Usuário atualizado com sucesso!', 'success')
    return redirect(url_for('gerenciar_usuarios.gerenciar_usuarios'))

@gerenciar_usuarios_bp.route('/bibliotecario/usuarios/excluir/<int:id>')
def excluir_usuario(id):
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Bibliotecario':
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    usuario = Usuario.query.get_or_404(id)
    
    # Verificar se o usuário pertence à mesma unidade do bibliotecário
    if usuario.unidade != session.get('unidade'):
        flash('Acesso negado! Você só pode excluir usuários da sua unidade.', 'error')
        return redirect(url_for('gerenciar_usuarios.gerenciar_usuarios'))
    
    # Não permitir excluir a si mesmo
    if usuario.id == session.get('usuario_id'):
        flash('Você não pode excluir sua própria conta!', 'error')
        return redirect(url_for('gerenciar_usuarios.gerenciar_usuarios'))
    
    db.session.delete(usuario)
    db.session.commit()
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('gerenciar_usuarios.gerenciar_usuarios'))