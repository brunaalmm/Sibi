from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime

db = SQLAlchemy()
bcrypt = Bcrypt()

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    tipo_usuario = db.Column(db.Enum('Bibliotecario', 'Aluno'), nullable=False)
    unidade = db.Column(db.String(255), nullable=False)
    foto_perfil = db.Column(db.String(300), nullable=True)
    
    logins = db.relationship('Login', backref='usuario', lazy=True, cascade="all, delete-orphan")
    agendamentos = db.relationship('Agendamento', backref='aluno', lazy=True, cascade="all, delete-orphan")

class Login(db.Model):
    __tablename__ = "logins"
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    data_login = db.Column(db.DateTime, default=datetime.utcnow)

class Livro(db.Model):
    __tablename__ = "livros"
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    autor = db.Column(db.String(150), nullable=False)
    isbn = db.Column(db.String(20), nullable=False, unique=True)
    genero = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    quantidade = db.Column(db.Integer, nullable=False, default=1)
    unidade = db.Column(db.String(200), nullable=False)
    capa = db.Column(db.String(300))
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    agendamentos = db.relationship('Agendamento', backref='livro', lazy=True)

class Agendamento(db.Model):
    __tablename__ = "agendamentos"
    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    livro_id = db.Column(db.Integer, db.ForeignKey('livros.id', ondelete='RESTRICT'), nullable=False)
    usuario = db.relationship('Usuario', backref='agendamentos_usuario', lazy=True)
    data_agendamento = db.Column(db.Date, nullable=False)
    horario = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pendente')  
    tipo_agendamento = db.Column(db.String(20), default='emprestimo')
    agendamento_original_id = db.Column(db.Integer, db.ForeignKey('agendamentos.id', ondelete='SET NULL'), nullable=True)
    data_emprestimo = db.Column(db.DateTime)
    data_devolucao_prevista = db.Column(db.Date)
    data_devolucao_real = db.Column(db.DateTime)
    renovacoes = db.Column(db.Integer, default=0)  
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)