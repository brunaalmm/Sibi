DROP DATABASE IF EXISTS sibi_biblioteca;
CREATE DATABASE sibi_biblioteca;
USE sibi_biblioteca;

CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    senha VARCHAR(100) NOT NULL,
    tipo_usuario ENUM('Bibliotecario', 'Aluno') NOT NULL,
    unidade VARCHAR(255) NOT NULL,
    foto_perfil VARCHAR(300) NULL
);

CREATE TABLE logins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    data_login DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE TABLE livros (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    autor VARCHAR(150) NOT NULL,
    isbn VARCHAR(20) NOT NULL,
    genero VARCHAR(100) NOT NULL,
    descricao TEXT,
    quantidade INT NOT NULL DEFAULT 1,
    unidade VARCHAR(200) NOT NULL,
    capa VARCHAR(300),
    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (isbn)
);

CREATE TABLE agendamentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aluno_id INT NOT NULL,
    livro_id INT NOT NULL,
    data_agendamento DATE NOT NULL,
    horario VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'pendente',
    data_emprestimo DATETIME,
    data_devolucao_prevista DATE,
    data_devolucao_real DATETIME,
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    renovacoes INT DEFAULT 0,
    tipo_agendamento VARCHAR(20) DEFAULT 'emprestimo',
    agendamento_original_id INT NULL
);

ALTER TABLE agendamentos
ADD CONSTRAINT agendamentos_fk_usuario
FOREIGN KEY (aluno_id) REFERENCES usuarios(id)
ON DELETE CASCADE;

ALTER TABLE agendamentos
ADD CONSTRAINT agendamentos_fk_livro
FOREIGN KEY (livro_id) REFERENCES livros(id)
ON DELETE RESTRICT;

ALTER TABLE agendamentos
ADD CONSTRAINT agendamentos_fk_original
FOREIGN KEY (agendamento_original_id) REFERENCES agendamentos(id)
ON DELETE SET NULL;