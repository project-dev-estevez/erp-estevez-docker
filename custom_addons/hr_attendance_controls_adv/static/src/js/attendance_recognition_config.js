/** @odoo-module **/

// 🔧 CONFIGURACIÓN CENTRALIZADA PARA RECONOCIMIENTO FACIAL
export const FACE_DETECTION_CONFIG = {
    // Configuración de detección de sonrisa
    SMILE: {
        HAPPINESS_THRESHOLD: 0.6,        // Umbral mínimo de felicidad (0-1)
        TIME_INCREMENT: 0.2,             // Incremento por detección (segundos)
        REQUIRED_DURATION: 5,            // Duración total requerida (segundos) - CAMBIADO A 5s
        DETECTION_INTERVAL: 200,         // Intervalo entre detecciones (ms)
        MOBILE_DETECTION_INTERVAL: 400,  // Intervalo más largo para móviles (ms)
    },
    
    // Configuración de reconocimiento facial
    RECOGNITION: {
        MAX_DESCRIPTOR_DISTANCE: 0.45,          // Distancia máxima para descriptores
        MAX_MATCH_DISTANCE: 0.5,                // Distancia máxima para matches válidos
        MIN_MATCH_COUNT: 2,                     // Mínimo de matches consecutivos
        DETECTION_INTERVAL: 200,                // Intervalo entre detecciones (ms)
        MOBILE_DETECTION_INTERVAL: 400,         // Intervalo más largo para móviles (ms)
        RETRY_DELAY: 500,                       // Delay para reintentos (ms)
        INITIAL_DISTANCE: 0.45,                 // Distancia para reconocimiento inicial
        SMILE_VALIDATION_DISTANCE: 0.5,         // Distancia para validar sonrisa
        FINAL_VALIDATION_DISTANCE: 0.5,         // Distancia para validación final
        INITIAL_TIMEOUT: 15000,                 // Timeout para reconocimiento inicial (ms) - Aumentado para móviles
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
    INITIAL_RECOGNITION_TIMEOUT: "⏰ Tiempo agotado: No se pudo identificar ningún empleado registrado. Por favor, asegúrese de estar bien iluminado y frente a la cámara.",
    NO_EMPLOYEE_DETECTED: "No se detectó ningún empleado registrado",
};

// 🎭 FASES DEL PROCESO DE SEGURIDAD
export const DETECTION_PHASES = {
    INITIAL_RECOGNITION: 'initial_recognition',
    SMILE_VALIDATION: 'smile_validation', 
    FINAL_RECOGNITION: 'final_recognition',
    COMPLETED: 'completed'
};