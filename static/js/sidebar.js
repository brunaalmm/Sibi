// Controle da Sidebar
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const sidebarMinimize = document.getElementById('sidebarMinimize');
    const mainContent = document.getElementById('main-content');
    
    // Verificar estado salvo no localStorage
    const isMinimized = localStorage.getItem('sidebarMinimized') === 'true';
    
    // Aplicar estado salvo
    if (isMinimized) {
        sidebar.classList.add('minimized');
    }
    
    // Controle de minimizar/maximizar
    if (sidebarMinimize) {
        sidebarMinimize.addEventListener('click', function() {
            sidebar.classList.toggle('minimized');
            
            // Salvar estado no localStorage
            const isNowMinimized = sidebar.classList.contains('minimized');
            localStorage.setItem('sidebarMinimized', isNowMinimized);
            
            // Atualizar ícone
            updateMinimizeIcon();
        });
    }
    
    // Função para atualizar o ícone do botão
    function updateMinimizeIcon() {
        if (sidebarMinimize) {
            const icon = sidebarMinimize.querySelector('i');
            if (sidebar.classList.contains('minimized')) {
                icon.className = 'bi bi-chevron-right fs-3 text-white';
            } else {
                icon.className = 'bi bi-chevron-left fs-3 text-white';
            }
        }
    }
    
    // Inicializar ícone
    updateMinimizeIcon();
    
    // Fechar sidebar no mobile quando clicar em um link
    const navLinks = document.querySelectorAll('.sidebar .nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            // Apenas no mobile
            if (window.innerWidth <= 850) {
                sidebar.classList.remove('show');
                overlay.classList.remove('active');
            }
        });
    });
    
    // Ajustar sidebar na redimensionamento da tela
    window.addEventListener('resize', function() {
        if (window.innerWidth > 850) {
            sidebar.classList.remove('show');
            overlay.classList.remove('active');
        }
    });
});