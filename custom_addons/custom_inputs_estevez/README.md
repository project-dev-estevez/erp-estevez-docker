# Custom Inputs Styles - Estevez

## Descripción
Módulo para personalizar globalmente los estilos de los campos de entrada (inputs) en el backend de Odoo.

## Características
- ✅ Estilos consistentes en todos los formularios del backend
- ✅ Bordes azules (#1a73e8) y esquinas redondeadas
- ✅ Efectos interactivos (hover y focus) 
- ✅ Fondo gris claro para mejor legibilidad
- ✅ Transiciones suaves
- ✅ Estados especiales para campos deshabilitados y de solo lectura
- ✅ Compatible con campos de texto, número, email, contraseña, textarea y selects
- ✅ Preserva el estilo original de checkboxes y radios

## Instalación
1. Colocar el módulo en la carpeta `custom_addons`
2. Actualizar la lista de aplicaciones en Odoo
3. Instalar el módulo desde Apps → Custom Inputs Styles - Estevez
4. Limpiar caché del navegador (Ctrl + Shift + R)

## Campos afectados
- Campos de texto (input[type="text"])
- Campos de contraseña (input[type="password"])  
- Campos numéricos (input[type="number"])
- Campos de email (input[type="email"])
- Campos de teléfono (input[type="tel"])
- Campos de URL (input[type="url"])
- Áreas de texto (textarea)
- Campos de selección (select)
- Campos de fecha (input[type="date"])

## Campos NO afectados
- Checkboxes (input[type="checkbox"])
- Radio buttons (input[type="radio"])
- Botones (input[type="button"])
- Archivos (input[type="file"])

## Personalización
Para modificar los estilos, editar el archivo:
`static/src/scss/custom_inputs.scss`

## Versión
16.0.1.0.0

## Autor
Estevez
