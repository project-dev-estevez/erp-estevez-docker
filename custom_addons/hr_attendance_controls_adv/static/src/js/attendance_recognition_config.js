/** @odoo-module **/

// 🔧 CONFIGURACIÓN CENTRALIZADA PARA RECONOCIMIENTO FACIAL
export const FACE_DETECTION_CONFIG = {
    // Configuración de detección de sonrisa
    SMILE: {
        HAPPINESS_THRESHOLD: 0.6,        // Umbral mínimo de felicidad (0-1)
        TIME_INCREMENT: 0.2,             // Incremento por detección (segundos)
        REQUIRED_DURATION: 10,           // Duración total requerida (segundos)
        DETECTION_INTERVAL: 200,         // Intervalo entre detecciones (ms)
    },
    
    // Configuración de reconocimiento facial
    RECOGNITION: {
        MAX_DESCRIPTOR_DISTANCE: 0.45,   // Distancia máxima para descriptores
        MAX_MATCH_DISTANCE: 0.5,         // Distancia máxima para matches válidos
        MIN_MATCH_COUNT: 2,              // Mínimo de matches consecutivos
        DETECTION_INTERVAL: 200,         // Intervalo entre detecciones (ms)
        RETRY_DELAY: 500,                // Delay para reintentos (ms)
    },
    
    // Configuración de captura de imagen
    IMAGE_CAPTURE: {
        FACE_PADDING: 100,               // Padding alrededor del rostro (px)
        IMAGE_FORMAT: "image/jpeg",      // Formato de imagen
        BASE64_REGEX: /^data:image\/(png|jpg|jpeg);base64,/, // Regex para limpiar base64
    },
    
    // Configuración de UI
    UI: {
        SMILE_COMPLETION_DELAY: 1000,    // Delay antes del reconocimiento (ms)
        PROGRESS_MAX_PERCENT: 100,       // Porcentaje máximo de progreso
    },
};

// 📝 MENSAJES DE LA APLICACIÓN
export const FACE_DETECTION_MESSAGES = {
    SMILE_SUCCESS: "¡Excelente! Sonrisa detectada correctamente 😁",
    HTTPS_WARNING: "Error HTTPS: ¡La cámara web solo funciona con conexiones HTTPS! Tu instancia de Odoo debe estar configurada en modo HTTPS.",
    WEBCAM_ERROR: "Error de cámara web: ",
    FACE_RECOGNITION_START: "Iniciando reconocimiento facial...",
    NO_EMPLOYEE_DETECTED: "No se detectó ningún empleado registrado",
};

// 🎭 FASES DEL PROCESO (para futuras mejoras)
export const DETECTION_PHASES = {
    INITIALIZING: 'initializing',
    SMILE_DETECTION: 'smile_detection',
    FACE_RECOGNITION: 'face_recognition',
    COMPLETED: 'completed',
};