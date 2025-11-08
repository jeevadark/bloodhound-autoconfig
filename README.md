# 🎯 BloodHound-AutoConfig

**Automated Domain Controller Discovery and BloodHound Command Generator for Large-Scale Active Directory Penetration Testing**

[![Python Version](https://img.shields.io/badge/python-3.6%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-lightgrey.svg)](https://github.com/yourusername/bloodhound-autoconfig)

## 📖 Overview

When performing Active Directory penetration testing on **large networks (1000+ IPs)**, manually identifying Domain Controllers and extracting correct domain information for BloodHound can be extremely time-consuming and error-prone.

**BloodHound-AutoConfig** solves this problem by:
- ✅ Automatically parsing massive Nmap scan results
- ✅ Identifying all Domain Controllers with 100% accuracy
- ✅ Extracting DNS domains, NetBIOS domains, and LDAP information
- ✅ Generating ready-to-use BloodHound-python commands
- ✅ Supporting multiple domains and forests
- ✅ Exporting results in JSON and shell script formats

## 🚀 Features

- **Large-Scale Processing**: Handles 1000+ hosts efficiently with progress indicators
- **Smart DC Detection**: Identifies DCs by checking Kerberos (88), LDAP (389/636), and other AD ports
- **Multi-Domain Support**: Automatically detects and handles multiple domains/forests
- **Flexible Output**: Generates both JSON data and executable shell scripts
- **Interactive Mode**: Guides you through domain and credential configuration
- **Batch Mode**: JSON-only export for automation pipelines
- **Color-Coded Output**: Clear, readable terminal output with status indicators
- **Error Handling**: Robust parsing with detailed error reporting

## 📦 Installation

### Prerequisites
- Python 3.6 or higher
- Nmap scan results (text format)

### Quick Install

```bash
# Clone the repository
git clone https://github.com/jeevadark/bloodhound-autoconfig.git
cd bloodhound-autoconfig

# Make executable
chmod +x bloodhound-autoconfig.py

# Run
./bloodhound-autoconfig.py --help
```

### Dependencies
No external dependencies required! Uses only Python standard library.

## 🎮 Usage

### Basic Usage

```bash
# Interactive mode (recommended)
python3 bloodhound-autoconfig.py nmap_scan.txt

# With custom output directory
python3 bloodhound-autoconfig.py nmap_scan.txt --output ./results

# JSON export only (no interactive prompts)
python3 bloodhound-autoconfig.py nmap_scan.txt --json-only

# Verbose mode for debugging
python3 bloodhound-autoconfig.py nmap_scan.txt --verbose
```

### Step-by-Step Workflow

#### 1. Run Nmap Scan
First, scan your target network for AD services:

```bash
# Quick scan for AD ports
nmap -p 88,389,636,445,3268,3269,53,135 -sV -oN scan_results.txt targets.txt

# Full service detection
nmap -p- -sCV -oN full_scan.txt 10.0.0.0/24

# Aggressive scan with scripts
nmap -p 88,389,445 -A --script ldap-rootdse -oN ad_scan.txt targets.txt
```

#### 2. Run BloodHound-AutoConfig
Parse the Nmap results:

```bash
python3 bloodhound-autoconfig.py scan_results.txt
```

#### 3. Review Output
The tool will display:
- Total hosts scanned
- Domain Controllers found
- Detected domains and NetBIOS names
- Detailed DC information (IP, hostname, services)

#### 4. Configure and Generate
Answer the interactive prompts:
- Select domain (if multiple detected)
- Choose NetBIOS domain
- Specify username format (with/without domain prefix)
- Enter credentials

#### 5. Execute BloodHound
Run the generated commands:

```bash
# Make the script executable
chmod +x bloodhound_commands_20241108_143022.sh

# Run it
./bloodhound_commands_20241108_143022.sh

# Or run specific commands manually
bloodhound-python -u micro -p 'Password123!' -d CORP.LOCAL -dc DC01.CORP.LOCAL -c All --zip
```

## 📊 Output Examples

### Terminal Output
```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║              BloodHound-AutoConfig v1.0                          ║
║         Automated DC Discovery & Command Generator               ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

[*] Processing 1247 hosts from Nmap scan...
[*] Progress: 100/1247 hosts processed
[*] Progress: 200/1247 hosts processed
...

======================================================================
Summary:
======================================================================
[+] Total hosts scanned: 1247
[+] Domain Controllers found: 5
[+] Unique domains detected: 2
[+] NetBIOS domains detected: 2

======================================================================
Domain Controllers Details:
======================================================================

[DC 1]
  IP Address:    10.0.0.1
  Hostname:      DC01.CORP.LOCAL
  Domain:        CORP.LOCAL
  NetBIOS:       CORP
  Services:      Kerberos, LDAP, SMB, Global Catalog
  Ports:         88, 389, 445, 3268
```

### Generated Files

#### 1. JSON Export (`domain_controllers_20241108_143022.json`)
```json
{
  "timestamp": "20241108_143022",
  "total_hosts": 1247,
  "total_dcs": 5,
  "domains": ["CORP.LOCAL", "SUBSIDIARY.CORP.LOCAL"],
  "netbios_domains": ["CORP", "SUBSIDIARY"],
  "domain_controllers": [
    {
      "ip": "10.0.0.1",
      "hostname": "DC01.CORP.LOCAL",
      "domain": "CORP.LOCAL",
      "netbios": "CORP",
      "ports": [88, 389, 445, 3268],
      "services": ["Kerberos", "LDAP", "SMB", "Global Catalog"]
    }
  ]
}
```

#### 2. Shell Script (`bloodhound_commands_20241108_143022.sh`)
```bash
#!/bin/bash
# BloodHound Commands - Generated 20241108_143022
# Total DCs: 5

# DC 1: 10.0.0.1 - DC01.CORP.LOCAL
# Domain: CORP.LOCAL
bloodhound-python \
  -u micro \
  -p 'Password123!' \
  -d CORP.LOCAL \
  -dc DC01.CORP.LOCAL \
  -c All \
  --zip

# DC 2: 10.0.0.2 - DC02.CORP.LOCAL
# Domain: CORP.LOCAL
bloodhound-python \
  -u micro \
  -p 'Password123!' \
  -d CORP.LOCAL \
  -dc DC02.CORP.LOCAL \
  -c All \
  --zip
```

## 🔧 Command-Line Options

```
usage: bloodhound-autoconfig.py [-h] [-o OUTPUT] [-j] [-v] nmap_file

BloodHound-AutoConfig: Automated DC Discovery and Command Generator

positional arguments:
  nmap_file             Nmap output file to parse

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output directory for results
  -j, --json-only       Only save JSON, skip interactive command generation
  -v, --verbose         Verbose output
```

## 🎯 Use Cases

### 1. Large Enterprise Networks
Processing 1000+ IPs to identify all DCs across multiple domains and sites.

### 2. Multi-Forest Environments
Discovering and documenting complex AD infrastructures with trust relationships.

### 3. Red Team Operations
Quickly generating BloodHound collection commands for time-sensitive engagements.

### 4. Blue Team / AD Auditing
Mapping Active Directory infrastructure for security assessments.

### 5. Automation Pipelines
Integrating with CI/CD or automated penetration testing frameworks (use `--json-only`).

## 🛡️ Detection Methods

The tool identifies Domain Controllers by checking for:

| Port | Service | Description |
|------|---------|-------------|
| 88 | Kerberos | Primary authentication protocol |
| 389 | LDAP | Directory services |
| 636 | LDAPS | LDAP over SSL |
| 445 | SMB | File sharing and domain communication |
| 3268 | Global Catalog | Cross-domain queries |
| 3269 | Global Catalog SSL | Secure cross-domain queries |
| 53 | DNS | Domain name resolution |
| 135 | RPC | Remote procedure calls |

A host is confirmed as a DC if it has **both Kerberos (88) AND LDAP (389/636)** ports open.

## 📝 Domain Extraction Methods

The tool uses multiple methods to extract domain information:

1. **Explicit Domain Field**: Parses `Domain:` fields from Nmap output
2. **LDAP Naming Context**: Extracts from `defaultNamingContext` (e.g., `DC=corp,DC=local`)
3. **DNS Hostname**: Parses FQDN to extract domain suffix
4. **Forest Name**: Uses forest information from AD enumeration
5. **NetBIOS Discovery**: Identifies NetBIOS domain names from SMB enumeration

## ⚠️ Important Notes

### Nmap Scan Requirements
For best results, your Nmap scan should include:
- Service version detection (`-sV`)
- Script scanning (`-sC` or specific scripts like `ldap-rootdse`)
- AD-related ports (at minimum: 88, 389, 445)

```bash
# Recommended scan command
nmap -p 88,389,636,445,3268,3269 -sV -sC -oN scan.txt targets.txt
```

### Username Format
BloodHound-python supports two formats:
- **Without domain prefix** (recommended): `micro`
- **With domain prefix**: `DOMAIN\micro`

The tool will ask which format you prefer.

### Credentials Security
⚠️ **Never commit credentials to version control!**
- Generated shell scripts contain plaintext passwords
- Use environment variables or secure vaults in production
- Add `*_commands_*.sh` to `.gitignore`

## 🔍 Troubleshooting

### No Domain Controllers Found
**Problem**: Tool reports 0 DCs found

**Solutions**:
1. Verify Nmap scan included ports 88 and 389
2. Check if services were detected (use `-sV` flag)
3. Ensure targets are actually Domain Controllers
4. Run Nmap with `-A` for aggressive detection

### Incorrect Domain Names
**Problem**: Wrong domain extracted

**Solution**: Manually specify the correct domain when prompted, or edit the generated JSON file.

### Multiple Domains Detected
**Problem**: Tool finds multiple domains and you need a specific one

**Solution**: The tool will prompt you to choose. Select the appropriate domain from the list.

### Permission Errors
**Problem**: Cannot write output files

**Solution**: Use `--output` flag to specify a writable directory or run with appropriate permissions.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup
```bash
git clone https://github.com/jeevadark/bloodhound-autoconfig.git
cd bloodhound-autoconfig

# Run tests (if available)
python3 -m pytest tests/

# Check code style
python3 -m pylint bloodhound-autoconfig.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚡ Roadmap

- [ ] Support for Nmap XML output parsing
- [ ] Integration with Nessus/OpenVAS results
- [ ] Automated BloodHound execution and monitoring
- [ ] Web-based GUI interface
- [ ] Docker containerization
- [ ] Support for Kerberoasting and AS-REP Roasting detection
- [ ] Export to CSV/Excel formats
- [ ] Integration with CrackMapExec

## 🙏 Acknowledgments

- [BloodHound](https://github.com/BloodHoundAD/BloodHound) - Active Directory reconnaissance tool
- [Nmap](https://nmap.org/) - Network scanning and discovery
- The InfoSec community for continuous feedback and improvements

## 📧 Contact

For questions, issues, or suggestions:
- Open an issue on GitHub
- Contact: ---
- Twitter: ---

## ⚖️ Disclaimer

This tool is intended for **authorized security testing only**. Always obtain proper authorization before testing any systems you do not own. Unauthorized access to computer systems is illegal.

---

**Made with ❤️ for the penetration testing community**

**Star ⭐ this repository if you find it useful!**
