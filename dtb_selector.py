#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DTB Selector - R36 Clone Device Selection Tool
Original creator: LCDYK (https://lcdyk0517.github.io/dtbTools.html)
Modified by: Leonardo Bruno (https://github.com/souza-lb/arkos4clone-leonardo)
Multi-language support with English/Portuguese
30/11/2025 21:34:00
"""

import os
import sys
import shutil
import glob
import json
from pathlib import Path

# Global configuration
OPERATING_SYSTEM = None
CONSOLES = []
BRANDS = []

# Message system
class Messages:
    # Centralized message system with bilingual support / Sistema de mensagens centralizado com suporte bilíngue
    
    @staticmethod
    def get_header():
        return [
            "============================================================",
            "       DTB SELECTOR TOOL - R36 Device Configuration",
            "   Original creator: LCDYK - Modified by: Leonardo Bruno",
            "============================================================"
        ]
    
    @staticmethod
    def get_instructions():
        return {
            "title": "IMPORTANT INSTRUCTIONS / INSTRUÇÕES IMPORTANTES",
            "items": [
                "* Support only for listed consoles / Suporte apenas para consoles listados",
                "* DO NOT USE original DTB files! / Não utilize arquivos DTB originais!",
                "* Use the identification tool / Use a ferramenta de identificação:",
                "  https://lcdyk0517.github.io/dtbTools.html"
            ]
        }
    
    @staticmethod
    def get_success(console_name):
        return {
            "title": "OPERATION COMPLETED SUCCESSFULLY / OPERAÇÃO CONCLUÍDA COM SUCESSO",
            "console": f"Console: {console_name}",
            "next_steps": [
                "* Boot your device with the new configuration / Inicialize o dispositivo",
                "* Report any issues encountered / Relate problemas encontrados",
                "  Github: https://github.com/souza-lb/dtb-selector"
            ]
        }
    
    @staticmethod
    def get_errors():
        return {
            "file_not_found": "consoles.json file not found! / Arquivo consoles.json não encontrado!",
            "check_file": "Make sure the file is in the script directory. / Certifique-se que o arquivo está no diretório.",
            "json_error": "Error reading consoles.json: {}",
            "invalid_structure": "Invalid structure in consoles.json: {}",
            "operation_cancelled": "Operation cancelled by user. / Operação cancelada pelo usuário.",
            "invalid_input": "Please enter a valid number. / Por favor digite um número válido.",
            "invalid_number": "Invalid number. Try again. / Número inválido. Tente novamente."
        }

# System utilities
class SystemUtils:
    # System operation utilities / Utilitários de operação do sistema
    
    @staticmethod
    def detect_system():
        # Detect operating system / Detecta o sistema operacional
        if os.name == 'nt':
            return 'windows'
        return 'linux' if sys.platform != 'darwin' else 'macos'
    
    @staticmethod
    def clear_screen():
        # Clear terminal screen / Limpa a tela do terminal
        os.system('cls' if OPERATING_SYSTEM == 'windows' else 'clear')
    
    @staticmethod
    def wait_for_enter():
        # Wait for user to press Enter / Aguarda o usuário pressionar Enter
        try:
            input("\nPress Enter to continue... / Pressione Enter para continuar... ")
        except (KeyboardInterrupt, EOFError):
            print(Messages.get_errors()["operation_cancelled"])
            sys.exit(0)

# User interface
class UserInterface:
    # Manages user interface and interactions / Gerencia interface do usuário e interações
    
    @staticmethod
    def show_header(title=""):
        # Display customized header / Exibe cabeçalho personalizado
        SystemUtils.clear_screen()
        
        header = Messages.get_header()
        for line in header:
            print(line)
        
        if title:
            print(f"\n{title}")
            print("=" * 60)
        print()
    
    @staticmethod
    def show_introduction():
        # Display introduction and instructions / Exibe introdução e instruções
        UserInterface.show_header("DTB Selector - Choose Your Console")
        
        instructions = Messages.get_instructions()
        
        print("WELCOME TO DTB SELECTOR / BEM-VINDO AO SELETOR DTB")
        print("=" * 60)
        print()
        
        print(instructions["title"])
        for item in instructions["items"]:
            print(f"  {item}")
        
        print("\nTip: Press 'q' anytime to exit / Pressione 'q' para sair")
        
        try:
            response = input("\nPress Enter to continue / Pressione Enter: ").strip().lower()
            if response == 'q':
                print("\nGoodbye! Thank you for using DTB Selector! / Obrigado por usar!")
                sys.exit(0)
        except (KeyboardInterrupt, EOFError):
            print(Messages.get_errors()["operation_cancelled"])
            sys.exit(0)
    
    @staticmethod
    def read_input(message):
        # Safely read user input / Lê entrada do usuário com segurança
        try:
            return input(message).strip()
        except (KeyboardInterrupt, EOFError):
            print(Messages.get_errors()["operation_cancelled"])
            sys.exit(0)

# Configuration manager
class ConfigManager:
    # Manages configuration loading / Gerencia carregamento de configuração
    
    @staticmethod
    def load_configuration():
        # Load console configuration from JSON file / Carrega configuração de consoles do arquivo JSON
        try:
            config_path = Path(__file__).parent / "consoles.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config["consoles"], config["brands"]
        except FileNotFoundError:
            print(Messages.get_errors()["file_not_found"])
            print(Messages.get_errors()["check_file"])
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(Messages.get_errors()["json_error"].format(e))
            sys.exit(1)
        except KeyError as e:
            print(Messages.get_errors()["invalid_structure"].format(e))
            sys.exit(1)

# File Manager
class FileManager:
    # Manages file operations / Gerencia operações de arquivo
    
    @staticmethod
    def clean_destination_directory():
        # Clean previous files from current directory / Limpa arquivos anteriores do diretório atual
        print("\nCleaning destination directory... / Limpando diretório...")
        
        patterns = ["*.dtb", "*.ini", "*.orig", "*.tony", ".cn"]
        files_removed = 0
        
        for pattern in patterns:
            try:
                for file in glob.glob(pattern):
                    print(f"   Removing: {file}")
                    try:
                        os.remove(file)
                        files_removed += 1
                    except OSError as e:
                        print(f"   Warning: Could not remove {file}: {e}")
            except Exception as e:
                print(f"   Error processing pattern {pattern}: {e}")
        
        # Remove BMPs directory if exists / Remove diretório BMPs se existir
        if os.path.exists("BMPs"):
            print("   Removing: BMPs/")
            try:
                shutil.rmtree("BMPs")
                print("   BMPs directory removed")
            except OSError as e:
                print(f"   Warning: Could not remove BMPs/: {e}")
        
        if files_removed == 0:
            print("   No previous files found")
    
    @staticmethod
    def recursive_copy(source, destination):
        # Copy files/directories recursively / Copia arquivos/diretórios recursivamente
        try:
            source_path = Path(source)
            destination_path = Path(destination)
            
            if not source_path.exists():
                print(f"   Source does not exist: {source}")
                return False
                
            if source_path.is_dir():
                if sys.version_info >= (3, 8):
                    shutil.copytree(source, destination, dirs_exist_ok=True)
                else:
                    for item in source_path.iterdir():
                        item_dest = destination_path / item.name
                        if item.is_dir():
                            FileManager.recursive_copy(str(item), str(item_dest))
                        else:
                            shutil.copy2(str(item), str(item_dest))
                return True
            else:
                destination_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                return True
        except Exception as e:
            print(f"   Error copying {source} to {destination}: {e}")
            return False
    
    @staticmethod
    def copy_console(selected_console):
        # Copy files for selected console / Copia arquivos para o console selecionado
        display_name = selected_console["display_name"]
        real_name = selected_console["real_name"]
        
        print(f"\nStarting copy: {display_name}")
        
        # Copy main console / Copia console principal
        console_source = os.path.join("consoles", real_name)
        if os.path.exists(console_source):
            print(f"   Copying console: {real_name}")
            if not FileManager.recursive_copy(console_source, "."):
                return False
        else:
            print(f"   Directory not found: {console_source}")
            return False
        
        # Copy extra resources / Copia recursos extras
        print("   Copying extra resources...")
        for resource in selected_console["extra_sources"]:
            resource_source = os.path.join("consoles", resource)
            if os.path.exists(resource_source):
                print(f"      {resource}")
                if not FileManager.recursive_copy(resource_source, "."):
                    print(f"      Warning: Failed to copy {resource}")
            else:
                print(f"      Extra resource not found: {resource}")
        
        return True

# Menu System
class MenuManager:
    # Manages all system menus / Gerencia todos os menus do sistema
    
    @staticmethod
    def brand_menu():
        # Brand selection menu / Menu de seleção de marca
        while True:
            UserInterface.show_header("Brand Selection")
            
            print("SELECT A BRAND / SELECIONE UMA MARCA")
            print("-" * 40)
            print()
            
            for i, brand in enumerate(BRANDS, 1):
                print(f"  {i}. {brand}")
            
            print(f"\n  0. Exit / Sair")
            print()
            
            choice = UserInterface.read_input("Enter brand number / Digite o número da marca: ")
            
            if not choice:
                continue
                
            try:
                choice_num = int(choice)
                if choice_num == 0:
                    return None
                elif 1 <= choice_num <= len(BRANDS):
                    return BRANDS[choice_num - 1]
                else:
                    print(Messages.get_errors()["invalid_number"])
                    SystemUtils.wait_for_enter()
            except ValueError:
                print(Messages.get_errors()["invalid_input"])
                SystemUtils.wait_for_enter()
    
    @staticmethod
    def console_menu(selected_brand):
        # Console selection menu for specific brand / Menu de seleção de console para marca específica
        brand_consoles = []
        for console in CONSOLES:
            for entry in console["brand_entries"]:
                if entry["brand"] == selected_brand:
                    brand_consoles.append({
                        "console_config": console,
                        "display_name": entry["display_name"]
                    })
        
        if not brand_consoles:
            print(f"No consoles found for: {selected_brand}")
            SystemUtils.wait_for_enter()
            return None
        
        while True:
            UserInterface.show_header(f"{selected_brand} Consoles")
            
            print("SELECT CONSOLE / SELECIONE O CONSOLE")
            print("-" * 40)
            print()
            
            for i, console_info in enumerate(brand_consoles, 1):
                print(f"  {i}. {console_info['display_name']}")
            
            print(f"\n  0. Back / Voltar")
            print()
            
            choice = UserInterface.read_input("Enter console number / Digite o número do console: ")
            
            if not choice:
                continue
                
            try:
                choice_num = int(choice)
                if choice_num == 0:
                    return None
                elif 1 <= choice_num <= len(brand_consoles):
                    selected_console = brand_consoles[choice_num - 1]
                    console_config = selected_console["console_config"].copy()
                    console_config["display_name"] = selected_console["display_name"]
                    return console_config
                else:
                    print(Messages.get_errors()["invalid_number"])
                    SystemUtils.wait_for_enter()
            except ValueError:
                print(Messages.get_errors()["invalid_input"])
                SystemUtils.wait_for_enter()
    
    @staticmethod
    def language_menu():
        # Language selection menu / Menu de seleção de idioma
        while True:
            UserInterface.show_header("Language Selection")
            
            print("Select language / Selecione o idioma:")
            print(" 1. English")
            print(" 2. Chinese")
            print(" 3. Portuguese")
            print(f" 0. Keep current setting / Manter configuração atual")
            print()
            
            choice = UserInterface.read_input("Enter your choice / Digite sua escolha: ")
            
            if not choice:
                return None
            
            try:
                choice_num = int(choice)
                if choice_num == 0:
                    return None
                elif choice_num == 1:
                    return "en"
                elif choice_num == 2:
                    return "cn" 
                elif choice_num == 3:
                    return "br"
                else:
                    print("Invalid choice. / Escolha inválida.")
                    SystemUtils.wait_for_enter()
            except ValueError:
                print(Messages.get_errors()["invalid_input"])
                SystemUtils.wait_for_enter()
    
    @staticmethod
    def apply_language(language):
        # Apply selected language configuration / Aplica configuração de idioma selecionada
        print("\nConfiguring language... / Configurando idioma...")
        
        # Remove existing language files / Remove arquivos de idioma existentes
        for lang_file in [".cn", ".br", ".en"]:
            if os.path.exists(lang_file):
                try:
                    os.remove(lang_file)
                    print(f"   Removed: {lang_file}")
                except OSError as e:
                    print(f"   Could not remove {lang_file}: {e}")
        
        # Create selected language file / Cria arquivo de idioma selecionado
        if language == "en":
            print("   Language set: English / Idioma definido: Inglês")
            print("   No file created (English default) / Nenhum arquivo criado (Inglês padrão)")
        elif language == "cn":
            try:
                # Create empty .cn file / Cria arquivo .cn vazio
                open(".cn", "w", encoding='utf-8').close()
                print("   Language set: Chinese / Idioma definido: Chinês")
            except Exception as e:
                print(f"   Error creating .cn file: {e}")
        elif language == "br":
            try:
                # Create empty .br file / Cria arquivo .br vazio
                open(".br", "w", encoding='utf-8').close()
                print("   Language set: Portuguese Brazil / Idioma definido: Português Brasil")
            except Exception as e:
                print(f"   Error creating .br file: {e}")

# Main function
def main():
    # Main program function / Função principal do programa
    global OPERATING_SYSTEM, CONSOLES, BRANDS
    
    try:
        # Initialization / Inicialização
        OPERATING_SYSTEM = SystemUtils.detect_system()
        CONSOLES, BRANDS = ConfigManager.load_configuration()
        
        print(f"System detected: {OPERATING_SYSTEM.upper()}")
        print(f"Python: {sys.version.split()[0]}")
        
        # Introduction / Introdução
        UserInterface.show_introduction()
        
        # Brand selection / Seleção de marca
        brand = MenuManager.brand_menu()
        if not brand:
            print("\nOperation cancelled. Goodbye! / Operação cancelada. Até logo!")
            return
        
        # Console selection / Seleção de console
        console = MenuManager.console_menu(brand)
        if not console:
            print("\nNo console selected. / Nenhum console selecionado.")
            return
        
        # Confirmation / Confirmação
        print(f"\nConsole selected: {console['display_name']}")
        confirmation = UserInterface.read_input("Continue with copy? (y/N) / Continuar com a cópia? (s/N): ").strip().lower()
        
        if confirmation not in ['s', 'sim', 'y', 'yes']:
            print("\nOperation cancelled by user. / Operação cancelada pelo usuário.")
            return
        
        # Processing / Processamento
        FileManager.clean_destination_directory()
        
        if not FileManager.copy_console(console):
            print("\nError during file copy. / Erro durante a cópia dos arquivos.")
            return
        
        # Language / Idioma
        language = MenuManager.language_menu()
        if language:
            MenuManager.apply_language(language)
        
        # Success / Sucesso
        UserInterface.show_header("Operation Completed! / Operação Concluída!")
        
        success_msg = Messages.get_success(console['display_name'])
        print("SUCCESS! / SUCESSO!")
        print("=" * 30)
        print()
        print(success_msg["title"])
        print(success_msg["console"])
        
        # Language applied / Idioma aplicado
        if language == "en":
            print("Language: English / Idioma: Inglês")
        elif language == "cn":
            print("Language: Chinese / Idioma: Chinês")
        elif language == "br":
            print("Language: Portuguese Brazil / Idioma: Português Brasil")
        else:
            if os.path.exists(".cn"):
                print("Language: Chinese (kept) / Idioma: Chinês (mantido)")
            elif os.path.exists(".br"):
                print("Language: Portuguese Brazil (kept) / Idioma: Português Brasil (mantido)")
            else:
                print("Language: English (kept) / Idioma: Inglês (mantido)")
        
        print("\nNEXT STEPS / PRÓXIMOS PASSOS:")
        for step in success_msg["next_steps"]:
            print(f"  {step}")
                
        SystemUtils.wait_for_enter()
        
    except KeyboardInterrupt:
        print("\nOperation interrupted by user. Goodbye! / Operação interrompida. Até logo!")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
