/** @odoo-module **/

import { Component, useState, onMounted, useRef } from "@odoo/owl";

console.log('Password toggle OWL script loaded');

// Función para inicializar el toggle fuera del contexto de OWL
function initPasswordToggleVanilla() {
    console.log('=== Initializing Vanilla Password Toggle ===');
    
    function setupPasswordToggle() {
        const passwordField = document.querySelector('input[name="password"]');
        console.log('Password field found:', passwordField);
        
        if (passwordField) {
            const container = passwordField.parentElement;
            
            // Verificar si ya existe el botón
            let toggleBtn = container.querySelector('.password-toggle-btn');
            
            if (!toggleBtn) {
                console.log('Creating password toggle button...');
                
                // Agregar clases
                container.classList.add('password-toggle-container');
                passwordField.classList.add('password-field');
                
                // Crear el botón
                toggleBtn = document.createElement('button');
                toggleBtn.type = 'button';
                toggleBtn.className = 'password-toggle-btn';
                toggleBtn.innerHTML = '<i class="fa fa-eye"></i>';
                toggleBtn.setAttribute('aria-label', 'Mostrar contraseña');
                
                // Insertar el botón
                container.appendChild(toggleBtn);
                console.log('Toggle button created and added');
            }
            
            // Configurar el evento (siempre, para asegurar que funcione)
            const newToggleBtn = toggleBtn.cloneNode(true);
            toggleBtn.parentNode.replaceChild(newToggleBtn, toggleBtn);
            
            newToggleBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log('=== PASSWORD TOGGLE CLICKED ===');
                
                const currentPasswordField = document.querySelector('input[name="password"]');
                if (currentPasswordField) {
                    const newType = currentPasswordField.type === 'password' ? 'text' : 'password';
                    currentPasswordField.type = newType;
                    console.log('Password type changed to:', newType);
                    
                    // Cambiar el icono
                    const icon = newToggleBtn.querySelector('i');
                    if (icon) {
                        if (newType === 'text') {
                            icon.className = 'fa fa-eye-slash';
                            newToggleBtn.setAttribute('aria-label', 'Ocultar contraseña');
                        } else {
                            icon.className = 'fa fa-eye';
                            newToggleBtn.setAttribute('aria-label', 'Mostrar contraseña');
                        }
                        console.log('Icon updated:', icon.className);
                    }
                } else {
                    console.error('Password field not found during toggle!');
                }
            });
            
            console.log('Event listener configured');
            return true;
        }
        return false;
    }
    
    // Intentar múltiples veces con diferentes delays
    const attempts = [0, 100, 500, 1000, 2000, 3000];
    let attemptCount = 0;
    
    function trySetup() {
        if (attemptCount < attempts.length) {
            setTimeout(() => {
                console.log(`Setup attempt ${attemptCount + 1}`);
                const success = setupPasswordToggle();
                if (!success) {
                    attemptCount++;
                    trySetup();
                } else {
                    console.log('Password toggle setup successful!');
                }
            }, attempts[attemptCount]);
        } else {
            console.warn('Failed to setup password toggle after all attempts');
        }
    }
    
    trySetup();
    
    // Observer para cambios dinámicos
    const observer = new MutationObserver(function(mutations) {
        let shouldCheck = false;
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                for (let node of mutation.addedNodes) {
                    if (node.nodeType === 1 && (
                        node.querySelector && node.querySelector('input[name="password"]') ||
                        node.matches && node.matches('input[name="password"]')
                    )) {
                        shouldCheck = true;
                        break;
                    }
                }
            }
        });
        
        if (shouldCheck) {
            console.log('DOM mutation detected, re-checking password toggle');
            setTimeout(setupPasswordToggle, 100);
        }
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPasswordToggleVanilla);
} else {
    initPasswordToggleVanilla();
}

// También inicializar cuando la página esté completamente cargada
window.addEventListener('load', initPasswordToggleVanilla);

// Exportar para compatibilidad con módulos
export default {
    initPasswordToggleVanilla
};
