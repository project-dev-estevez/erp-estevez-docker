#!/bin/bash
set -ex

echo "Reiniciando el servicio odoo18..."
sudo systemctl restart odoo18

echo "Servicio odoo18 reiniciado correctamente."