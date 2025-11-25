function confirmarEmprestimo(agendamentoId) {
    if (confirm('Confirmar empréstimo deste livro?')) {
        fetch(`/bibliotecario/agendamento/${agendamentoId}/confirmar_emprestimo`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(data.message);
                location.reload();
            } else {
                alert('Erro: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            alert('Erro ao confirmar empréstimo');
        });
    }
}

function confirmarDevolucao(agendamentoId) {
    if (confirm('Confirmar devolução deste livro?')) {
        fetch(`/bibliotecario/agendamento/${agendamentoId}/confirmar_devolucao`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(data.message);
                location.reload();
            } else {
                alert('Erro: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            alert('Erro ao confirmar devolução');
        });
    }
}

function cancelarAgendamento(agendamentoId) {
    if (confirm('Cancelar este agendamento?')) {
        fetch(`/bibliotecario/agendamento/${agendamentoId}/cancelar`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(data.message);
                location.reload();
            } else {
                alert('Erro: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            alert('Erro ao cancelar agendamento');
        });
    }
}

// Filtros e busca
document.addEventListener('DOMContentLoaded', function() {
    const filtroStatus = document.getElementById('filtroStatus');
    const ordenarPor = document.getElementById('ordenarPor');
    const buscarInput = document.getElementById('buscarInput');
    
    if (filtroStatus) {
        filtroStatus.addEventListener('change', filtrarAgendamentos);
    }
    
    if (ordenarPor) {
        ordenarPor.addEventListener('change', filtrarAgendamentos);
    }
    
    if (buscarInput) {
        buscarInput.addEventListener('input', filtrarAgendamentos);
    }
});

function filtrarAgendamentos() {
    const statusFiltro = document.getElementById('filtroStatus').value;
    const ordenacao = document.getElementById('ordenarPor').value;
    const busca = document.getElementById('buscarInput').value.toLowerCase();
    
    const cards = document.querySelectorAll('.agendamento-card');
    
    cards.forEach(card => {
        const status = card.getAttribute('data-status');
        const aluno = card.getAttribute('data-aluno');
        const livro = card.getAttribute('data-livro');
        
        let mostrar = true;
        
        // Filtro por status
        if (statusFiltro !== 'todos' && status !== statusFiltro) {
            mostrar = false;
        }
        
        // Filtro por busca
        if (busca && !aluno.includes(busca) && !livro.includes(busca)) {
            mostrar = false;
        }
        
        card.style.display = mostrar ? 'block' : 'none';
    });
    
    // Ordenação (simplificada - em produção seria melhor no backend)
    ordenarCards(ordenacao);
}

function ordenarCards(ordenacao) {
    const container = document.getElementById('agendamentosContainer');
    const cards = Array.from(container.querySelectorAll('.agendamento-card'));
    
    cards.sort((a, b) => {
        const dataA = new Date(a.querySelector('.agendamento-dates p:first-child').textContent.split(': ')[1]);
        const dataB = new Date(b.querySelector('.agendamento-dates p:first-child').textContent.split(': ')[1]);
        const statusA = a.getAttribute('data-status');
        const statusB = b.getAttribute('data-status');
        
        switch (ordenacao) {
            case 'data_asc':
                return dataA - dataB;
            case 'data_desc':
                return dataB - dataA;
            case 'status':
                return statusA.localeCompare(statusB);
            default:
                return 0;
        }
    });
    
    // Reorganizar os cards no container
    cards.forEach(card => container.appendChild(card));
}