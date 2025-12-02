#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DTB Selector - R36 Clone Device Selection Tool
Original creator: LCDYK (https://lcdyk0517.github.io/dtbTools.html)
Modified by: Leonardo Bruno (https://github.com/souza-lb/arkos4clone-leonardo)
Multi-language support with English/Portuguese
"""

import os
import sys
import shutil
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# ============================================================================
# Configurações Globais e Constantes
# ============================================================================

class Config:
    """Configurações globais do aplicativo."""
    CLEANUP_PATTERNS = ["*.dtb", "*.ini", "*.orig", "*.tony"]
    CONSOLES_DIR = "consoles"
    CONFIG_FILE = "consoles.json"
    SUPPORTED_LANGUAGES = {
        "en": {"name": "English", "file": None},
        "cn": {"name": "Chinese", "file": ".cn"},
        "br": {"name": "Portuguese Brazil", "file": ".br"}
    }
    DEFAULT_LANGUAGE = "en"

# ============================================================================
# Classes de Exceção Personalizadas
# ============================================================================

class DTBSelectorError(Exception):
    """Exceção base para erros do DTB Selector."""
    pass

class ConfigError(DTBSelectorError):
    """Erro de configuração."""
    pass

class FileOperationError(DTBSelectorError):
    """Erro em operação de arquivo."""
    pass

# ============================================================================
# Configuração de Logging
# ============================================================================

def setup_logging(level: str = "INFO") -> None:
    """Configura o sistema de logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('dtb_selector.log'),
            logging.StreamHandler()
        ]
    )

# ============================================================================
# Classe de Estado da Aplicação
# ============================================================================

class AppState:
    """Mantém o estado da aplicação."""
    def __init__(self):
        self.operating_system: Optional[str] = None
        self.consoles: List[Dict[str, Any]] = []
        self.brands: List[str] = []
        self.selected_brand: Optional[str] = None
        self.selected_console: Optional[Dict[str, Any]] = None
        self.selected_language: Optional[str] = None
        
    def reset_selections(self) -> None:
        """Reseta as seleções do usuário."""
        self.selected_brand = None
        self.selected_console = None
        self.selected_language = None

# ============================================================================
# Sistema de Mensagens
# ============================================================================

class Messages:
    """Centraliza todas as mensagens do sistema."""
    
    @staticmethod
    def get_header() -> List[str]:
        return [
            "============================================================",
            "       DTB SELECTOR TOOL - R36 Device Configuration",
            "   Original creator: LCDYK - Modified by: Leonardo Bruno",
            "============================================================"
        ]
    
    @staticmethod
    def get_instructions() -> Dict[str, Any]:
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
    def get_success(console_name: str) -> Dict[str, Any]:
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
    def get_errors() -> Dict[str, str]:
        return {
            "file_not_found": "consoles.json file not found! / Arquivo consoles.json não encontrado!",
            "check_file": "Make sure the file is in the script directory. / Certifique-se que o arquivo está no diretório.",
            "json_error": "Error reading consoles.json: {}",
            "invalid_structure": "Invalid structure in consoles.json: {}",
            "operation_cancelled": "Operation cancelled by user. / Operação cancelada pelo usuário.",
            "invalid_input": "Please enter a valid number. / Por favor digite um número válido.",
            "invalid_number": "Invalid number. Try again. / Número inválido. Tente novamente.",
            "unexpected_error": "Unexpected error: {}"
        }

# ============================================================================
# Utilitários do Sistema
# ============================================================================

class SystemUtils:
    """Utilitários para operações do sistema."""
    
    @staticmethod
    def detect_system() -> str:
        """Detecta o sistema operacional."""
        if os.name == 'nt':
            return 'windows'
        return 'linux' if sys.platform != 'darwin' else 'macos'
    
    @staticmethod
    def clear_screen() -> None:
        """Limpa a tela do terminal."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    @staticmethod
    def wait_for_enter() -> None:
        """Aguarda o usuário pressionar Enter."""
        try:
            input("\nPress Enter to continue... / Pressione Enter para continuar... ")
        except (KeyboardInterrupt, EOFError):
            raise DTBSelectorError(Messages.get_errors()["operation_cancelled"])

# ============================================================================
# Utilitários de Entrada do Usuário
# ============================================================================

class InputHandler:
    """Lida com a entrada do usuário de forma segura."""
    
    @staticmethod
    def read_input(prompt: str) -> str:
        """Lê a entrada do usuário, tratando interrupções."""
        try:
            return input(prompt).strip()
        except (KeyboardInterrupt, EOFError):
            raise DTBSelectorError(Messages.get_errors()["operation_cancelled"])
    
    @staticmethod
    def get_integer_input(prompt: str, min_val: int = None, max_val: int = None) -> int:
        """Lê um número inteiro com validação."""
        while True:
            try:
                value = InputHandler.read_input(prompt)
                num = int(value)
                
                if min_val is not None and num < min_val:
                    print(f"Value must be at least {min_val}")
                    continue
                if max_val is not None and num > max_val:
                    print(f"Value must be at most {max_val}")
                    continue
                    
                return num
            except ValueError:
                print(Messages.get_errors()["invalid_input"])

# ============================================================================
# Gerenciador de Configuração
# ============================================================================

class ConfigManager:
    """Gerencia o carregamento da configuração."""
    
    @staticmethod
    def load_configuration() -> Tuple[List[Dict[str, Any]], List[str]]:
        """Carrega a configuração de consoles do arquivo JSON."""
        config_path = Path(__file__).parent / Config.CONFIG_FILE
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config["consoles"], config["brands"]
        except FileNotFoundError:
            raise ConfigError(Messages.get_errors()["file_not_found"] + "\n" + 
                             Messages.get_errors()["check_file"])
        except json.JSONDecodeError as e:
            raise ConfigError(Messages.get_errors()["json_error"].format(e))
        except KeyError as e:
            raise ConfigError(Messages.get_errors()["invalid_structure"].format(e))

# ============================================================================
# Gerenciador de Arquivos
# ============================================================================

class FileManager:
    """Gerencia operações de arquivo."""
    
    @staticmethod
    def clean_destination_directory() -> None:
        """Limpa o diretório atual de arquivos anteriores."""
        logging.info("Cleaning destination directory...")
        current_dir = Path.cwd()
        
        for pattern in Config.CLEANUP_PATTERNS:
            for file in current_dir.glob(pattern):
                try:
                    file.unlink()
                    logging.info(f"   Removed: {file}")
                except OSError as e:
                    logging.warning(f"   Could not remove {file}: {e}")
        
        # Remove BMPs directory if exists
        bmp_dir = current_dir / "BMPs"
        if bmp_dir.exists():
            try:
                shutil.rmtree(bmp_dir)
                logging.info("   Removed: BMPs/")
            except OSError as e:
                logging.warning(f"   Could not remove BMPs/: {e}")
    
    @staticmethod
    def recursive_copy(source: Path, destination: Path) -> bool:
        """Copia arquivos/diretórios recursivamente."""
        try:
            if not source.exists():
                logging.error(f"Source does not exist: {source}")
                return False
                
            if source.is_dir():
                # Usar shutil.copytree com dirs_exist_ok se disponível (Python 3.8+)
                if sys.version_info >= (3, 8):
                    shutil.copytree(source, destination, dirs_exist_ok=True)
                else:
                    for item in source.iterdir():
                        item_dest = destination / item.name
                        if item.is_dir():
                            FileManager.recursive_copy(item, item_dest)
                        else:
                            shutil.copy2(str(item), str(item_dest))
                return True
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                return True
        except Exception as e:
            logging.error(f"Error copying {source} to {destination}: {e}")
            return False
    
    @staticmethod
    def copy_console(selected_console: Dict[str, Any]) -> bool:
        """Copia os arquivos do console selecionado."""
        display_name = selected_console["display_name"]
        real_name = selected_console["real_name"]
        
        logging.info(f"Starting copy: {display_name}")
        
        # Caminho base para os consoles
        base_path = Path(__file__).parent / Config.CONSOLES_DIR
        
        # Copiar console principal
        console_source = base_path / real_name
        if not console_source.exists():
            logging.error(f"Directory not found: {console_source}")
            return False
        
        print(f"   Copying console: {real_name}")
        if not FileManager.recursive_copy(console_source, Path.cwd()):
            return False
        
        # Copiar recursos extras
        print("   Copying extra resources...")
        for resource in selected_console["extra_sources"]:
            resource_source = base_path / resource
            if resource_source.exists():
                print(f"      {resource}")
                if not FileManager.recursive_copy(resource_source, Path.cwd()):
                    logging.warning(f"Failed to copy {resource}")
            else:
                logging.warning(f"Extra resource not found: {resource}")
        
        return True

# ============================================================================
# Sistema de Menus
# ============================================================================

class MenuItem:
    """Representa um item de menu."""
    def __init__(self, text: str, value: Any):
        self.text = text
        self.value = value

class Menu:
    """Classe genérica para menus."""
    def __init__(self, title: str, items: List[MenuItem]):
        self.title = title
        self.items = items
    
    def display(self) -> Any:
        """Exibe o menu e retorna a escolha do usuário."""
        SystemUtils.clear_screen()
        
        # Mostrar cabeçalho
        for line in Messages.get_header():
            print(line)
        
        print(f"\n{self.title}")
        print("=" * 60)
        
        # Exibir itens
        for i, item in enumerate(self.items, 1):
            print(f"  {i}. {item.text}")
        
        print(f"  0. Exit / Sair")
        print()
        
        return self.get_choice()
    
    def get_choice(self) -> Any:
        """Obtém a escolha do usuário."""
        while True:
            try:
                choice = InputHandler.read_input("Enter choice / Digite sua escolha: ")
                if choice == '0':
                    return None
                
                idx = int(choice) - 1
                if 0 <= idx < len(self.items):
                    return self.items[idx].value
                else:
                    print(Messages.get_errors()["invalid_number"])
            except ValueError:
                print(Messages.get_errors()["invalid_input"])

# ============================================================================
# Gerenciador de Interface do Usuário
# ============================================================================

class UserInterface:
    """Gerencia a interface do usuário."""
    
    @staticmethod
    def show_introduction() -> None:
        """Exibe a introdução e instruções."""
        SystemUtils.clear_screen()
        
        # Cabeçalho
        for line in Messages.get_header():
            print(line)
        
        print("\nWELCOME TO DTB SELECTOR / BEM-VINDO AO SELETOR DTB")
        print("=" * 60)
        print()
        
        instructions = Messages.get_instructions()
        print(instructions["title"])
        for item in instructions["items"]:
            print(f"  {item}")
        
        print("\nTip: Press 'q' anytime to exit / Pressione 'q' para sair")
        
        try:
            response = InputHandler.read_input("\nPress Enter to continue / Pressione Enter: ")
            if response.lower() == 'q':
                print("\nGoodbye! Thank you for using DTB Selector! / Obrigado por usar!")
                sys.exit(0)
        except DTBSelectorError:
            raise
    
    @staticmethod
    def brand_menu(brands: List[str]) -> Optional[str]:
        """Menu de seleção de marca."""
        items = [MenuItem(brand, brand) for brand in brands]
        menu = Menu("SELECT A BRAND / SELECIONE UMA MARCA", items)
        return menu.display()
    
    @staticmethod
    def console_menu(consoles: List[Dict[str, Any]], brand: str) -> Optional[Dict[str, Any]]:
        """Menu de seleção de console para uma marca específica."""
        brand_consoles = []
        for console in consoles:
            for entry in console["brand_entries"]:
                if entry["brand"] == brand:
                    brand_consoles.append({
                        "console_config": console,
                        "display_name": entry["display_name"]
                    })
        
        if not brand_consoles:
            print(f"No consoles found for: {brand}")
            SystemUtils.wait_for_enter()
            return None
        
        items = []
        for console_info in brand_consoles:
            items.append(MenuItem(console_info['display_name'], console_info))
        
        menu = Menu(f"{brand} Consoles", items)
        selected = menu.display()
        
        if selected:
            console_config = selected["console_config"].copy()
            console_config["display_name"] = selected["display_name"]
            return console_config
        
        return None
    
    @staticmethod
    def language_menu() -> Optional[str]:
        """Menu de seleção de idioma."""
        items = []
        for code, info in Config.SUPPORTED_LANGUAGES.items():
            items.append(MenuItem(info["name"], code))
        
        items.append(MenuItem("Keep current setting / Manter configuração atual", None))
        menu = Menu("Language Selection / Seleção de Idioma", items)
        return menu.display()
    
    @staticmethod
    def apply_language(language: str) -> None:
        """Aplica o idioma selecionado."""
        logging.info("Configuring language...")
        
        # Remove existing language files
        current_dir = Path.cwd()
        for code, info in Config.SUPPORTED_LANGUAGES.items():
            if info["file"] and (current_dir / info["file"]).exists():
                try:
                    (current_dir / info["file"]).unlink()
                    logging.info(f"   Removed: {info['file']}")
                except OSError as e:
                    logging.warning(f"   Could not remove {info['file']}: {e}")
        
        # Create selected language file
        if language in Config.SUPPORTED_LANGUAGES:
            lang_info = Config.SUPPORTED_LANGUAGES[language]
            if lang_info["file"]:
                try:
                    (current_dir / lang_info["file"]).touch()
                    print(f"   Language set: {lang_info['name']}")
                except Exception as e:
                    logging.error(f"   Error creating {lang_info['file']} file: {e}")
            else:
                print(f"   Language set: {lang_info['name']} (default)")

# ============================================================================
# Função Principal
# ============================================================================

def main():
    """Função principal do programa."""
    # Configurar parsing de argumentos
    parser = argparse.ArgumentParser(description='DTB Selector Tool')
    parser.add_argument('--lang', choices=['en', 'cn', 'br'], 
                       help='Set initial language')
    parser.add_argument('--console', help='Pre-select console by name')
    parser.add_argument('--silent', action='store_true',
                       help='Run in silent mode (non-interactive)')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    args = parser.parse_args()
    
    # Configurar logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Inicializar estado da aplicação
    state = AppState()
    
    try:
        # Detectar sistema operacional
        state.operating_system = SystemUtils.detect_system()
        logger.info(f"System detected: {state.operating_system.upper()}")
        logger.info(f"Python: {sys.version.split()[0]}")
        
        # Carregar configuração
        state.consoles, state.brands = ConfigManager.load_configuration()
        
        # Modo silencioso (não implementado completamente, apenas exemplo)
        if args.silent:
            logger.info("Running in silent mode")
            # Aqui você implementaria a lógica para modo silencioso
            # Por exemplo, usando --console e --lang para fazer a seleção automaticamente
            return
        
        # Introdução
        UserInterface.show_introduction()
        
        # Seleção de marca
        brand = UserInterface.brand_menu(state.brands)
        if not brand:
            print("\nOperation cancelled. Goodbye! / Operação cancelada. Até logo!")
            return
        state.selected_brand = brand
        
        # Seleção de console
        console = UserInterface.console_menu(state.consoles, brand)
        if not console:
            print("\nNo console selected. / Nenhum console selecionado.")
            return
        state.selected_console = console
        
        # Confirmação
        print(f"\nConsole selected: {console['display_name']}")
        confirmation = InputHandler.read_input(
            "Continue with copy? (y/N) / Continuar com a cópia? (s/N): "
        ).strip().lower()
        
        if confirmation not in ['s', 'sim', 'y', 'yes']:
            print("\nOperation cancelled by user. / Operação cancelada pelo usuário.")
            return
        
        # Processamento
        FileManager.clean_destination_directory()
        
        if not FileManager.copy_console(console):
            print("\nError during file copy. / Erro durante a cópia dos arquivos.")
            return
        
        # Seleção de idioma
        language = args.lang or UserInterface.language_menu()
        if language:
            UserInterface.apply_language(language)
            state.selected_language = language
        
        # Mensagem de sucesso
        SystemUtils.clear_screen()
        for line in Messages.get_header():
            print(line)
        
        print("\nOperation Completed! / Operação Concluída!")
        print("=" * 60)
        
        success_msg = Messages.get_success(console['display_name'])
        print(f"\n{success_msg['title']}")
        print(success_msg['console'])
        
        # Mostrar idioma aplicado
        if state.selected_language:
            lang_name = Config.SUPPORTED_LANGUAGES[state.selected_language]['name']
            print(f"Language: {lang_name}")
        else:
            # Verificar se há arquivo de idioma existente
            for code, info in Config.SUPPORTED_LANGUAGES.items():
                if info["file"] and Path(info["file"]).exists():
                    print(f"Language: {info['name']} (kept)")
                    break
            else:
                print("Language: English (default)")
        
        print("\nNEXT STEPS / PRÓXIMOS PASSOS:")
        for step in success_msg['next_steps']:
            print(f"  {step}")
        
        SystemUtils.wait_for_enter()
        
    except DTBSelectorError as e:
        logger.error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation interrupted by user. Goodbye! / Operação interrompida. Até logo!")
        sys.exit(0)
    except Exception as e:
        logger.error(Messages.get_errors()["unexpected_error"].format(e))
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
