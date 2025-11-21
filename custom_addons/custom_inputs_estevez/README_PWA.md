# Customización de Logos PWA para ERP Estevez

Este módulo personaliza los logos e iconos que aparecen cuando se descarga la PWA (Progressive Web App) en escritorio o Android.

## Iconos Personalizados

Para que funcione correctamente, debes colocar tus propios iconos en:

```
custom_inputs_estevez/static/src/img/
```

### Archivos necesarios:

1. **favicon.ico** (16x16 o 32x32 px)
   - Icono que aparece en la pestaña del navegador

2. **icon.png** (64x64 px)
   - Icono pequeño para la PWA

3. **odoo-icon-192x192.png** (192x192 px)
   - Icono estándar para Android y escritorio
   - Se usa como "apple-touch-icon" también

4. **odoo-icon-512x512.png** (512x512 px)
   - Icono de alta resolución para pantallas grandes
   - Usado en splash screens de Android

## Características

- **Color del tema**: `#714B67` (puedes cambiarlo en `controllers/main.py`)
- **Nombre de la app**: "ERP Estevez"
- **Nombre corto**: "Estevez"

## Cómo Generar los Iconos

### Opción 1: Usando herramientas online
1. Ve a https://realfavicongenerator.net/
2. Sube tu logo (preferiblemente cuadrado, PNG con fondo transparente)
3. Descarga todos los tamaños
4. Renombra según los nombres requeridos arriba

### Opción 2: Usando ImageMagick (línea de comandos)
```bash
# Desde tu logo original (logo.png)
magick convert logo.png -resize 64x64 icon.png
magick convert logo.png -resize 192x192 odoo-icon-192x192.png
magick convert logo.png -resize 512x512 odoo-icon-512x512.png
magick convert logo.png -resize 32x32 favicon.ico
```

### Opción 3: Photoshop/GIMP
1. Abre tu logo
2. Exporta en los tamaños mencionados
3. Para el favicon, guarda como ICO de 32x32

## Recomendaciones de Diseño

- **Fondo**: Preferiblemente transparente o con el color del tema (#714B67)
- **Forma**: Cuadrado o circular funcionan mejor
- **Contraste**: Asegúrate de que el logo sea visible sobre el color de fondo
- **Simplicidad**: Los iconos pequeños deben ser reconocibles fácilmente

## Aplicar los Cambios

Después de reemplazar los iconos:

1. Actualiza el módulo:
   ```bash
   docker compose restart
   ```

2. En Odoo, ve a:
   - Aplicaciones → Custom Inputs Estevez → Actualizar

3. Limpia la caché del navegador (Ctrl+Shift+Delete)

4. Para Android/iOS:
   - Desinstala la PWA anterior si la tenías instalada
   - Vuelve a instalarla desde el navegador

## Probar la PWA

### En escritorio:
1. Abre Chrome/Edge
2. Ve a tu Odoo
3. Busca el icono de instalación en la barra de direcciones
4. Instala la aplicación

### En Android:
1. Abre Chrome
2. Ve a tu Odoo
3. Menú → Agregar a pantalla de inicio
4. Verás tus iconos personalizados

## Personalización Adicional

Si quieres cambiar el color del tema, edita `controllers/main.py`:

```python
'background_color': '#714B67',  # Tu color aquí
'theme_color': '#714B67',        # Tu color aquí
```

También puedes modificar los nombres en:
- `'name': 'ERP Estevez'` (nombre completo)
- `'short_name': 'Estevez'` (nombre corto para pantalla inicio)

## Soporte

Los iconos funcionan en:
- ✅ Chrome (Windows, macOS, Linux, Android)
- ✅ Edge (Windows, macOS)
- ✅ Safari (iOS, macOS)
- ✅ Firefox (Android)
- ✅ Samsung Internet (Android)
