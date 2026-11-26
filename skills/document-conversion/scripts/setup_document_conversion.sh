#!/bin/bash
# Setup script for document conversion tools

set -e

echo "Setting up document conversion tools..."

# Create virtual environment (recommended)
if [ ! -d ".venv-docs" ]; then
    python3 -m venv .venv-docs
fi

source .venv-docs/bin/activate

# Install secure, vetted packages
echo "Installing packages..."
pip install --upgrade pip

# Core conversion libraries
pip install PyMuPDF        # PDF handling
pip install python-docx    # Word documents
pip install python-pptx    # PowerPoint
pip install pandas         # Excel/data
pip install openpyxl       # Excel engine
pip install tabulate       # Markdown tables
pip install markitdown     # Microsoft tool (optional)

echo "Setup complete!"
echo "Activate environment: source .venv-docs/bin/activate"
echo "Usage: python scripts/convert_to_markdown.py <file>"
