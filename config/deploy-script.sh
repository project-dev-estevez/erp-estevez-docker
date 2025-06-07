#!/bin/bash
set -e

echo "Cambiando a usuario odoo18 y listando el home:"
sudo su - odoo18 -c "ls -1 ~" > /tmp/odoo18_home.txt
echo "Carpetas en el home de odoo18:"
cat /tmp/odoo18_home.txt

echo "Entrando a la carpeta odoo-erp y listando su contenido:"
sudo su - odoo18 -c "cd ~/odoo-erp && ls -1" > /tmp/odoo18_odooerp.txt
echo "Contenido de ~/odoo-erp:"
cat /tmp/odoo18_odooerp.txt