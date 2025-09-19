(function() {
    // Agregar estilos del widget
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://cdn.jsdelivr.net/npm/@n8n/chat/dist/style.css';
    document.head.appendChild(link);

    // Importar y lanzar el chat de n8n
    import('https://cdn.jsdelivr.net/npm/@n8n/chat/dist/chat.bundle.es.js')
        .then(({ createChat }) => {
            createChat({
                webhookUrl: 'https://n8n-estevez.gotdns.ch/webhook/02caa068-1311-47f9-b2e9-9ab9bd0436ea/chat',
                // 👇 Opcional: ajusta como quieras
                initialMessages: ["👋 Hola, soy tu asistente IA. ¿En qué te ayudo?"],
                mode: "float", // "float" o "fullscreen"
            });
        });
})();
