# Especificación — auth_estevez

> Fuente de verdad del comportamiento del módulo (SDD). Cada criterio tiene un ID
> `AUTH-NN`; las pruebas lo citan en su docstring y la tabla de trazabilidad del
> final dice en qué estado está. **Si cambia el comportamiento, primero cambia
> este archivo, después la prueba, al final el código.**

## 1. Propósito

Personalizar las pantallas de acceso de Odoo 18 (iniciar sesión, restablecer
contraseña y registro) con la identidad de Estevez.Jor: diseño de la página,
logo, fondo, lema y botón para mostrar la contraseña.

Fuera de alcance: autenticación en sí (2FA, SSO, políticas de contraseña), el
backend de Odoo y el portal.

## 2. Glosario

| Término | Significado |
|---|---|
| Pantallas de acceso | `/web/login`, `/web/reset_password`, `/web/signup` |
| Diseño | Uno de: `fullscreen_left`, `fullscreen_right`, `boxed_left`, `boxed_right`, `boxed_center` |
| Compañía de acceso | La compañía cuya configuración se muestra antes de iniciar sesión: la del usuario con sesión o, si no hay sesión, `base.main_company` (misma regla que `/web/binary/company_logo`) |
| Valores de la página | El `dict` que devuelve `res.company._get_login_page_values()` y que reciben las plantillas |

## 3. Decisiones de arquitectura

| ID | Decisión | Motivo |
|---|---|---|
| D1 | La configuración vive en campos de `res.company`; `res.config.settings` la expone con `related=..., readonly=False`. | Tipado y validación del ORM, valores por defecto reales, imágenes como `ir.attachment` (no base64 en `ir.config_parameter` ni en `ormcache`). |
| D2 | Un único punto de lectura: `res.company._get_login_page_values()`, que ya resuelve valores por defecto y sanea entradas. | Una sola fuente de verdad, fácil de probar sin HTTP. |
| D3 | El controlador inyecta los valores con `response.qcontext.update(...)` tras `super()`. Nunca escribe en `request.params` ni en `SIGN_UP_REQUEST_PARAMS`. | Sin estado global mutable, sin mezclar entrada del usuario con configuración. |
| D4 | Las imágenes se sirven con `ir.binary` (`_get_image_stream_from`). | ETag, caché y mimetype resueltos por Odoo; sin código duplicado. |
| D5 | Todo el CSS de las pantallas de acceso cuelga de la clase raíz `.o_auth_estevez`. | Que nada se filtre al portal, eLearning o sitio web. |
| D6 | Los datos existentes se migran con `migrations/18.0.2.0.0/post-migrate.py` desde `ir.config_parameter` (`auth_estevez.*`) y luego se borran esos parámetros. | Actualizar producción sin perder la configuración. |

## 4. Criterios de aceptación

### 4.1 Valores de la página (modelo)

- **AUTH-01 — Diseño por defecto.**
  Dado que nunca se configuró el diseño,
  cuando se obtienen los valores de la página,
  entonces `login_page_design` es `fullscreen_left`.
- **AUTH-02 — Diseño inválido.**
  Dado un diseño guardado que no está en la lista,
  cuando se obtienen los valores,
  entonces se usa `fullscreen_left`.
- **AUTH-03 — Color del lema saneado.**
  Dado que el color del lema está vacío o no es un hex `#rgb`/`#rrggbb`,
  cuando se obtienen los valores,
  entonces `login_page_motto_text_color` es `#000000`.
  (Evita inyectar CSS en el atributo `style`.)
- **AUTH-04 — Ajustes de ida y vuelta.**
  Dado que un administrador guarda diseño, fondo, lema, autor y color en Ajustes,
  cuando vuelve a abrir Ajustes,
  entonces ve los mismos valores.
- **AUTH-05 — Imágenes como adjuntos.**
  Dado que se sube un logo o un fondo en Ajustes,
  entonces queda en la compañía de acceso
  y no existe ningún parámetro `auth_estevez.login_page_logo` ni
  `auth_estevez.login_page_background_image` en `ir.config_parameter`.

- **AUTH-18 — Migración sin pérdida.**
  Dado que existen parámetros `auth_estevez.*` en `ir.config_parameter` (versión ≤ 18.0.1),
  cuando se actualiza a 18.0.2.0.0,
  entonces sus valores quedan en los campos de la compañía de acceso
  (los booleanos `"True"` como `True`, un diseño inválido se ignora)
  y ya no existe ningún parámetro `auth_estevez.*`.
- **AUTH-19 — Compañía de acceso.**
  Sin sesión, `res.company._get_login_page_company()` devuelve `base.main_company`;
  con sesión, la compañía del usuario.

> Nota multicompañía: Ajustes edita la compañía activa del administrador, pero sin sesión
> la página muestra la de `base.main_company`. Si hay varias compañías, configurar la principal.

### 4.2 Pantallas de acceso (HTTP)

- **AUTH-06 — Clase raíz y diseño.**
  Cuando se abre cualquiera de las pantallas de acceso,
  entonces el HTML contiene `o_auth_estevez` y `o_login--<diseño>` con el diseño vigente.
- **AUTH-07 — Títulos por pantalla.**
  `/web/login` muestra "Iniciar Sesión", `/web/reset_password` muestra
  "Restablecer contraseña" y `/web/signup` muestra "Crear cuenta".
- **AUTH-08 — La URL no cambia la configuración.**
  Dado que el diseño vigente es `fullscreen_left`,
  cuando se abre `/web/login?login_page_design=boxed_center`,
  entonces se muestra `o_login--fullscreen_left`.
- **AUTH-09 — Sin estado global.**
  Después de servir `/web/login`, `SIGN_UP_REQUEST_PARAMS` de
  `odoo.addons.web.controllers.home` no contiene ninguna clave `login_page_*`.
- **AUTH-10 — Lema visible solo si está activo.**
  Con el lema activo se muestran texto y autor; con el lema inactivo no se
  renderiza `login-quote`.

### 4.3 Imágenes (HTTP)

- **AUTH-11 — Respaldo sin imagen.**
  Sin logo configurado, `/login_logo.png` responde 200 con `image/png`
  (PNG transparente de 1x1). Igual para `/login_page_background_image.png`.
- **AUTH-12 — Imagen configurada.**
  Con logo configurado, `/login_logo.png` responde 200 con los bytes del logo
  y su mimetype real.

### 4.4 Frontend (punto 3 del plan; verificación con tour o revisión)

- **AUTH-13 — CSS acotado.** Ninguna regla del módulo aplica fuera de `.o_auth_estevez`
  (no hay `body`/`#wrapwrap` globales ni `!important`).
- **AUTH-14 — Bundle sin duplicados.** El manifiesto no vuelve a incluir
  `web._assets_bootstrap_frontend`; las fuentes son solo `woff2` de los pesos usados.
- **AUTH-15 — Mostrar contraseña.** En las pantallas de acceso, cada campo
  de contraseña tiene un botón que alterna `type` entre `password`/`text`,
  actualiza `aria-pressed` y conserva el foco y la posición del cursor. Las
  etiquetas son traducibles (`_t`).
- **AUTH-16 — Textos traducibles.** Títulos, etiquetas de Ajustes y textos de
  plantillas salen en `i18n/es.po` y `i18n/es_419.po`.
- **AUTH-17 — Accesibilidad.** Toda `<img>` tiene `alt`; el lema cumple
  contraste AA sobre su fondo.

## 5. Trazabilidad

Estado: ✅ pasa · 🔴 falla (pendiente de implementar) · ⏳ sin prueba automática todavía.
Historial de corridas (base `test_auth_estevez`):

| Fecha | Paso | Resultado |
|---|---|---|
| 2026-11-02 | 1 — especificación + pruebas en rojo | 4 ✅ / 8 🔴 de 12 |
| 2026-11-02 | 2 — backend (D1–D4, D6), con el parche aplicado | 13 ✅ / 2 🔴 de 15 |
| 2026-11-02 | Código actual de `main` (parche del paso 2 guardado, sin aplicar) | **4 ✅ / 11 🔴 de 15** |

La columna "Estado" refleja el código de `main`; "Con parche" refleja el paso 2 validado.

| Criterio | Prueba | Estado | Con parche |
|---|---|---|---|
| AUTH-01 | `test_login_page_values.py::test_default_design` | 🔴 | ✅ |
| AUTH-02 | `test_login_page_values.py::test_invalid_design_falls_back` | 🔴 | ✅ |
| AUTH-03 | `test_login_page_values.py::test_motto_color_sanitized` | 🔴 | ✅ |
| AUTH-04 | `test_login_page_values.py::test_settings_round_trip` | ✅ | ✅ |
| AUTH-05 | `test_login_page_values.py::test_images_stored_on_company` | 🔴 | ✅ |
| AUTH-06 | `test_login_routes.py::test_root_and_design_classes` | 🔴 | 🔴 paso 3 (plantillas) |
| AUTH-07 | `test_login_routes.py::test_titles_per_screen` | 🔴 (H1) | ✅ |
| AUTH-08 | `test_login_routes.py::test_url_cannot_override_design` | 🔴 | 🔴 paso 3 (clase de AUTH-06) |
| AUTH-09 | `test_login_routes.py::test_no_global_state_mutation` | 🔴 | ✅ |
| AUTH-10 | `test_login_routes.py::test_motto_toggle` | ✅ | ✅ |
| AUTH-11 | `test_login_routes.py::test_image_fallback` | ✅ | ✅ |
| AUTH-12 | `test_login_routes.py::test_configured_logo_served` | ✅ | ✅ |
| AUTH-13…17 | — | ⏳ | ⏳ |
| AUTH-18 | `test_migration.py::test_legacy_params_move_to_company`, `test_invalid_legacy_design_is_ignored` | 🔴 | ✅ |
| AUTH-19 | `test_migration.py::test_login_page_company` | 🔴 | ✅ |

### Hallazgos de las pruebas

- **H1 (bug confirmado).** En una base nueva no existe `auth_estevez.login_page_design`;
  el `default` del campo de Ajustes solo aplica en el formulario, así que la plantilla
  cae en `boxed_center`, que **no muestra el título** de la pantalla ("Log in" de Odoo
  en lugar de "Iniciar Sesión"). Producción no lo nota porque el diseño ya se guardó
  alguna vez. Se corrige con AUTH-01 + AUTH-07. **Corregido en el paso 2 (parche).**

## 6. Plan de refactor

1. ~~Especificación y pruebas~~ ✅
2. Backend: D1–D4 y migración D6 — **implementado y validado, en pausa** 🚧
   - Contenido: campos en `res.company`, `_get_login_page_values()`, `_get_login_page_company()`,
     inyección por `qcontext`, imágenes con `ir.binary`, `migrations/18.0.2.0.0/post-migrate.py`,
     versión 18.0.2.0.0; elimina `models/ir_config_parameter.py` y los alias de ruta sin uso
     (`/web/binary/login_logo`, `/web/login_logo`, `/web/binary/login_page_background_image`,
     `/web/login_page_background_image`).
   - **Por qué en pausa:** agrega columnas y una migración, y el deploy actual a producción
     solo reinicia el servicio (sin respaldo ni `-u`). Bloqueado por la nueva infraestructura
     ([docs/infra/spec.md](../../../docs/infra/spec.md), criterios INFRA-07 y INFRA-08).
   - **Cómo retomarlo:** desde la raíz del repo, `git apply docs/wip/auth_estevez-paso2-backend.patch`,
     correr las pruebas (debe dar 13 ✅ / 2 🔴) y borrar el parche.
3. Plantillas QWeb: subplantillas `t-call`, clase raíz y de diseño, i18n, `alt` (AUTH-06, 08, 16, 17).
   También bloqueado: las vistas son registros `ir.ui.view` y solo se actualizan con `-u`.
4. Frontend: CSS acotado, bundle y fuentes, `publicWidget` (AUTH-13…15). Los cambios en archivos
   estáticos y en la clave `assets` del manifiesto llegan con un reinicio, así que es lo único
   que se podría desplegar con el pipeline actual.
