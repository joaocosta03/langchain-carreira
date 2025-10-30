#!/bin/bash
# Script de execução rápida para Linux/Mac

echo "======================================"
echo "Agente Consultor de Carreira em TI"
echo "======================================"
echo

# Ativa ambiente virtual se existir
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
    echo "[OK] Ambiente virtual ativado"
else
    echo "[AVISO] Ambiente virtual não encontrado"
    echo "Execute: python -m venv .venv"
    exit 1
fi

# Verifica se .env existe
if [ ! -f .env ]; then
    echo "[ERRO] Arquivo .env não encontrado"
    echo "Execute: python setup.py"
    exit 1
fi

echo
echo "Executando agente..."
echo

python main.py

