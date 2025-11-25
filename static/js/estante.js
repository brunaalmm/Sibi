// static/js/estante.js
function renovarEmprestimo(agendamentoId) {
    if (confirm('Deseja renovar o empréstimo deste livro por mais 7 dias?\n\nVocê pode renovar até 2 vezes por livro.')) {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/aluno/emprestimo/' + agendamentoId + '/renovar', true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        
        xhr.onload = function() {
            if (xhr.status === 200) {
                const data = JSON.parse(xhr.responseText);
                if (data.success) {
                    alert('Empréstimo renovado com sucesso!');
                    location.reload();
                } else {
                    alert('Erro: ' + data.message);
                }
            } else {
                alert('Erro na requisição. Status: ' + xhr.status);
            }
        };
        
        xhr.onerror = function() {
            alert('Erro de conexão.');
        };
        
        xhr.send();
    }
}

// Outras funções relacionadas à estante podem ser adicionadas aqui