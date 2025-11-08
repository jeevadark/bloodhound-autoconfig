#!/bin/bash
# BloodHound-AutoConfig - Quick Setup Script
# This script sets up the complete GitHub repository structure

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║         BloodHound-AutoConfig Setup Script                       ║
║         GitHub Repository Initialization                         ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}[!] Git is not installed. Please install git first.${NC}"
    exit 1
fi

# Get user information
echo -e "${YELLOW}[*] Repository Configuration${NC}"
read -p "Enter your GitHub username: " GITHUB_USER
read -p "Enter repository name [bloodhound-autoconfig]: " REPO_NAME
REPO_NAME=${REPO_NAME:-bloodhound-autoconfig}

read -p "Enter your name (for LICENSE): " AUTHOR_NAME
read -p "Enter your email: " AUTHOR_EMAIL

# Create directory structure
echo -e "${BLUE}[*] Creating directory structure...${NC}"
mkdir -p examples scripts docs tests/fixtures

# Create .gitignore
echo -e "${BLUE}[*] Creating .gitignore...${NC}"
cat > .gitignore << 'EOF'
# Byte-compiled / optimized
__pycache__/
*.py[cod]
*$py.class

# Distribution / packaging
dist/
build/
*.egg-info/

# Environments
.env
.venv
venv/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Project specific
*.nmap
*.xml
scan_*.txt
domain_controllers_*.json
bloodhound_commands_*.sh
bloodhound_*.zip
credentials.txt
passwords.txt
*.log
tmp/
EOF

# Create LICENSE
echo -e "${BLUE}[*] Creating LICENSE (MIT)...${NC}"
YEAR=$(date +%Y)
cat > LICENSE << EOF
MIT License

Copyright (c) $YEAR $AUTHOR_NAME

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF

# Create CHANGELOG.md
echo -e "${BLUE}[*] Creating CHANGELOG.md...${NC}"
cat > CHANGELOG.md << 'EOF'
# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2024-11-08

### Added
- Initial release
- Automated Domain Controller discovery from Nmap scans
- Support for 1000+ IP addresses
- Multi-domain and multi-forest support
- JSON export functionality
- Interactive command generation
- Shell script generation for batch execution
- Color-coded terminal output
- Progress indicators for large scans
- Comprehensive error handling
EOF

# Create helper scripts
echo -e "${BLUE}[*] Creating helper scripts...${NC}"

# Quick scan script
cat > scripts/quick_scan.sh << 'EOF'
#!/bin/bash
# Quick AD Port Scan Script
# Usage: ./quick_scan.sh targets.txt

if [ -z "$1" ]; then
    echo "Usage: $0 <targets_file>"
    exit 1
fi

OUTPUT="scan_$(date +%Y%m%d_%H%M%S).txt"

echo "[*] Starting AD port scan..."
echo "[*] Targets: $1"
echo "[*] Output: $OUTPUT"

nmap -p 88,389,636,445,3268,3269 \
     -sV \
     -sC \
     --script ldap-rootdse \
     -iL "$1" \
     -oN "$OUTPUT" \
     --open

echo "[+] Scan complete: $OUTPUT"
echo "[*] Run: python3 ../bloodhound-autoconfig.py $OUTPUT"
EOF
chmod +x scripts/quick_scan.sh

# Batch collection script
cat > scripts/batch_collect.sh << 'EOF'
#!/bin/bash
# Batch BloodHound Collection
# Collects from all discovered DCs

if [ ! -f domain_controllers_*.json ]; then
    echo "[!] No DC JSON file found. Run bloodhound-autoconfig.py first."
    exit 1
fi

# Get credentials
read -p "Username: " USERNAME
read -sp "Password: " PASSWORD
echo

# Extract DCs and run BloodHound
jq -r '.domain_controllers[] | "\(.ip)|\(.domain)"' domain_controllers_*.json | while IFS='|' read -r ip domain; do
    echo "[*] Collecting from $ip ($domain)..."
    bloodhound-python -u "$USERNAME" -p "$PASSWORD" -d "$domain" -dc "$ip" -c All --zip
done

echo "[+] Collection complete!"
EOF
chmod +x scripts/batch_collect.sh

# Create examples README
cat > examples/README.md << 'EOF'
# Example Nmap Outputs

This directory contains sample Nmap scan results for testing.

## Usage

```bash
python3 ../bloodhound-autoconfig.py sample_scan.txt
```

## Creating Samples

Scan your test lab and save here:
```bash
nmap -p 88,389,445 -sV targets.txt -oN sample_scan.txt
```
EOF

# Initialize git repository
echo -e "${BLUE}[*] Initializing git repository...${NC}"
git init
git config user.name "$AUTHOR_NAME"
git config user.email "$AUTHOR_EMAIL"

# Initial commit
echo -e "${BLUE}[*] Creating initial commit...${NC}"
git add .
git commit -m "Initial commit: BloodHound-AutoConfig v1.0

- Automated DC discovery from Nmap scans
- Support for large-scale networks (1000+ IPs)
- Multi-domain and forest support
- JSON and shell script output
- Interactive and batch modes
- Comprehensive documentation"

# Add remote (if user wants)
echo -e "${YELLOW}[?] Do you want to add GitHub remote now? (y/n)${NC}"
read -p "> " ADD_REMOTE

if [ "$ADD_REMOTE" = "y" ] || [ "$ADD_REMOTE" = "Y" ]; then
    git remote add origin "https://github.com/$GITHUB_USER/$REPO_NAME.git"
    git branch -M main
    
    echo -e "${GREEN}[+] Remote added: https://github.com/$GITHUB_USER/$REPO_NAME.git${NC}"
    echo -e "${YELLOW}[*] Create the repository on GitHub first, then run:${NC}"
    echo -e "    ${BLUE}git push -u origin main${NC}"
fi

# Create tag
echo -e "${BLUE}[*] Creating version tag...${NC}"
git tag -a v1.0.0 -m "BloodHound-AutoConfig v1.0.0 - Initial Release"

# Summary
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    Setup Complete! ✓                             ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "  1. Copy your main script to: ${BLUE}bloodhound-autoconfig.py${NC}"
echo -e "  2. Copy documentation to: ${BLUE}README.md, CONTRIBUTING.md, EXAMPLES.md${NC}"
echo -e "  3. Create GitHub repository: ${BLUE}https://github.com/new${NC}"
echo -e "  4. Push to GitHub: ${BLUE}git push -u origin main${NC}"
echo -e "  5. Push tags: ${BLUE}git push origin v1.0.0${NC}"
echo -e "  6. Create release on GitHub"
echo ""
echo -e "${GREEN}Repository Structure:${NC}"
tree -L 2 2>/dev/null || find . -maxdepth 2 -not -path '*/\.*' | sed 's|[^/]*/| |g'
echo ""
echo -e "${YELLOW}Happy hacking! 🎯${NC}"
echo ""
