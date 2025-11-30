#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DTB Selector - R36 Clone Device Selection Tool
Original creator: LCDYK (https://lcdyk0517.github.io/dtbTools.html)
Modified by: Leonardo Bruno (https://github.com/souza-lb/arkos4clone-leonardo)
Multi-language support with English/Portuguese
28/11/2025 21:34:00
"""

import os
import sys
import shutil
import glob
import json
from pathlib import Path

# ===================== GLOBAL CONFIGURATION =====================
OPERATING_SYSTEM = None
CONSOLES = []
BRANDS = []

# ===================== COLOR SYSTEM =====================
class Colors:
    """ANSI color codes for terminal"""
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'

class Messages:
    """Centralized message system with bilingual support"""
    
    @staticmethod
    def get_header():
        return [
            "╔═══════════════════════════════════════════════════════════════╗",
            "║                                                               ║",
            "║                      DTB SELECTOR TOOL                        ║",
            "║                R36 Clone Device Configuration                 ║",
            "║                                                               ║",
            "║    Original creator: LCDYK                                    ║",
            "║    GitHub: https://github.com/lcdyk0517/arkos4clone           ║",
            "║    Modified by: Leonardo Bruno                                ║",
            "║    GitHub: https://github.com/souza-lb/arkos4clone-leonardo   ║",
            "║                                                               ║",
            "╚═══════════════════════════════════════════════════════════════╝"
        ]
    
    @staticmethod
    def get_instructions():
        return {
            "title": "📋 IMPORTANT INSTRUCTIONS / INSTRUÇÕES IMPORTANTES",
            "items": [
                "• Only listed R36 clones are supported / Apenas clones R36 listados são suportados",
                "• Use the identification tool to find your device / Use a ferramenta de identificação",
                "• Original EmuELEC dtb files will BRICK your boot! / Arquivos dtb originais danificam o sistema!",
                "• Tool: https://lcdyk0517.github.io/dtbTools.html"
            ]
        }
    
    @staticmethod
    def get_success(console_name):
        return {
            "title": "✅ OPERATION COMPLETED SUCCESSFULLY / OPERAÇÃO CONCLUÍDA COM SUCESSO",
            "console": f"📋 Console: {console_name}",
            "next_steps": [
                "• Verify files were copied correctly / Verifique se os arquivos foram copiados",
                "• Boot your device with the new configuration / Inicialize o dispositivo",
                "• Report any issues encountered / Relate problemas encontrados"
            ]
        }
    
    @staticmethod
    def get_errors():
        return {
            "file_not_found": "❌ consoles.json file not found! / Arquivo consoles.json não encontrado!",
            "check_file": "💡 Make sure the file is in the script directory. / Certifique-se que o arquivo está no diretório.",
            "json_error": "❌ Error reading consoles.json: {}",
            "invalid_structure": "❌ Invalid structure in consoles.json: {}",
            "operation_cancelled": "Operation cancelled by user. / Operação cancelada pelo usuário.",
            "invalid_input": "❌ Please enter a valid number. / Por favor digite um número válido.",
            "invalid_number": "❌ Invalid number. Try again. / Número inválido. Tente novamente."
        }

# ===================== SYSTEM UTILITIES =====================
class SystemUtils:
    """System operation utilities"""
    
    @staticmethod
    def detect_system():
        """Detect operating system"""
        if os.name == 'nt':
            return 'windows'
        return 'linux' if sys.platform != 'darwin' else 'macos'
    
    @staticmethod
    def supports_colors():
        """Check if terminal supports ANSI colors"""
        if OPERATING_SYSTEM == 'windows':
            return ('ANSICON' in os.environ or 
                    'WT_SESSION' in os.environ or
                    'TERM' in os.environ)
        return sys.stdout.isatty()
    
    @staticmethod
    def color(text, color_code):
        """Apply color to text if supported"""
        if SystemUtils.supports_colors():
            return f"{color_code}{text}{Colors.RESET}"
        return text
    
    @staticmethod
    def clear_screen():
        """Clear terminal screen"""
        os.system('cls' if OPERATING_SYSTEM == 'windows' else 'clear')
    
    @staticmethod
    def wait_for_enter():
        """Wait for user to press Enter"""
        try:
            message = SystemUtils.color("\n⏎ Press Enter to continue... / Pressione Enter para continuar... ", Colors.BOLD)
            input(message)
        except (KeyboardInterrupt, EOFError):
            print(SystemUtils.color(Messages.get_errors()["operation_cancelled"], Colors.RED))
            sys.exit(0)

# ===================== USER INTERFACE =====================
class UserInterface:
    """Manages user interface and interactions"""
    
    @staticmethod
    def show_header(title=""):
        """Display customized header"""
        SystemUtils.clear_screen()
        
        # Header
        header = Messages.get_header()
        for line in header:
            print(SystemUtils.color(line, Colors.BLUE))
        
        if title:
            print(SystemUtils.color(f"\n🔧 {title}", Colors.BOLD + Colors.GREEN))
            print(SystemUtils.color("═" * 60, Colors.CYAN))
        print()
    
    @staticmethod
    def show_introduction():
        """Display introduction and instructions"""
        UserInterface.show_header("DTB Selector - Choose Your Console")
        
        instructions = Messages.get_instructions()
        
        print(SystemUtils.color("🎯 WELCOME TO DTB SELECTOR / BEM-VINDO AO SELETOR DTB", Colors.BOLD + Colors.GREEN))
        print(SystemUtils.color("═" * 50, Colors.CYAN))
        print()
        
        print(SystemUtils.color(instructions["title"], Colors.BOLD + Colors.YELLOW))
        for item in instructions["items"]:
            print(SystemUtils.color(f"  {item}", Colors.BLUE))
        
        print(SystemUtils.color("\n💡 Tip: Press 'q' anytime to exit / Pressione 'q' para sair", Colors.YELLOW))
        
        try:
            prompt = SystemUtils.color("\n⏎ Press Enter to continue / Pressione Enter: ", Colors.BOLD)
            response = input(prompt).strip().lower()
            if response == 'q':
                print(SystemUtils.color("\n👋 Goodbye! Thank you for using DTB Selector! / Obrigado por usar!", Colors.GREEN))
                sys.exit(0)
        except (KeyboardInterrupt, EOFError):
            print(SystemUtils.color(Messages.get_errors()["operation_cancelled"], Colors.RED))
            sys.exit(0)
    
    @staticmethod
    def read_input(message):
        """Safely read user input"""
        try:
            return input(SystemUtils.color(message, Colors.BOLD)).strip()
        except (KeyboardInterrupt, EOFError):
            print(SystemUtils.color(Messages.get_errors()["operation_cancelled"], Colors.RED))
            sys.exit(0)

# ===================== CONFIGURATION MANAGER =====================
class ConfigManager:
    """Manages configuration loading"""
    
    @staticmethod
    def load_configuration():
        """Load console configuration from JSON file"""
        try:
            config_path = Path(__file__).parent / "consoles.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config["consoles"], config["brands"]
        except FileNotFoundError:
            print(SystemUtils.color(Messages.get_errors()["file_not_found"], Colors.RED))
            print(SystemUtils.color(Messages.get_errors()["check_file"], Colors.BLUE))
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(SystemUtils.color(Messages.get_errors()["json_error"].format(e), Colors.RED))
            sys.exit(1)
        except KeyError as e:
            print(SystemUtils.color(Messages.get_errors()["invalid_structure"].format(e), Colors.RED))
            sys.exit(1)

# ===================== FILE MANAGER =====================
class FileManager:
    """Manages file operations"""
    
    @staticmethod
    def clean_destination_directory():
        """Clean previous files from current directory"""
        print(SystemUtils.color("\n🧹 Cleaning destination directory... / Limpando diretório...", Colors.CYAN))
        
        patterns = ["*.dtb", "*.ini", "*.orig", "*.tony", ".cn", ".en", ".br"]
        files_removed = 0
        
        for pattern in patterns:
            try:
                for file in glob.glob(pattern):
                    print(SystemUtils.color(f"   📄 Removing: {file}", Colors.YELLOW))
                    try:
                        os.remove(file)
                        files_removed += 1
                    except OSError as e:
                        print(SystemUtils.color(f"   ⚠️  Warning: Could not remove {file}: {e}", Colors.YELLOW))
            except Exception as e:
                print(SystemUtils.color(f"   ⚠️  Error processing pattern {pattern}: {e}", Colors.YELLOW))
        
        # Remove BMPs directory if exists
        if os.path.exists("BMPs"):
            print(SystemUtils.color("   📁 Removing: BMPs/", Colors.YELLOW))
            try:
                shutil.rmtree("BMPs")
                print(SystemUtils.color("   ✅ BMPs directory removed", Colors.GREEN))
            except OSError as e:
                print(SystemUtils.color(f"   ⚠️  Warning: Could not remove BMPs/: {e}", Colors.YELLOW))
        
        if files_removed == 0:
            print(SystemUtils.color("   ✅ No previous files found", Colors.GREEN))
    
    @staticmethod
    def recursive_copy(source, destination):
        """Copy files/directories recursively"""
        try:
            source_path = Path(source)
            destination_path = Path(destination)
            
            if not source_path.exists():
                print(SystemUtils.color(f"   ❌ Source does not exist: {source}", Colors.RED))
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
            print(SystemUtils.color(f"   ❌ Error copying {source} to {destination}: {e}", Colors.RED))
            return False
    
    @staticmethod
    def copy_console(selected_console):
        """Copy files for selected console"""
        display_name = selected_console["display_name"]
        real_name = selected_console["real_name"]
        
        print(SystemUtils.color(f"\n🚀 Starting copy: {display_name}", Colors.CYAN))
        
        # Copy main console
        console_source = os.path.join("consoles", real_name)
        if os.path.exists(console_source):
            print(SystemUtils.color(f"   📂 Copying console: {real_name}", Colors.GREEN))
            if not FileManager.recursive_copy(console_source, "."):
                return False
        else:
            print(SystemUtils.color(f"   ❌ Directory not found: {console_source}", Colors.RED))
            return False
        
        # Copy extra resources
        print(SystemUtils.color("   📦 Copying extra resources...", Colors.CYAN))
        for resource in selected_console["extra_sources"]:
            resource_source = os.path.join("consoles", resource)
            if os.path.exists(resource_source):
                print(SystemUtils.color(f"      📁 {resource}", Colors.GREEN))
                if not FileManager.recursive_copy(resource_source, "."):
                    print(SystemUtils.color(f"      ⚠️  Warning: Failed to copy {resource}", Colors.YELLOW))
            else:
                print(SystemUtils.color(f"      ⚠️  Extra resource not found: {resource}", Colors.YELLOW))
        
        return True

# ===================== MENU SYSTEM =====================
class MenuManager:
    """Manages all system menus"""
    
    @staticmethod
    def brand_menu():
        """Brand selection menu"""
        while True:
            UserInterface.show_header("Brand Selection")
            
            print(SystemUtils.color("┌────────────────────────────────────────┐", Colors.CYAN))
            print(SystemUtils.color("│           SELECT A BRAND               │", Colors.BOLD + Colors.GREEN))
            print(SystemUtils.color("└────────────────────────────────────────┘", Colors.CYAN))
            print()
            
            for i, brand in enumerate(BRANDS, 1):
                print(SystemUtils.color(f"  {i}. {brand}", Colors.WHITE))
            
            print(SystemUtils.color(f"\n  0. 🚪 Exit / Sair", Colors.RED))
            print()
            
            choice = UserInterface.read_input("🎯 Enter brand number / Digite o número da marca: ")
            
            if not choice:
                continue
                
            try:
                choice_num = int(choice)
                if choice_num == 0:
                    return None
                elif 1 <= choice_num <= len(BRANDS):
                    return BRANDS[choice_num - 1]
                else:
                    print(SystemUtils.color(Messages.get_errors()["invalid_number"], Colors.RED))
                    SystemUtils.wait_for_enter()
            except ValueError:
                print(SystemUtils.color(Messages.get_errors()["invalid_input"], Colors.RED))
                SystemUtils.wait_for_enter()
    
    @staticmethod
    def console_menu(selected_brand):
        """Console selection menu for specific brand"""
        brand_consoles = []
        for console in CONSOLES:
            for entry in console["brand_entries"]:
                if entry["brand"] == selected_brand:
                    brand_consoles.append({
                        "console_config": console,
                        "display_name": entry["display_name"]
                    })
        
        if not brand_consoles:
            print(SystemUtils.color(f"❌ No consoles found for: {selected_brand}", Colors.RED))
            SystemUtils.wait_for_enter()
            return None
        
        while True:
            UserInterface.show_header(f"{selected_brand} Consoles")
            
            print(SystemUtils.color("┌────────────────────────────────────────┐", Colors.CYAN))
            print(SystemUtils.color("│          SELECT CONSOLE                │", Colors.BOLD + Colors.GREEN))
            print(SystemUtils.color("└────────────────────────────────────────┘", Colors.CYAN))
            print()
            
            for i, console_info in enumerate(brand_consoles, 1):
                print(SystemUtils.color(f"  {i}. {console_info['display_name']}", Colors.WHITE))
            
            print(SystemUtils.color(f"\n  0. ↩️  Back / Voltar", Colors.RED))
            print()
            
            choice = UserInterface.read_input("🎯 Enter console number / Digite o número do console: ")
            
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
                    print(SystemUtils.color(Messages.get_errors()["invalid_number"], Colors.RED))
                    SystemUtils.wait_for_enter()
            except ValueError:
                print(SystemUtils.color(Messages.get_errors()["invalid_input"], Colors.RED))
                SystemUtils.wait_for_enter()
    
    @staticmethod
    def language_menu():
        """Language selection menu"""
        while True:
            UserInterface.show_header("Language Selection")
            
            print(SystemUtils.color("🌐 LANGUAGE FILE SYSTEM:", Colors.YELLOW + Colors.BOLD))
            print(SystemUtils.color("   • English    → No file (default)", Colors.BLUE))
            print(SystemUtils.color("   • Chinese    → .cn file", Colors.BLUE))
            print(SystemUtils.color("   • Portuguese → .br file", Colors.BLUE))
            print()
            print(SystemUtils.color("Select language / Selecione o idioma:", Colors.BOLD + Colors.GREEN))
            print(SystemUtils.color("  1. 🇺🇸 English - No file (default)", Colors.WHITE))
            print(SystemUtils.color("  2. 🇨🇳 中文 (Chinese) - .cn file", Colors.WHITE))
            print(SystemUtils.color("  3. 🇧🇷 Português Brasil - .br file", Colors.WHITE))
            print(SystemUtils.color(f"  0. ⚙️  Keep current setting", Colors.RED))
            print()
            
            choice = UserInterface.read_input("🎯 Enter your choice / Digite sua escolha: ")
            
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
                    print(SystemUtils.color("❌ Invalid choice. / Escolha inválida.", Colors.RED))
                    SystemUtils.wait_for_enter()
            except ValueError:
                print(SystemUtils.color(Messages.get_errors()["invalid_input"], Colors.RED))
                SystemUtils.wait_for_enter()
    
    @staticmethod
    def apply_language(language):
        """Apply selected language configuration"""
        print(SystemUtils.color("\n🌐 Configuring language...", Colors.CYAN))
        
        # Remove existing language files
        for lang_file in [".cn", ".br", ".en"]:
            if os.path.exists(lang_file):
                try:
                    os.remove(lang_file)
                    print(SystemUtils.color(f"   🗑️  Removed: {lang_file}", Colors.YELLOW))
                except OSError as e:
                    print(SystemUtils.color(f"   ⚠️  Could not remove {lang_file}: {e}", Colors.YELLOW))
        
        # Create selected language file
        if language == "en":
            print(SystemUtils.color("   🇺🇸 Language set: English", Colors.GREEN))
            print(SystemUtils.color("   ✅ No file created (English default)", Colors.GREEN))
        elif language == "cn":
            try:
                with open(".cn", "w", encoding='utf-8') as f:
                    f.write("chinese")
                print(SystemUtils.color("   🇨🇳 Language set: Chinese", Colors.GREEN))
                print(SystemUtils.color("   ✅ .cn file created", Colors.GREEN))
            except Exception as e:
                print(SystemUtils.color(f"   ❌ Error creating .cn file: {e}", Colors.RED))
        elif language == "br":
            try:
                with open(".br", "w", encoding='utf-8') as f:
                    f.write("portugues_brasil")
                print(SystemUtils.color("   🇧🇷 Language set: Portuguese Brazil", Colors.GREEN))
                print(SystemUtils.color("   ✅ .br file created", Colors.GREEN))
            except Exception as e:
                print(SystemUtils.color(f"   ❌ Error creating .br file: {e}", Colors.RED))

# ===================== MAIN FUNCTION =====================
def main():
    """Main program function"""
    global OPERATING_SYSTEM, CONSOLES, BRANDS
    
    try:
        # Initialization
        OPERATING_SYSTEM = SystemUtils.detect_system()
        CONSOLES, BRANDS = ConfigManager.load_configuration()
        
        print(SystemUtils.color(f"🔍 System detected: {OPERATING_SYSTEM.upper()}", Colors.CYAN))
        print(SystemUtils.color(f"🐍 Python: {sys.version.split()[0]}", Colors.BLUE))
        
        # Introduction
        UserInterface.show_introduction()
        
        # Brand selection
        brand = MenuManager.brand_menu()
        if not brand:
            print(SystemUtils.color("\n👋 Operation cancelled. Goodbye! / Operação cancelada. Até logo!", Colors.GREEN))
            return
        
        # Console selection
        console = MenuManager.console_menu(brand)
        if not console:
            print(SystemUtils.color("\n👋 No console selected. / Nenhum console selecionado.", Colors.GREEN))
            return
        
        # Confirmation
        print(SystemUtils.color(f"\n✅ Console selected: {console['display_name']}", Colors.GREEN))
        confirmation = UserInterface.read_input("🔄 Continue with copy? (y/N) / Continuar com a cópia? (s/N): ").strip().lower()
        
        if confirmation not in ['s', 'sim', 'y', 'yes']:
            print(SystemUtils.color("\n👋 Operation cancelled by user. / Operação cancelada pelo usuário.", Colors.GREEN))
            return
        
        # Processing
        FileManager.clean_destination_directory()
        
        if not FileManager.copy_console(console):
            print(SystemUtils.color("\n❌ Error during file copy. / Erro durante a cópia dos arquivos.", Colors.RED))
            return
        
        # Language
        language = MenuManager.language_menu()
        if language:
            MenuManager.apply_language(language)
        
        # Success
        UserInterface.show_header("✅ Operation Completed!")
        
        success_msg = Messages.get_success(console['display_name'])
        print(SystemUtils.color("╔══════════════════════════════════════════════════════╗", Colors.GREEN))
        print(SystemUtils.color("║                  SUCCESS!                            ║", Colors.BOLD + Colors.GREEN))
        print(SystemUtils.color("╚══════════════════════════════════════════════════════╝", Colors.GREEN))
        print()
        print(SystemUtils.color(success_msg["title"], Colors.BOLD + Colors.GREEN))
        print(SystemUtils.color(success_msg["console"], Colors.BLUE))
        
        # Language applied
        if language == "en":
            print(SystemUtils.color("🌐 Language: English - No file", Colors.BLUE))
        elif language == "cn":
            print(SystemUtils.color("🌐 Language: Chinese - .cn file", Colors.BLUE))
        elif language == "br":
            print(SystemUtils.color("🌐 Language: Portuguese Brazil - .br file", Colors.BLUE))
        else:
            if os.path.exists(".cn"):
                print(SystemUtils.color("🌐 Language: Chinese (kept) - .cn file", Colors.BLUE))
            elif os.path.exists(".br"):
                print(SystemUtils.color("🌐 Language: Portuguese Brazil (kept) - .br file", Colors.BLUE))
            else:
                print(SystemUtils.color("🌐 Language: English (kept) - No file", Colors.BLUE))
        
        print(SystemUtils.color("\n📋 NEXT STEPS / PRÓXIMOS PASSOS:", Colors.BOLD + Colors.CYAN))
        for step in success_msg["next_steps"]:
            print(SystemUtils.color(f"  {step}", Colors.BLUE))
        
        # Final verification
        print(SystemUtils.color("\n🔍 FILE VERIFICATION / VERIFICAÇÃO:", Colors.BOLD))
        if os.path.exists(".cn"):
            print(SystemUtils.color("   📄 .cn: PRESENT → Chinese language", Colors.GREEN))
        else:
            print(SystemUtils.color("   📄 .cn: absent", Colors.BLUE))
            
        if os.path.exists(".br"):
            try:
                with open(".br", "r", encoding='utf-8') as f:
                    content = f.read().strip()
                print(SystemUtils.color("   📄 .br: PRESENT → Portuguese Brazil", Colors.GREEN))
                print(SystemUtils.color(f"   📝 Content: {content}", Colors.CYAN))
            except Exception as e:
                print(SystemUtils.color(f"   📄 .br: PRESENT (read error: {e})", Colors.GREEN))
        else:
            print(SystemUtils.color("   📄 .br: absent", Colors.BLUE))
            
        if not os.path.exists(".cn") and not os.path.exists(".br"):
            print(SystemUtils.color("   🌐 No files: English language (default)", Colors.GREEN))
        
        SystemUtils.wait_for_enter()
        
    except KeyboardInterrupt:
        print(SystemUtils.color("\n\n👋 Operation interrupted by user. Goodbye! / Operação interrompida. Até logo!", Colors.GREEN))
    except Exception as e:
        print(SystemUtils.color(f"\n❌ Unexpected error: {e}", Colors.RED))
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
