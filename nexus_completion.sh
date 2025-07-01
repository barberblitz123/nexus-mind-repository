#!/bin/bash
# NEXUS Shell Completion Script

# Bash completion for nexus command
_nexus_completion() {
    local cur prev commands subcommands
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    # Main commands
    commands="status chat goal create launch config help"
    
    # Subcommand options
    case "${prev}" in
        nexus)
            COMPREPLY=( $(compgen -W "${commands}" -- ${cur}) )
            return 0
            ;;
        goal)
            COMPREPLY=( $(compgen -W "--priority -p" -- ${cur}) )
            return 0
            ;;
        create)
            COMPREPLY=( $(compgen -W "--template -t" -- ${cur}) )
            return 0
            ;;
        launch)
            COMPREPLY=( $(compgen -W "--minimal -m" -- ${cur}) )
            return 0
            ;;
        --priority|-p)
            COMPREPLY=( $(compgen -W "LOW MEDIUM HIGH CRITICAL" -- ${cur}) )
            return 0
            ;;
        --template|-t)
            COMPREPLY=( $(compgen -W "react vue angular python-api django fastapi express nextjs" -- ${cur}) )
            return 0
            ;;
    esac
    
    # Handle file completion for certain commands
    case "${COMP_WORDS[1]}" in
        create)
            if [[ ${COMP_CWORD} -eq 2 ]]; then
                # Project name - no completion
                return 0
            fi
            ;;
    esac
    
    COMPREPLY=( $(compgen -W "${commands}" -- ${cur}) )
}

# Zsh completion for nexus command
if [[ -n "$ZSH_VERSION" ]]; then
    _nexus_completion_zsh() {
        local -a commands
        commands=(
            'status:Show NEXUS system status'
            'chat:Start interactive chat with NEXUS'
            'goal:Submit a goal to NEXUS'
            'create:Create a new project'
            'launch:Launch NEXUS services'
            'config:Configure NEXUS settings'
            'help:Show detailed help and examples'
        )
        
        _arguments \
            '1: :->command' \
            '*:: :->args'
        
        case $state in
            command)
                _describe 'command' commands
                ;;
            args)
                case $words[1] in
                    goal)
                        _arguments \
                            '--priority[Goal priority]:priority:(LOW MEDIUM HIGH CRITICAL)' \
                            '-p[Goal priority]:priority:(LOW MEDIUM HIGH CRITICAL)'
                        ;;
                    create)
                        _arguments \
                            '--template[Project template]:template:(react vue angular python-api django fastapi express nextjs)' \
                            '-t[Project template]:template:(react vue angular python-api django fastapi express nextjs)'
                        ;;
                    launch)
                        _arguments \
                            '--minimal[Start only core services]' \
                            '-m[Start only core services]'
                        ;;
                esac
                ;;
        esac
    }
    
    compdef _nexus_completion_zsh nexus
else
    # Bash completion
    complete -F _nexus_completion nexus
fi

# Quick aliases for common commands
alias nx='nexus'
alias nxs='nexus status'
alias nxc='nexus chat'
alias nxg='nexus goal'
alias nxcr='nexus create'
alias nxl='nexus launch'

# Function for quick project creation
nxnew() {
    if [ -z "$1" ]; then
        echo "Usage: nxnew <project-name> [template]"
        echo "Templates: react, vue, angular, python-api, django, fastapi, express, nextjs"
        return 1
    fi
    
    if [ -z "$2" ]; then
        nexus create "$1"
    else
        nexus create "$1" --template "$2"
    fi
}

# Function for quick goal submission
nxdo() {
    if [ -z "$1" ]; then
        echo "Usage: nxdo <goal> [priority]"
        echo "Priorities: LOW, MEDIUM, HIGH, CRITICAL"
        return 1
    fi
    
    if [ -z "$2" ]; then
        nexus goal "$1"
    else
        nexus goal "$1" --priority "$2"
    fi
}

# Export functions
export -f nxnew
export -f nxdo