from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, Agendamento, Livro, Usuario
from datetime import datetime, timedelta

agendamento_bp = Blueprint('agendamento', __name__)

# ================= AGENDAMENTO DE EMPRÉSTIMO =================
@agendamento_bp.route('/aluno/agendamento/emprestimo/<int:livro_id>')
def agendamento_emprestimo(livro_id):
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Aluno':
        flash('Acesso negado! Faça login como aluno.', 'error')
        return redirect(url_for('login'))
    
    livro = Livro.query.get_or_404(livro_id)
    
    if livro.quantidade <= 0:
        flash('Este livro não está disponível no momento.', 'error')
        return redirect(url_for('detalhes_livro', livro_id=livro_id))
    
    # Gerar datas disponíveis
    datas_disponiveis = []
    hoje = datetime.now().date()
    
    # ALTEREI O "1, 31" PARA "0, 31" PARA INCLUIR O DIA ATUAL NA LISTA DE DATAS MAS NÃO ESTÁ FUNCIONANDO

    for i in range(0, 31):
        data = hoje + timedelta(days=i)
        if data.weekday() < 5:  # Dias úteis
            datas_disponiveis.append({
                'data': data,
                'formatada': data.strftime('%d/%m/%Y'),
                'dia_semana': ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta'][data.weekday()]
            })
    
    return render_template('aluno/agendamento_emprestimo.html', 
                         livro=livro, 
                         datas_disponiveis=datas_disponiveis)

@agendamento_bp.route('/aluno/agendamento/devolucao/<int:agendamento_id>')
def agendamento_devolucao(agendamento_id):
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Aluno':
        flash('Acesso negado! Faça login como aluno.', 'error')
        return redirect(url_for('login'))
    
    agendamento_original = Agendamento.query.get_or_404(agendamento_id)
    livro = Livro.query.get(agendamento_original.livro_id)
    
    if agendamento_original.aluno_id != session.get('usuario_id'):
        flash('Acesso negado!', 'error')
        return redirect(url_for('agendamento.estante_aluno'))
    
    if agendamento_original.status != 'emprestado':
        flash('Só é possível agendar devolução de livros emprestados!', 'error')
        return redirect(url_for('agendamento.estante_aluno'))
    
    # Gerar datas para devolução
    datas_disponiveis = []
    hoje = datetime.now().date()
    
    for i in range(1, 8):  # Próximos 7 dias
        data = hoje + timedelta(days=i)
        if data.weekday() < 5:
            datas_disponiveis.append({
                'data': data,
                'formatada': data.strftime('%d/%m/%Y'),
                'dia_semana': ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta'][data.weekday()]
            })
    
    return render_template('aluno/agendamento_devolucao.html', 
                         agendamento_original=agendamento_original,
                         livro=livro,
                         datas_disponiveis=datas_disponiveis,
                         today=hoje)

@agendamento_bp.route('/aluno/agendamento/salvar', methods=['POST'])
def salvar_agendamento():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Aluno':
        return jsonify({'success': False, 'message': 'Acesso negado!'})
    
    tipo_agendamento = request.form.get('tipo_agendamento', 'emprestimo')
    
    if tipo_agendamento == 'emprestimo':
        return _salvar_agendamento_emprestimo()
    elif tipo_agendamento == 'devolucao':
        return _salvar_agendamento_devolucao()
    else:
        return jsonify({'success': False, 'message': 'Tipo de agendamento inválido!'})

def _salvar_agendamento_emprestimo():
    livro_id = request.form['livro_id']
    data_agendamento = request.form['data_agendamento']
    horario = request.form['horario']
    
    data_obj = datetime.strptime(data_agendamento, '%d/%m/%Y').date()
    livro = Livro.query.get(livro_id)
    
    if not livro:
        return jsonify({'success': False, 'message': 'Livro não encontrado!'})
    
    if livro.quantidade <= 0:
        return jsonify({'success': False, 'message': 'Este livro não está mais disponível!'})
    
    # Criar agendamento de empréstimo
    novo_agendamento = Agendamento(
        aluno_id=session.get('usuario_id'),
        livro_id=livro_id,
        data_agendamento=data_obj,
        horario=horario,
        status='pendente',
        tipo_agendamento='emprestimo'
    )
    
    db.session.add(novo_agendamento)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Agendamento de empréstimo realizado com sucesso!'})

def _salvar_agendamento_devolucao():
    agendamento_emprestimo_id = request.form['agendamento_emprestimo_id']
    data_agendamento = request.form['data_agendamento']
    horario = request.form['horario']
    
    agendamento_original = Agendamento.query.get_or_404(agendamento_emprestimo_id)
    
    if agendamento_original.aluno_id != session.get('usuario_id'):
        return jsonify({'success': False, 'message': 'Acesso negado!'})
    
    if agendamento_original.status != 'emprestado':
        return jsonify({'success': False, 'message': 'Este livro não está mais emprestado!'})
    
    data_obj = datetime.strptime(data_agendamento, '%d/%m/%Y').date()
    
    # ✅ CORREÇÃO: Atualizar o agendamento existente em vez de criar novo
    agendamento_original.data_agendamento = data_obj
    agendamento_original.horario = horario
    agendamento_original.status = 'devolucao_agendada'
    agendamento_original.tipo_agendamento = 'devolucao'
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Agendamento de devolução realizado com sucesso!'})

@agendamento_bp.route('/aluno/agenda')
def minha_agenda():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Aluno':
        flash('Acesso negado! Faça login como aluno.', 'error')
        return redirect(url_for('login'))
    
    agendamentos = Agendamento.query.filter_by(aluno_id=session.get('usuario_id')).order_by(Agendamento.data_agendamento.desc()).all()
    return render_template('aluno/agenda.html', agendamentos=agendamentos)

@agendamento_bp.route('/aluno/estante')
def estante_aluno():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Aluno':
        flash('Acesso negado! Faça login como aluno.', 'error')
        return redirect(url_for('login'))
    
    aluno_id = session.get('usuario_id')
    today = datetime.now().date()
    
    livros_emprestados = Agendamento.query.filter_by(
        aluno_id=aluno_id, 
        status='emprestado'
    ).order_by(Agendamento.data_devolucao_prevista.asc()).all()
    
    livros_pendentes = Agendamento.query.filter_by(
        aluno_id=aluno_id, 
        status='pendente'
    ).order_by(Agendamento.data_agendamento.asc()).all()
    
    # ✅ NOVO: Devoluções agendadas
    devolucoes_agendadas = Agendamento.query.filter_by(
        aluno_id=aluno_id, 
        status='devolucao_agendada'
    ).order_by(Agendamento.data_agendamento.asc()).all()
    
    livros_devolvidos = Agendamento.query.filter_by(
        aluno_id=aluno_id, 
        status='devolvido'
    ).order_by(Agendamento.data_devolucao_real.desc()).all()
    
    livros_atrasados = [a for a in livros_emprestados if a.data_devolucao_prevista < today]
    
    return render_template('aluno/estante.html',
                         livros_emprestados=livros_emprestados,
                         livros_pendentes=livros_pendentes,
                         devolucoes_agendadas=devolucoes_agendadas,
                         livros_devolvidos=livros_devolvidos,
                         livros_atrasados=livros_atrasados,
                         today=today)

@agendamento_bp.route('/aluno/emprestimo/<int:agendamento_id>/renovar', methods=['POST'])
def renovar_emprestimo(agendamento_id):
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Aluno':
        return jsonify({'success': False, 'message': 'Acesso negado!'})
    
    agendamento = Agendamento.query.get_or_404(agendamento_id)
    
    if agendamento.aluno_id != session.get('usuario_id'):
        return jsonify({'success': False, 'message': 'Acesso negado!'})
    
    if agendamento.status != 'emprestado':
        return jsonify({'success': False, 'message': 'Só é possível renovar livros emprestados!'})
    
    if agendamento.renovacoes >= 2:
        return jsonify({'success': False, 'message': 'Limite de renovações atingido!'})
    
    if agendamento.data_devolucao_prevista < datetime.now().date():
        return jsonify({'success': False, 'message': 'Não é possível renovar livros atrasados!'})
    
    # Renovar
    agendamento.data_devolucao_prevista = agendamento.data_devolucao_prevista + timedelta(days=7)
    agendamento.renovacoes += 1
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Empréstimo renovado com sucesso!'})

# ================= ROTAS DO BIBLIOTECÁRIO =================
@agendamento_bp.route('/bibliotecario/agenda')
def agenda_bibliotecario():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Bibliotecario':
        flash('Acesso negado! Faça login como bibliotecário.', 'error')
        return redirect(url_for('login'))
    
    unidade_bibliotecario = session.get('unidade')
    agendamentos = Agendamento.query.join(Livro).filter(
        Livro.unidade == unidade_bibliotecario
    ).order_by(Agendamento.data_agendamento.asc()).all()
    
    today = datetime.now().date()
    
    return render_template('bibliotecario/agenda_bibliotecario.html', 
                         agendamentos=agendamentos, 
                         today=today)

# ✅ NOVAS ROTAS PARA O BIBLIOTECÁRIO
@agendamento_bp.route('/bibliotecario/agendamento/<int:agendamento_id>/confirmar_emprestimo', methods=['POST'])
def confirmar_emprestimo(agendamento_id):
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Bibliotecario':
        return jsonify({'success': False, 'message': 'Acesso negado!'})
    
    agendamento = Agendamento.query.get_or_404(agendamento_id)
    
    if agendamento.status != 'pendente':
        return jsonify({'success': False, 'message': 'Agendamento já processado!'})
    
    # Confirmar empréstimo
    agendamento.status = 'emprestado'
    agendamento.data_emprestimo = datetime.utcnow()
    agendamento.data_devolucao_prevista = datetime.utcnow().date() + timedelta(days=7)
    
    # Decrementar quantidade do livro
    livro = Livro.query.get(agendamento.livro_id)
    if livro.quantidade > 0:
        livro.quantidade -= 1
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Empréstimo confirmado com sucesso!'})

@agendamento_bp.route('/bibliotecario/agendamento/<int:agendamento_id>/confirmar_devolucao', methods=['POST'])
def confirmar_devolucao(agendamento_id):
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Bibliotecario':
        return jsonify({'success': False, 'message': 'Acesso negado!'})
    
    agendamento = Agendamento.query.get_or_404(agendamento_id)
    
    if agendamento.status != 'devolucao_agendada':
        return jsonify({'success': False, 'message': 'Status inválido para devolução!'})
    
    # Confirmar devolução
    agendamento.status = 'devolvido'
    agendamento.data_devolucao_real = datetime.utcnow()
    
    # Incrementar quantidade do livro
    livro = Livro.query.get(agendamento.livro_id)
    livro.quantidade += 1
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Devolução confirmada com sucesso!'})

@agendamento_bp.route('/bibliotecario/agendamento/<int:agendamento_id>/cancelar', methods=['POST'])
def cancelar_agendamento(agendamento_id):
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Bibliotecario':
        return jsonify({'success': False, 'message': 'Acesso negado!'})
    
    agendamento = Agendamento.query.get_or_404(agendamento_id)
    
    if agendamento.status != 'pendente':
        return jsonify({'success': False, 'message': 'Só é possível cancelar agendamentos pendentes!'})
    
    # Cancelar agendamento
    agendamento.status = 'cancelado'
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Agendamento cancelado com sucesso!'})