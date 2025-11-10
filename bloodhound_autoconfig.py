#!/usr/bin/env python3
"""
BloodHound-AutoConfig v1.0
Automated Domain Controller Discovery and BloodHound Command Generator

Author: Jeeva S ()
GitHub: https://github.com/jeevadark/bloodhound-autoconfig
License: MIT

Description:
    Parses large-scale Nmap scan results (1000+ IPs) and automatically:
    - Identifies Domain Controllers
    - Extracts AD domain information
    - Generates ready-to-use BloodHound-python commands
    - Supports multiple DCs and domains
    
Usage:
    python3 bloodhound-autoconfig.py <nmap_output_file>
    python3 bloodhound-autoconfig.py -h
"""

import re
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Optional, Tuple

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class DomainController:
    """Represents a discovered Domain Controller"""
    def __init__(self, ip: str, hostname: str, domain: Optional[str] = None, 
                 netbios: Optional[str] = None):
        self.ip = ip
        self.hostname = hostname
        self.domain = domain
        self.netbios = netbios
        self.ports = []
        self.services = []
    
    def __repr__(self):
        return f"DC({self.ip}, {self.hostname}, {self.domain})"
    
    def to_dict(self):
        return {
            'ip': self.ip,
            'hostname': self.hostname,
            'domain': self.domain,
            'netbios': self.netbios,
            'ports': self.ports,
            'services': self.services
        }

class NmapParser:
    """Parses Nmap output and extracts Active Directory information"""
    
    # AD-related ports to look for
    AD_PORTS = {
        88: 'Kerberos',
        389: 'LDAP',
        636: 'LDAPS',
        445: 'SMB',
        3268: 'Global Catalog',
        3269: 'Global Catalog SSL',
        53: 'DNS',
        135: 'RPC'
    }
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.domain_controllers: List[DomainController] = []
        self.domain_names: Set[str] = set()
        self.netbios_domains: Set[str] = set()
        self.total_hosts: int = 0
        self.parse_errors: List[str] = []
    
    def parse(self) -> bool:
        """Parse the Nmap output file"""
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"{Colors.FAIL}[!] Error reading file: {e}{Colors.ENDC}")
            return False
        
        # Split by Nmap scan report to process each host
        hosts = re.split(r'Nmap scan report for ', content)
        self.total_hosts = len(hosts) - 1  # Exclude first empty split
        
        print(f"{Colors.OKBLUE}[*] Processing {self.total_hosts} hosts from Nmap scan...{Colors.ENDC}")
        
        for idx, host_block in enumerate(hosts[1:], 1):
            if idx % 100 == 0:
                print(f"{Colors.OKCYAN}[*] Progress: {idx}/{self.total_hosts} hosts processed{Colors.ENDC}")
            
            try:
                dc = self._parse_host(host_block)
                if dc:
                    self.domain_controllers.append(dc)
            except Exception as e:
                self.parse_errors.append(f"Host {idx}: {str(e)}")
        
        return True
    
    def _parse_host(self, host_block: str) -> Optional[DomainController]:
        """Parse a single host block"""
        lines = host_block.split('\n')
        first_line = lines[0]
        
        # Extract IP and hostname
        ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', first_line)
        hostname_match = re.search(r'^([^\(]+)', first_line)
        
        ip = ip_match.group(1) if ip_match else None
        hostname = hostname_match.group(1).strip() if hostname_match else ip
        
        if not ip:
            return None
        
        # Check if this is a Domain Controller
        is_dc, ports, services = self._check_domain_controller(host_block)
        
        if not is_dc:
            return None
        
        # Extract domain information
        domain = self._extract_domain(host_block)
        netbios = self._extract_netbios(host_block)
        
        # Create DC object
        dc = DomainController(ip, hostname, domain, netbios)
        dc.ports = ports
        dc.services = services
        
        # Add to global sets
        if domain:
            self.domain_names.add(domain)
        if netbios:
            self.netbios_domains.add(netbios)
        
        return dc
    
    def _check_domain_controller(self, block: str) -> Tuple[bool, List[int], List[str]]:
        """Check if host is a Domain Controller"""
        block_lower = block.lower()
        found_ports = []
        found_services = []
        
        # Look for AD-related ports
        for port, service in self.AD_PORTS.items():
            port_pattern = f'{port}/tcp'
            if port_pattern in block_lower:
                found_ports.append(port)
                found_services.append(service)
        
        # A DC typically has Kerberos (88) AND LDAP (389)
        has_kerberos = 88 in found_ports
        has_ldap = 389 in found_ports or 636 in found_ports
        
        is_dc = has_kerberos and has_ldap
        
        return is_dc, found_ports, found_services
    
    def _extract_domain(self, block: str) -> Optional[str]:
        """Extract DNS domain name"""
        # Method 1: Look for explicit Domain field
        domain_match = re.search(r'Domain:\s*([a-zA-Z0-9\-\.]+)', block, re.IGNORECASE)
        if domain_match:
            return domain_match.group(1).strip()
        
        # Method 2: Extract from LDAP defaultNamingContext
        naming_context = re.search(r'defaultNamingContext[:\s]+([^\n,]+)', block, re.IGNORECASE)
        if naming_context:
            dn = naming_context.group(1).strip()
            dc_parts = re.findall(r'DC=([^,]+)', dn, re.IGNORECASE)
            if dc_parts:
                return '.'.join(dc_parts)
        
        # Method 3: Extract from DNS hostname
        dns_hostname = re.search(r'dns_computer_name:\s*([^\n]+)', block, re.IGNORECASE)
        if dns_hostname:
            fqdn = dns_hostname.group(1).strip()
            if '.' in fqdn:
                return '.'.join(fqdn.split('.')[1:])
        
        # Method 4: Extract from forest name
        forest_match = re.search(r'forest[:\s]+([a-zA-Z0-9\-\.]+)', block, re.IGNORECASE)
        if forest_match:
            return forest_match.group(1).strip()
        
        return None
    
    def _extract_netbios(self, block: str) -> Optional[str]:
        """Extract NetBIOS domain name"""
        # Look for NetBIOS domain
        netbios_match = re.search(r'NetBIOS.*Domain:\s*([a-zA-Z0-9\-]+)', block, re.IGNORECASE)
        if netbios_match:
            return netbios_match.group(1).strip().upper()
        
        # Alternative: NetBIOS computer name
        netbios_computer = re.search(r'NetBIOS.*Computer.*:\s*([a-zA-Z0-9\-]+)', block, re.IGNORECASE)
        if netbios_computer:
            return netbios_computer.group(1).strip().upper()
        
        return None

class BloodHoundCommandGenerator:
    """Generates BloodHound-python commands"""
    
    def __init__(self, parser: NmapParser):
        self.parser = parser
    
    def generate_command(self, dc: DomainController, username: str, password: str, 
                        domain: str, use_domain_prefix: bool = False, 
                        netbios_domain: Optional[str] = None) -> str:
        """Generate a single BloodHound command"""
        
        # Determine DC hostname (prefer FQDN over IP)
        dc_hostname = dc.hostname if dc.hostname != dc.ip else dc.ip
        
        # Format username
        if use_domain_prefix and netbios_domain:
            username_str = f"'{netbios_domain}\\{username}'"
        else:
            username_str = username
        
        command = f"""bloodhound-python \\
  -u {username_str} \\
  -p '{password}' \\
  -d {domain} \\
  -dc {dc_hostname} \\
  -c All \\
  --zip"""
        
        return command
    
    def generate_all_commands(self, username: str, password: str, 
                            use_domain_prefix: bool = False) -> List[Dict]:
        """Generate commands for all DCs"""
        commands = []
        
        # Group DCs by domain
        dc_by_domain = {}
        for dc in self.parser.domain_controllers:
            domain = dc.domain or "UNKNOWN"
            if domain not in dc_by_domain:
                dc_by_domain[domain] = []
            dc_by_domain[domain].append(dc)
        
        # Generate commands for each domain
        for domain, dcs in dc_by_domain.items():
            # Try to find matching NetBIOS domain
            netbios = None
            for dc in dcs:
                if dc.netbios:
                    netbios = dc.netbios
                    break
            
            if not netbios and self.parser.netbios_domains:
                netbios = list(self.parser.netbios_domains)[0]
            
            for dc in dcs:
                cmd = self.generate_command(dc, username, password, domain, 
                                          use_domain_prefix, netbios)
                commands.append({
                    'dc': dc.to_dict(),
                    'command': cmd,
                    'domain': domain,
                    'netbios': netbios
                })
        
        return commands

def print_banner():
    """Print tool banner"""
    banner = f"""
{Colors.OKCYAN}╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║              BloodHound-AutoConfig v1.0                          ║
║         Automated DC Discovery & Command Generator               ║
║                                                                 ║
║  For large-scale Active Directory penetration testing           ║
║  Processes 1000+ IPs and extracts exact DC information          ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝{Colors.ENDC}
"""
    print(banner)

def print_summary(parser: NmapParser):
    """Print parsing summary"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}Summary:{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}[+] Total hosts scanned: {parser.total_hosts}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}[+] Domain Controllers found: {len(parser.domain_controllers)}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}[+] Unique domains detected: {len(parser.domain_names)}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}[+] NetBIOS domains detected: {len(parser.netbios_domains)}{Colors.ENDC}")
    
    if parser.parse_errors:
        print(f"{Colors.WARNING}[!] Parse errors: {len(parser.parse_errors)}{Colors.ENDC}")

def print_domain_controllers(parser: NmapParser):
    """Print detailed DC information"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}Domain Controllers Details:{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*70}{Colors.ENDC}")
    
    for idx, dc in enumerate(parser.domain_controllers, 1):
        print(f"\n{Colors.OKCYAN}[DC {idx}]{Colors.ENDC}")
        print(f"  IP Address:    {dc.ip}")
        print(f"  Hostname:      {dc.hostname}")
        print(f"  Domain:        {dc.domain or 'Unknown'}")
        print(f"  NetBIOS:       {dc.netbios or 'Unknown'}")
        print(f"  Services:      {', '.join(dc.services) if dc.services else 'N/A'}")
        print(f"  Ports:         {', '.join(map(str, dc.ports)) if dc.ports else 'N/A'}")

def get_user_input(parser: NmapParser) -> Dict:
    """Get user input for command generation"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}Configuration:{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*70}{Colors.ENDC}")
    
    config = {}
    
    # Domain selection
    if len(parser.domain_names) > 1:
        print(f"{Colors.WARNING}[*] Multiple domains detected:{Colors.ENDC}")
        for idx, domain in enumerate(sorted(parser.domain_names), 1):
            print(f"    {idx}. {domain}")
        domain_choice = input(f"{Colors.OKBLUE}[+] Enter domain name to use: {Colors.ENDC}").strip()
        config['domain'] = domain_choice if domain_choice else list(parser.domain_names)[0]
    elif parser.domain_names:
        config['domain'] = list(parser.domain_names)[0]
        print(f"{Colors.OKGREEN}[*] Using domain: {config['domain']}{Colors.ENDC}")
    else:
        config['domain'] = input(f"{Colors.FAIL}[!] No domain detected. Enter manually: {Colors.ENDC}").strip()
    
    # NetBIOS domain selection
    if len(parser.netbios_domains) > 1:
        print(f"{Colors.WARNING}[*] Multiple NetBIOS domains detected:{Colors.ENDC}")
        for idx, netbios in enumerate(sorted(parser.netbios_domains), 1):
            print(f"    {idx}. {netbios}")
        netbios_choice = input(f"{Colors.OKBLUE}[+] Enter NetBIOS domain (leave empty to skip): {Colors.ENDC}").strip().upper()
        config['netbios'] = netbios_choice if netbios_choice else list(parser.netbios_domains)[0]
    elif parser.netbios_domains:
        config['netbios'] = list(parser.netbios_domains)[0]
    else:
        netbios_input = input(f"{Colors.OKBLUE}[+] Enter NetBIOS domain (optional, press Enter to skip): {Colors.ENDC}").strip().upper()
        config['netbios'] = netbios_input if netbios_input else None
    
    # Username format
    print(f"\n{Colors.WARNING}[*] Username format options:{Colors.ENDC}")
    print(f"    1. Without domain prefix (recommended): micro")
    print(f"    2. With domain prefix: DOMAIN\\micro")
    use_prefix = input(f"{Colors.OKBLUE}[+] Use domain prefix? (y/n) [n]: {Colors.ENDC}").lower().strip() == 'y'
    config['use_domain_prefix'] = use_prefix
    
    # Credentials
    config['username'] = input(f"{Colors.OKBLUE}[+] Enter username (without domain): {Colors.ENDC}").strip()
    config['password'] = input(f"{Colors.OKBLUE}[+] Enter password: {Colors.ENDC}").strip()
    
    return config

def save_results(parser: NmapParser, commands: List[Dict], output_dir: str = "."):
    """Save results to files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save DC information as JSON
    dc_file = f"{output_dir}/domain_controllers_{timestamp}.json"
    dc_data = {
        'timestamp': timestamp,
        'total_hosts': parser.total_hosts,
        'total_dcs': len(parser.domain_controllers),
        'domains': list(parser.domain_names),
        'netbios_domains': list(parser.netbios_domains),
        'domain_controllers': [dc.to_dict() for dc in parser.domain_controllers]
    }
    
    with open(dc_file, 'w') as f:
        json.dump(dc_data, f, indent=2)
    
    print(f"{Colors.OKGREEN}[+] DC information saved to: {dc_file}{Colors.ENDC}")
    
    # Save commands as shell script
    cmd_file = f"{output_dir}/bloodhound_commands_{timestamp}.sh"
    with open(cmd_file, 'w') as f:
        f.write("#!/bin/bash\n")
        f.write(f"# BloodHound Commands - Generated {timestamp}\n")
        f.write(f"# Total DCs: {len(commands)}\n\n")
        
        for idx, cmd_data in enumerate(commands, 1):
            f.write(f"# DC {idx}: {cmd_data['dc']['ip']} - {cmd_data['dc']['hostname']}\n")
            f.write(f"# Domain: {cmd_data['domain']}\n")
            f.write(cmd_data['command'])
            f.write("\n\n")
    
    print(f"{Colors.OKGREEN}[+] Commands saved to: {cmd_file}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}[*] Make executable: chmod +x {cmd_file}{Colors.ENDC}")

def main():
    parser_args = argparse.ArgumentParser(
        description='BloodHound-AutoConfig: Automated DC Discovery and Command Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 bloodhound-autoconfig.py nmap_scan.txt
  python3 bloodhound-autoconfig.py large_scan.xml --output ./results
  python3 bloodhound-autoconfig.py scan.txt --json-only
        """
    )
    
    parser_args.add_argument('nmap_file', help='Nmap output file to parse')
    parser_args.add_argument('-o', '--output', default='.', help='Output directory for results')
    parser_args.add_argument('-j', '--json-only', action='store_true', 
                           help='Only save JSON, skip interactive command generation')
    parser_args.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser_args.parse_args()
    
    # Print banner
    print_banner()
    
    # Check if file exists
    if not Path(args.nmap_file).exists():
        print(f"{Colors.FAIL}[!] File not found: {args.nmap_file}{Colors.ENDC}")
        sys.exit(1)
    
    # Parse Nmap output
    print(f"{Colors.OKBLUE}[*] Parsing Nmap output: {args.nmap_file}{Colors.ENDC}")
    parser = NmapParser(args.nmap_file)
    
    if not parser.parse():
        print(f"{Colors.FAIL}[!] Failed to parse Nmap output{Colors.ENDC}")
        sys.exit(1)
    
    # Print summary
    print_summary(parser)
    
    # Check if DCs were found
    if not parser.domain_controllers:
        print(f"{Colors.FAIL}[!] No Domain Controllers found in scan{Colors.ENDC}")
        print(f"{Colors.WARNING}[*] Make sure your Nmap scan included AD ports: 88, 389, 636, 445{Colors.ENDC}")
        sys.exit(1)
    
    # Print DC details
    print_domain_controllers(parser)
    
    # JSON-only mode
    if args.json_only:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dc_file = f"{args.output}/domain_controllers_{timestamp}.json"
        dc_data = {
            'timestamp': timestamp,
            'total_hosts': parser.total_hosts,
            'total_dcs': len(parser.domain_controllers),
            'domains': list(parser.domain_names),
            'netbios_domains': list(parser.netbios_domains),
            'domain_controllers': [dc.to_dict() for dc in parser.domain_controllers]
        }
        
        with open(dc_file, 'w') as f:
            json.dump(dc_data, f, indent=2)
        
        print(f"{Colors.OKGREEN}[+] DC information saved to: {dc_file}{Colors.ENDC}")
        sys.exit(0)
    
    # Get user configuration
    config = get_user_input(parser)
    
    # Generate commands
    generator = BloodHoundCommandGenerator(parser)
    commands = generator.generate_all_commands(
        config['username'],
        config['password'],
        config['use_domain_prefix']
    )
    
    # Display commands
    print(f"\n{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}Generated BloodHound Commands:{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*70}{Colors.ENDC}")
    
    for idx, cmd_data in enumerate(commands, 1):
        dc = cmd_data['dc']
        print(f"\n{Colors.OKCYAN}[Command {idx}] DC: {dc['ip']} ({dc['hostname']}){Colors.ENDC}")
        print(f"{Colors.OKGREEN}{cmd_data['command']}{Colors.ENDC}")
    
    # Save results
    save_choice = input(f"\n{Colors.OKBLUE}[?] Save results to files? (y/n): {Colors.ENDC}").lower().strip()
    if save_choice == 'y':
        save_results(parser, commands, args.output)
    
    print(f"\n{Colors.OKGREEN}[✓] Done! Happy hunting! 🎯{Colors.ENDC}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}[!] Interrupted by user{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.FAIL}[!] Error: {e}{Colors.ENDC}")
        if '--verbose' in sys.argv or '-v' in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)
