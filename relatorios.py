from flask import Blueprint, jsonify, session, render_template, flash, redirect, url_for
from models import db, Agendamento, Livro, Usuario
from sqlalchemy import func, extract, and_
from datetime import datetime, timedelta

relatorios_bp = Blueprint('relatorios', __name__)

def get_data_relatorios(unidade):
    """
    Função para buscar todos os dados necessários para os relatórios
    filtrados pela unidade do bibliotecário.
    """
    hoje = datetime.now().date()
    data_limite = hoje - timedelta(days=15)

    # 1. Empréstimos dos últimos 15 dias (Gráfico de Colunas/Tabela)
    # Contagem de empréstimos por dia nos últimos 15 dias
    emprestimos_15_dias = db.session.query(
        func.date(Agendamento.data_emprestimo).label('data'),
        func.count(Agendamento.id).label('total')
    ).join(Livro).filter(
        Livro.unidade == unidade,
        Agendamento.data_emprestimo >= data_limite,
        Agendamento.status == 'emprestado'
    ).group_by(
        func.date(Agendamento.data_emprestimo)
    ).order_by(
        func.date(Agendamento.data_emprestimo)
    ).all()

    # 2. Devoluções dos últimos 15 dias (Gráfico de Colunas/Tabela)
    # Contagem de devoluções por dia nos últimos 15 dias
    devolucoes_15_dias = db.session.query(
        func.date(Agendamento.data_devolucao_real).label('data'),
        func.count(Agendamento.id).label('total')
    ).join(Livro).filter(
        Livro.unidade == unidade,
        Agendamento.data_devolucao_real >= data_limite,
        Agendamento.status == 'devolvido'
    ).group_by(
        func.date(Agendamento.data_devolucao_real)
    ).order_by(
        func.date(Agendamento.data_devolucao_real)
    ).all()

    # 3. Top 5 livros mais emprestados da unidade (Gráfico de Coluna Vertical)
    # Contagem de todos os empréstimos (status 'emprestado' ou 'devolvido') por livro
    top_5_livros = db.session.query(
        Livro.titulo,
        func.count(Agendamento.id).label('total_emprestimos')
    ).join(Agendamento).filter(
        Livro.unidade == unidade,
        Agendamento.tipo_agendamento == 'emprestimo',
        Agendamento.status.in_(['emprestado', 'devolvido'])
    ).group_by(
        Livro.titulo
    ).order_by(
        func.count(Agendamento.id).desc()
    ).limit(5).all()

    # 4. Livros por gêneros mais emprestados (Gráfico de Pizza)
    # Contagem de todos os empréstimos por gênero
    generos_mais_emprestados = db.session.query(
        Livro.genero,
        func.count(Agendamento.id).label('total_emprestimos')
    ).join(Agendamento).filter(
        Livro.unidade == unidade,
        Agendamento.tipo_agendamento == 'emprestimo',
        Agendamento.status.in_(['emprestado', 'devolvido'])
    ).group_by(
        Livro.genero
    ).order_by(
        func.count(Agendamento.id).desc()
    ).all()

    # Formatando os dados para JSON
    data = {
        'emprestimos_15_dias': [{'data': str(e.data), 'total': e.total} for e in emprestimos_15_dias],
        'devolucoes_15_dias': [{'data': str(d.data), 'total': d.total} for d in devolucoes_15_dias],
        'top_5_livros': [{'titulo': t.titulo, 'total': t.total_emprestimos} for t in top_5_livros],
        'generos_mais_emprestados': [{'genero': g.genero, 'total': g.total_emprestimos} for g in generos_mais_emprestados]
    }

    return data

@relatorios_bp.route('/bibliotecario/relatorios')
def relatorios():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Bibliotecario':
        flash('Acesso negado! Faça login como bibliotecário.', 'error')
        return redirect(url_for('login'))
    
    # Filtrar relatórios por unidade
    unidade_bibliotecario = session.get('unidade')
    
    # Buscar dados do usuário para o template
    usuario = Usuario.query.get(session.get('usuario_id'))
    
    return render_template('bibliotecario/relatorios.html', 
                         unidade=unidade_bibliotecario,
                         user_data=usuario)

@relatorios_bp.route('/bibliotecario/api/relatorios', methods=['GET'])
def api_relatorios():
    if not session.get('logged_in') or session.get('tipo_usuario') != 'Bibliotecario':
        return jsonify({'error': 'Acesso negado'}), 403
    
    unidade = session.get('unidade')
    if not unidade:
        return jsonify({'error': 'Unidade do bibliotecário não encontrada na sessão'}), 400

    data = get_data_relatorios(unidade)
    return jsonify(data)