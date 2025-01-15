#!/bin/bash


VENV_PATH="/home/jacks/Security-Headers-Scanner/venv"

source "$VENV_PATH/bin/activate"

# Verificar se está dentro do prazo de 5 dias
if [[ $(date +%s) -le $(date +%s -d "5 days") ]]; then
    # Ativar ambiente virtual e executar o script
    
    "$VENV_PATH/bin/python3" /home/jacks/Security-Headers-Scanner/main.py   
else
    # Remover a tarefa do crontab
    crontab -l | grep -v 'scanner_job.sh' | crontab -
fi

deactivate
