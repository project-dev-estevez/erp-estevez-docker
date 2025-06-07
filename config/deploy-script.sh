#!/bin/bash
set -ex

echo "Directorio actual:"
pwd

echo "📁 Listando contenido del directorio actual:"
ls -la

echo "📁 Listando contenido del home de odoo18:"
sudo su - odoo18 -c 'ls -la $HOME'