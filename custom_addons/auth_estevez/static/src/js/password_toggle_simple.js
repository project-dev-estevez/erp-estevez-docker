// Password toggle functionality for Odoo login
(function() {
    'use strict';
    
    let setupAttempts = 0;
    const maxAttempts = 10;
    
    function setupPasswordToggle() {
        setupAttempts++;
        
        const passwordField = document.querySelector('input[name="password"]');
        
        if (!passwordField) {
            if (setupAttempts < maxAttempts) {
                setTimeout(setupPasswordToggle, 500);
            }
            return;
        }
        
        const container = passwordField.parentElement;
        let toggleBtn = container.querySelector('.password-toggle-btn');
        
        if (toggleBtn) {
            toggleBtn.remove();
        }
        
        // Preparar el contenedor
        container.style.position = 'relative';
        passwordField.style.paddingRight = '45px';
        
        // Crear el botón
        toggleBtn = document.createElement('button');
        toggleBtn.type = 'button';
        toggleBtn.className = 'password-toggle-btn';
        toggleBtn.innerHTML = '👁️'; // Usar emoji en lugar de FontAwesome
        toggleBtn.setAttribute('aria-label', 'Mostrar contraseña');
        toggleBtn.style.cssText = `
            position: absolute !important;
            right: 10px !important;
            top: 50% !important;
            transform: translateY(7%) !important;
            border: none !important;
            background: rgba(255,255,255,0.8) !important;
            cursor: pointer !important;
            padding: 5px !important;
            color: #6c757d !important;
            font-size: 16px !important;
            z-index: 1000 !important;
            min-width: 30px !important;
            height: 30px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            border-radius: 4px !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
        `;
        
        // Función para manejar el toggle
        function handleToggle(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const currentField = document.querySelector('input[name="password"]');
            if (currentField) {
                // Guardar la posición actual del cursor
                const cursorPosition = currentField.selectionStart;
                const wasPassword = currentField.type === 'password';
                const newType = wasPassword ? 'text' : 'password';
                
                // Cambiar el tipo del input
                currentField.type = newType;
                
                // Restaurar la posición del cursor
                setTimeout(() => {
                    currentField.setSelectionRange(cursorPosition, cursorPosition);
                    currentField.focus();
                }, 10);
                
                // Cambiar el emoji
                toggleBtn.innerHTML = wasPassword ? '🙈' : '👁️';
                
                // Feedback visual
                const originalColor = toggleBtn.style.color;
                const originalBackground = toggleBtn.style.background;
                
                toggleBtn.style.color = '#007bff';
                toggleBtn.style.background = 'rgba(0, 123, 255, 0.1)';
                
                setTimeout(() => {
                    toggleBtn.style.color = originalColor;
                    toggleBtn.style.background = originalBackground;
                }, 150);
                
                toggleBtn.setAttribute('aria-label', wasPassword ? 'Ocultar contraseña' : 'Mostrar contraseña');
            }
        }
        
        // Agregar eventos
        toggleBtn.addEventListener('click', handleToggle);
        toggleBtn.addEventListener('mousedown', function(e) {
            e.preventDefault();
            e.stopPropagation();
        });
        
        // Insertar el botón
        container.appendChild(toggleBtn);
    }
    
    // Inicializar
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupPasswordToggle);
    } else {
        setupPasswordToggle();
    }
    
    window.addEventListener('load', setupPasswordToggle);
    
    // Observer para cambios dinámicos
    const observer = new MutationObserver(function(mutations) {
        for (const mutation of mutations) {
            if (mutation.type === 'childList') {
                for (const node of mutation.addedNodes) {
                    if (node.nodeType === 1) {
                        if ((node.matches && node.matches('input[name="password"]')) ||
                            (node.querySelector && node.querySelector('input[name="password"]'))) {
                            setTimeout(setupPasswordToggle, 100);
                            return;
                        }
                    }
                }
            }
        }
    });
    
    if (document.body) {
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
})();
