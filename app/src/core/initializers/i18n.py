from __future__ import annotations

import argparse
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.core.config import settings


class LocaleManager:
    DOMAINS = {
        "forms": {
            "input_dirs": ["src/domain/v1/forms", "src/domain/v1/schemas"],
            "keywords": ["_form", "form_gettext"],
            "output_file": "forms.pot",
        },
        "responses": {
            "input_dirs": ["src/domain/v1/routers"],
            "keywords": ["_response", "response_gettext"],
            "output_file": "responses.pot",
        },
        "general": {
            "input_dirs": ["src"],
            "keywords": ["_", "gettext", "ngettext:1,2"],
            "output_file": "messages.pot",
        },
    }

    def __init__(self, locale_dir: Optional[str] = None):
        """Initialize LocaleManager with locale directory."""
        self.locale_dir = Path(locale_dir or os.path.join(settings.BASE_DIR, "locales"))
        self.babel_config_path = os.path.join(settings.BASE_DIR, "babel.cfg")

    def ensure_directory_exists(self, path: Path) -> None:
        """Ensure directory exists, create if it doesn't."""
        path.mkdir(parents=True, exist_ok=True)

    def get_python_files(self, directories: List[str]) -> List[str]:
        """Get all Python files from specified directories."""
        python_files = []

        for directory in directories:
            dir_path = Path(directory)
            if dir_path.exists():
                python_files.extend(
                    [str(file) for file in dir_path.rglob("*.py") if not file.name.startswith("__pycache__")]
                )
            else:
                print(f"Warning: Directory {directory} does not exist, skipping...")

        return python_files

    def extract_domain_messages(self, domain: str, config: Dict) -> None:
        """Extract messages for a specific domain."""
        print(f"\n--- Extracting messages for domain: {domain} ---")

        python_files = self.get_python_files(config["input_dirs"])

        if not python_files:
            print(f"No Python files found for domain {domain}")
            return

        pot_file = self.locale_dir / config["output_file"]

        cmd = [
            "pybabel",
            "extract",
            "--mapping-file",
            self.babel_config_path,
            "--keywords",
            " ".join(config["keywords"]),
            "--output",
            str(pot_file),
            "--input-dirs",
            " ".join(config["input_dirs"]),
            "--sort-by-file",
            "--add-comments=TRANSLATORS:",
            "--strip-comments",
            "--width=120",
        ]

        cmd.extend(config["input_dirs"])

        try:
            subprocess.run(cmd, check=True)
            print(f"Successfully extracted messages to {pot_file}")

            if pot_file.exists() and pot_file.stat().st_size > 0:
                print(f"Generated {pot_file} with messages")
            else:
                print(f"Warning: {pot_file} is empty or was not created")

        except subprocess.CalledProcessError as e:
            print(f"Error extracting messages for {domain}: {e}")
        except FileNotFoundError:
            print("Error: pybabel command not found. Make sure Babel is installed.")
            print("Install with: pip install babel")

    def update_po_files(self, domain: str) -> None:
        """Update .po files from .pot template for all locales."""
        pot_file = self.locale_dir / self.DOMAINS[domain]["output_file"]

        if not pot_file.exists():
            print(f"POT file {pot_file} does not exist, skipping PO update for {domain}")
            return

        for locale in settings.SUPPORTED_LOCALES:
            locale_path = self.locale_dir / locale / "LC_MESSAGES"
            self.ensure_directory_exists(locale_path)

            po_file = locale_path / f"{domain}.po"

            if po_file.exists():
                cmd = [
                    "pybabel",
                    "update",
                    "--input-file",
                    str(pot_file),
                    "--output-file",
                    str(po_file),
                    "--locale",
                    locale,
                    "--update-header-comment",
                ]
                action = "Updated"
            else:
                cmd = [
                    "pybabel",
                    "init",
                    "--input-file",
                    str(pot_file),
                    "--output-dir",
                    str(self.locale_dir),
                    "--locale",
                    locale,
                    "--domain",
                    domain,
                ]
                action = "Initialized"

            try:
                subprocess.run(cmd, check=True)
                print(f"{action} {locale} translation for {domain}: {po_file}")
            except subprocess.CalledProcessError as e:
                print(f"Error updating {locale} PO file for {domain}: {e}")

    def extract_all_messages(self) -> None:
        """Extract messages for all domains."""
        self.ensure_directory_exists(self.locale_dir)

        print(f"Extracting messages to: {self.locale_dir}")
        print(f"Supported locales: {', '.join(settings.SUPPORTED_LOCALES)}")

        for domain, config in self.DOMAINS.items():
            self.extract_domain_messages(domain, config)
            self.update_po_files(domain)

        print("\n--- Extraction Summary ---")
        print(f"Domains processed: {', '.join(self.DOMAINS.keys())}")
        print(f"Locales: {', '.join(settings.SUPPORTED_LOCALES)}")
        print("Next steps:")
        print("1. Translate the messages in the .po files")
        print("2. Run the compile command to generate .mo files")
        print("3. Configure your FastAPI app to use the translations")

    def validate_po_file(self, po_file: Path) -> Tuple[bool, Optional[str]]:
        """Validate .po file for syntax errors before compilation."""
        try:
            result = subprocess.run(
                ["msgfmt", "--check", str(po_file)],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return True, None
            else:
                return False, result.stderr.strip()
        except FileNotFoundError:
            return False, "msgfmt command not found. Install gettext tools."

    def compile_po_file(self, po_file: Path) -> Tuple[bool, str, Optional[str]]:
        """Compile a single .po file to .mo file."""
        mo_file = po_file.with_suffix(".mo")

        if not po_file.exists():
            return False, f"PO file {po_file} does not exist", None

        if po_file.stat().st_size == 0:
            return False, f"PO file {po_file} is empty", None

        is_valid, validation_error = self.validate_po_file(po_file)
        if not is_valid:
            return False, f"Invalid PO file {po_file}", validation_error

        if mo_file.exists() and mo_file.stat().st_mtime > po_file.stat().st_mtime:
            return True, f"Skipped {mo_file} (up to date)", None

        try:
            result = subprocess.run(
                ["msgfmt", "--statistics", "--verbose", str(po_file), "-o", str(mo_file)],
                capture_output=True,
                text=True,
                check=True,
            )

            stats = result.stderr.strip() if result.stderr else "compiled successfully"
            return True, f"Compiled {mo_file} - {stats}", None

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            return False, f"Failed to compile {po_file}", error_msg
        except FileNotFoundError:
            return False, f"msgfmt not found for {po_file}", "Install gettext tools"

    def find_po_files(self) -> List[Path]:
        """Find all .po files in the locale directory."""
        if not self.locale_dir.exists():
            print(f"Locale directory {self.locale_dir} does not exist.")
            return []

        po_files = list(self.locale_dir.glob("**/LC_MESSAGES/*.po"))

        if not po_files:
            print(f"No .po files found in {self.locale_dir}")
            return []

        return sorted(po_files)

    def compile_locales(self, max_workers: int = 4) -> None:
        """Compile all .po files to .mo files in parallel."""
        po_files = self.find_po_files()

        if not po_files:
            return

        print(f"Found {len(po_files)} .po files to process")
        print(f"Using {max_workers} worker threads")
        print("-" * 60)

        successful_compilations = 0
        failed_compilations = 0
        skipped_compilations = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(self.compile_po_file, po_file): po_file for po_file in po_files}

            for future in as_completed(future_to_file):
                po_file = future_to_file[future]
                try:
                    success, message, error = future.result()

                    if success:
                        if "up to date" in message:
                            skipped_compilations += 1
                            print(f"{message}")
                        else:
                            successful_compilations += 1
                            print(f"{message}")
                    else:
                        failed_compilations += 1
                        print(f"{message}")
                        if error:
                            print(f"   Error details: {error}")

                except Exception as e:
                    failed_compilations += 1
                    print(f"Unexpected error processing {po_file}: {e}")

        # Print summary
        print("-" * 60)
        print("Compilation Summary:")
        print(f"Successful: {successful_compilations}")
        print(f"Skipped (up to date): {skipped_compilations}")
        print(f"Failed: {failed_compilations}")
        print(f"Total processed: {len(po_files)}")

        if failed_compilations > 0:
            print("\nSome compilations failed. Check the error messages above.")
            print("Common issues:")
            print("  - Install gettext tools: sudo apt-get install gettext (Ubuntu/Debian)")
            print("  - Install gettext tools: brew install gettext (macOS)")
            print("  - Check .po file syntax with: msgfmt --check <file.po>")


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description="Manage locales: extract messages and compile translations")
    parser.add_argument(
        "action", choices=["extract", "compile"], help="Action to perform: extract messages or compile translations"
    )
    parser.add_argument(
        "--locale-dir", type=str, help="Custom locale directory path (default: settings.BASE_DIR/locales)"
    )
    parser.add_argument(
        "--max-workers", type=int, default=4, help="Maximum number of worker threads for compilation (default: 4)"
    )

    args = parser.parse_args()

    locale_manager = LocaleManager(args.locale_dir)

    if args.action == "extract":
        print("Starting message extraction...")
        locale_manager.extract_all_messages()
    elif args.action == "compile":
        print("Starting locale compilation...")
        locale_manager.compile_locales(args.max_workers)

    print("\nOperation completed!")


if __name__ == "__main__":
    main()
