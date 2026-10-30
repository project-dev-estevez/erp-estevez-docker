// Botón para mostrar/ocultar contraseña en las pantallas de acceso
// (iniciar sesión, restablecer contraseña, registro y cambio obligatorio de contraseña).
(function () {
    'use strict';

    const FORMS = '.oe_login_form, .oe_signup_form, .oe_reset_password_form';

    // Iconos de línea (ojo / ojo tachado) en el color del texto
    const ICON_SHOW = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.06 12.35a1 1 0 0 1 0-.7C3.42 8.1 7.36 5 12 5s8.58 3.1 9.94 6.65a1 1 0 0 1 0 .7C20.58 15.9 16.64 19 12 19s-8.58-3.1-9.94-6.65"/><circle cx="12" cy="12" r="3"/></svg>';
    const ICON_HIDE = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c4.64 0 8.58 3.1 9.94 6.65a1 1 0 0 1 0 .7 10.75 10.75 0 0 1-1.44 2.49"/><path d="M14.08 14.16a3 3 0 0 1-4.24-4.24"/><path d="M17.48 17.5A10.75 10.75 0 0 1 12 19c-4.64 0-8.58-3.1-9.94-6.65a1 1 0 0 1 0-.7 10.75 10.75 0 0 1 4.45-5.14"/><path d="m2 2 20 20"/></svg>';

    function setState(button, input, visible) {
        input.type = visible ? 'text' : 'password';
        button.innerHTML = visible ? ICON_HIDE : ICON_SHOW;
        button.setAttribute('aria-pressed', visible ? 'true' : 'false');
        const label = visible ? 'Ocultar contraseña' : 'Mostrar contraseña';
        button.setAttribute('aria-label', label);
        button.title = label;
    }

    function addToggle(input) {
        if (input.dataset.passwordToggle) {
            return;
        }
        input.dataset.passwordToggle = '1';

        // Envoltura propia para colocar el botón dentro del campo sin tocar la etiqueta
        const wrapper = document.createElement('span');
        wrapper.className = 'o_password_wrap';
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);
        input.classList.add('o_password_input');

        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'o_password_toggle';
        if (input.id) {
            button.setAttribute('aria-controls', input.id);
        }
        setState(button, input, false);

        // mousedown sin perder el foco ni la posición del cursor en el campo
        button.addEventListener('mousedown', (ev) => ev.preventDefault());
        button.addEventListener('click', () => {
            const position = input.selectionStart;
            setState(button, input, input.type === 'password');
            input.focus();
            if (position !== null) {
                input.setSelectionRange(position, position);
            }
        });
        wrapper.appendChild(button);
    }

    function setup() {
        document.querySelectorAll(FORMS).forEach((form) => {
            form.querySelectorAll('input[type="password"]').forEach(addToggle);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setup);
    } else {
        setup();
    }
})();
