# Authentication Estevez.Jor

## Descripción

Módulo de personalización de la página de inicio de sesión para Odoo 18. Este módulo extiende las funcionalidades de autenticación de Odoo proporcionando múltiples diseños personalizables para la página de login, permitiendo una identidad corporativa única y profesional.

[![EXPLORING_ODOO](https://img.youtube.com/vi/hmBIX6U9zhQ/0.jpg)](https://youtu.be/hmBIX6U9zhQ)

## Características Principales

### 🎨 Diseños de Página de Login
El módulo ofrece **5 diseños diferentes** completamente personalizables:

1. **Fullscreen Right** - Diseño a pantalla completa con formulario a la derecha
2. **Fullscreen Left** - Diseño a pantalla completa con formulario a la izquierda  
3. **Boxed Right** - Diseño en caja con formulario a la derecha
4. **Boxed Left** - Diseño en caja con formulario a la izquierda
5. **Boxed Center** - Diseño en caja centrado

### 🖼️ Personalización Visual
- **Logo personalizado**: Carga tu propio logo para la página de login
- **Imagen de fondo**: Opción de usar una imagen de fondo personalizada
- **Frases motivacionales**: Muestra citas con autor y color personalizable
- **Diseño responsive**: Adaptación automática a diferentes tamaños de pantalla

### 🔐 Funcionalidad de Contraseñas
- **Mostrar/ocultar contraseña**: botón dentro del campo en las pantallas de acceso
  (iniciar sesión, restablecer contraseña y registro)
- Estilos CSS personalizados para los campos de contraseña
- JavaScript para manejar la interacción del botón

## Instalación

1. Copia el módulo en tu carpeta de addons personalizados:
```bash
cp -r auth_estevez /path/to/your/odoo/custom_addons/
```

2. Actualiza la lista de módulos en Odoo
3. Busca "Authentication Estevez.Jor" e instala el módulo

## Configuración

### Acceso a Configuración
1. Ve a **Ajustes → General**
2. Busca la sección **Auth Estevez.Jor**

### Opciones Configurables

#### Logo
- Carga la imagen del logo que aparecerá en la página de login

#### Fondo Personalizado
- **Activar**: Marca la casilla "Use Custom Background"
- **Cargar imagen**: Sube tu imagen de fondo personalizada

#### Diseño
- Selecciona uno de los 5 diseños disponibles desde el menú desplegable

#### Motto/Frase
- **Activar**: Marca "Show Motto" para mostrar una frase
- **Texto**: Escribe la frase que deseas mostrar
- **Autor**: Nombre del autor de la frase (opcional)
- **Color**: Selecciona el color del texto usando el selector de color

## Estructura Técnica

```
auth_estevez/
├── __init__.py
├── __manifest__.py
├── README.md
├── docs/
│   └── spec.md          # Especificación: criterios AUTH-NN, decisiones y trazabilidad
├── tests/               # Pruebas que validan docs/spec.md
├── controllers/
│   ├── __init__.py
│   ├── home.py          # Inyecta la configuración en login, registro y restablecer contraseña
│   └── binary.py        # Sirve logo y fondo (/login_logo.png, /login_page_background_image.png)
├── models/
│   ├── __init__.py
│   ├── res_config_settings.py    # Modelo de configuración
│   └── ir_config_parameter.py    # get_param_with_last_update() para servir imágenes
├── views/
│   ├── login_templates.xml        # Templates QWeb para login
│   └── res_config_settings_views.xml  # Vistas de configuración
└── static/
    ├── fonts/           # Fuente Poppins
    ├── img/            # Imágenes del módulo
    └── src/
        ├── css/        # Estilos personalizados
        ├── js/         # JavaScript para toggle de password
        └── scss/       # Estilos SCSS

```

## Dependencias

- `web` - Módulo web base de Odoo
- `auth_signup` - Módulo de registro de usuarios de Odoo

## Compatibilidad

- **Versión Odoo**: 18.0
- **Licencia**: LGPL-3

## Autor

**Estevez.Jor**

## Notas Técnicas

### Controladores
El módulo extiende `AuthSignupHome` para inyectar los parámetros de configuración en las siguientes rutas:
- `/web/login` - Página de inicio de sesión
- `/web/reset_password` - Restablecimiento de contraseña
- `/web/signup` - Registro de usuarios

### Assets
Todo va en `web.assets_frontend`: fuentes Poppins, SCSS de login, CSS y JS del botón
de contraseña. No hay assets de backend.

### Parámetros de Sistema
Todos los ajustes se almacenan en `ir.config_parameter` con el prefijo `auth_estevez.`:
- `auth_estevez.login_page_design`
- `auth_estevez.login_page_custom_background`
- `auth_estevez.login_page_background_image`
- `auth_estevez.login_page_logo`
- `auth_estevez.login_page_show_motto`
- `auth_estevez.login_page_motto_text`
- `auth_estevez.login_page_motto_author`
- `auth_estevez.login_page_motto_text_color`

> 🚧 **Refactor en pausa.** El paso 2 (configuración en `res.company`, migración
> 18.0.2.0.0) está implementado y validado, pero guardado como parche en
> `docs/wip/auth_estevez-paso2-backend.patch` (raíz del repo) hasta que el deploy
> ejecute respaldo + `-u`. Ver [docs/spec.md](docs/spec.md), sección 6.

## Desarrollo (SDD + TDD)

El comportamiento esperado está en **[docs/spec.md](docs/spec.md)**. Flujo para cualquier cambio:

1. Escribir o ajustar el criterio `AUTH-NN` en la especificación.
2. Escribir la prueba que lo valida (con el ID en el docstring) y verla fallar.
3. Implementar lo mínimo para que pase y refactorizar con las pruebas en verde.
4. Actualizar la tabla de trazabilidad de la especificación.

### Ejecutar las pruebas

Se usa una base de pruebas aparte para no tocar `odoo-prod`. La primera vez se crea con `-i`;
después basta con `-u`:

```bash
# Desde Git Bash, MSYS_NO_PATHCONV=1 evita que /etc/odoo/... se convierta en ruta de Windows
MSYS_NO_PATHCONV=1 docker compose exec -T odoo odoo -c /etc/odoo/odoo.conf \
  -d test_auth_estevez -u auth_estevez --test-enable --test-tags /auth_estevez \
  --stop-after-init --http-port 8079 --log-level=test
```

- `tests/test_login_page_values.py` — `TransactionCase`: valores de la página y Ajustes.
- `tests/test_login_routes.py` — `HttpCase` (`post_install`): pantallas de acceso e imágenes.
- `tests/test_migration.py` — `TransactionCase`: migración 18.0.2.0.0 y compañía de acceso
  (en rojo hasta reaplicar el parche del paso 2).

## Capturas de Pantalla

_Las capturas de pantalla de los diferentes diseños pueden agregarse en la carpeta `static/description/`_

## Soporte

Para problemas o sugerencias, contacta al autor o abre un issue en el repositorio del proyecto.