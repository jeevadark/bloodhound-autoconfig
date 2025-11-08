# BloodHound-AutoConfig Usage Examples

## Table of Contents
- [Basic Scenarios](#basic-scenarios)
- [Advanced Use Cases](#advanced-use-cases)
- [Integration Examples](#integration-examples)
- [Troubleshooting Examples](#troubleshooting-examples)

---

## Basic Scenarios

### Scenario 1: Single Domain Network

**Context**: Small company with one AD domain

```bash
# 1. Scan the network
nmap -p 88,389,445 -sV -oN company_scan.txt 10.0.0.0/24

# 2. Run BloodHound-AutoConfig
python3 bloodhound-autoconfig.py company_scan.txt

# Expected output:
# [+] Domain Controllers found: 2
# [+] Detected Domains: COMPANY.LOCAL

# 3. Follow prompts:
# - Domain: COMPANY.LOCAL (auto-detected)
# - Username: admin
# - Password: P@ssw0rd123
```

### Scenario 2: Multi-Domain Forest

**Context**: Enterprise with parent and child domains

```bash
# 1. Comprehensive scan
nmap -p 88,389,636,445,3268 -sV -sC --script ldap-rootdse -oN enterprise_scan.txt 10.0.0.0/16

# 2. Run tool
python3 bloodhound-autoconfig.py enterprise_scan.txt

# Expected output:
# [+] Domain Controllers found: 8
# [+] Detected Domains: CORP.COM, SUBSIDIARY.CORP.COM, PARTNER.CORP.COM

# 3. Select target domain when prompted:
# [*] Multiple domains detected:
#     1. CORP.COM
#     2. SUBSIDIARY.CORP.COM
#     3. PARTNER.CORP.COM
# [+] Enter domain name to use: CORP.COM
```

### Scenario 3: Large Network (1000+ IPs)

**Context**: Red team engagement on large infrastructure

```bash
# 1. Initial discovery scan
nmap -p 88,389,445 -sV -iL targets.txt -oN massive_scan.txt --min-rate 1000

# 2. Parse results
python3 bloodhound-autoconfig.py massive_scan.txt --output ./results

# Progress indicators will show:
# [*] Processing 1247 hosts from Nmap scan...
# [*] Progress: 100/1247 hosts processed
# [*] Progress: 200/1247 hosts processed
# ...

# 3. Results saved automatically
# Files created:
# - results/domain_controllers_20241108_143022.json
# - results/bloodhound_commands_20241108_143022.sh
```

---

## Advanced Use Cases

### Use Case 1: Automated Pipeline

**Integrate with your automation workflow**

```bash
#!/bin/bash
# automated_recon.sh

# Step 1: Scan
echo "[*] Starting network scan..."
nmap -p 88,389,445 -sV -iL targets.txt -oN scan_$(date +%Y%m%d).txt

# Step 2: Extract DC info (JSON only, no prompts)
echo "[*] Extracting DC information..."
python3 bloodhound-autoconfig.py scan_$(date +%Y%m%d).txt --json-only --output ./results

# Step 3: Parse JSON and run BloodHound
echo "[*] Running BloodHound collection..."
DC_IP=$(jq -r '.domain_controllers[0].ip' results/domain_controllers_*.json)
DOMAIN=$(jq -r '.domains[0]' results/domain_controllers_*.json)

bloodhound-python \
  -u "$USERNAME" \
  -p "$PASSWORD" \
  -d "$DOMAIN" \
  -dc "$DC_IP" \
  -c All \
  --zip

echo "[*] Collection complete!"
```

### Use Case 2: Multiple Credentials Testing

**Test multiple accounts across all DCs**

```bash
#!/bin/bash
# test_multiple_creds.sh

# Extract DCs
python3 bloodhound-autoconfig.py scan.txt --json-only

# Read credentials from file
while IFS=: read -r username password; do
    echo "[*] Testing $username..."
    
    # Test against each DC
    for dc in $(jq -r '.domain_controllers[].ip' domain_controllers_*.json); do
        echo "  [*] Trying DC: $dc"
        bloodhound-python \
          -u "$username" \
          -p "$password" \
          -d "CORP.LOCAL" \
          -dc "$dc" \
          -c DCOnly \
          --zip 2>&1 | tee -a results.log
    done
done < credentials.txt
```

### Use Case 3: Cross-Forest Trust Discovery

**Discover and map trust relationships**

```bash
# 1. Scan all networks
nmap -p 88,389,445 -sV -iL all_networks.txt -oN complete_scan.txt

# 2. Extract all domains
python3 bloodhound-autoconfig.py complete_scan.txt --json-only

# 3. Analyze domains
jq '.domains[]' domain_controllers_*.json

# Output might show:
# "CORP.COM"
# "PARTNER.COM"
# "SUBSIDIARY.CORP.COM"

# 4. Run BloodHound for each domain
for domain in $(jq -r '.domains[]' domain_controllers_*.json | sort -u); do
    echo "[*] Collecting $domain..."
    # Find DC for this domain
    dc=$(jq -r ".domain_controllers[] | select(.domain==\"$domain\") | .ip" domain_controllers_*.json | head -1)
    
    bloodhound-python -u admin -p pass -d "$domain" -dc "$dc" -c All --zip
done
```

---

## Integration Examples

### Example 1: CrackMapExec Integration

**Verify credentials before running BloodHound**

```bash
#!/bin/bash
# Verify creds with CME, then run BloodHound

# Extract DC list
python3 bloodhound-autoconfig.py scan.txt --json-only
DC_LIST=$(jq -r '.domain_controllers[].ip' domain_controllers_*.json)

# Test with CrackMapExec
echo "[*] Verifying credentials..."
for dc in $DC_LIST; do
    crackmapexec smb $dc -u admin -p 'P@ssw0rd' -d CORP.LOCAL
    
    if [ $? -eq 0 ]; then
        echo "[+] Valid credentials for $dc"
        echo "[*] Running BloodHound..."
        bloodhound-python -u admin -p 'P@ssw0rd' -d CORP.LOCAL -dc $dc -c All --zip
        break
    fi
done
```

### Example 2: Docker Container Deployment

**Run in isolated environment**

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY bloodhound-autoconfig.py .

# Install BloodHound-python
RUN pip install bloodhound

ENTRYPOINT ["python3", "bloodhound-autoconfig.py"]
```

```bash
# Build
docker build -t bloodhound-autoconfig .

# Run
docker run -v $(pwd)/scans:/scans bloodhound-autoconfig /scans/nmap_output.txt
```

### Example 3: Ansible Playbook

**Automate across multiple environments**

```yaml
# bloodhound_collect.yml
---
- name: BloodHound Collection Automation
  hosts: localhost
  tasks:
    - name: Run Nmap scan
      command: nmap -p 88,389,445 -sV {{ target_network }} -oN scan.txt
      
    - name: Extract DC info
      command: python3 bloodhound-autoconfig.py scan.txt --json-only --output results/
      
    - name: Parse JSON
      shell: cat results/domain_controllers_*.json
      register: dc_info
      
    - name: Run BloodHound
      command: >
        bloodhound-python
        -u {{ username }}
        -p {{ password }}
        -d {{ item.domain }}
        -dc {{ item.ip }}
        -c All
        --zip
      loop: "{{ (dc_info.stdout | from_json).domain_controllers }}"
```

---

## Troubleshooting Examples

### Problem 1: No DCs Found

**Scenario**: Tool reports 0 Domain Controllers

```bash
# Debug: Check what Nmap detected
grep -E "(88/tcp|389/tcp|kerberos|ldap)" scan.txt

# If nothing found, rescan with more aggressive options
nmap -p- -A -T4 --script ldap-rootdse,smb-os-discovery 10.0.0.1 -oN detailed_scan.txt

# Rerun tool with verbose mode
python3 bloodhound-autoconfig.py detailed_scan.txt --verbose
```

### Problem 2: Wrong Domain Detected

**Scenario**: Tool extracts incorrect domain name

```bash
# Extract raw DC info
python3 bloodhound-autoconfig.py scan.txt --json-only

# Check detected domains
jq '.domains' domain_controllers_*.json

# Manually verify with ldapsearch
ldapsearch -x -h 10.0.0.1 -b "" -s base "(objectclass=*)" defaultNamingContext

# If domain is wrong, manually edit JSON and generate commands
jq '.domains = ["CORRECT.DOMAIN"]' domain_controllers_*.json > fixed.json
```

### Problem 3: Authentication Failures

**Scenario**: BloodHound commands fail with auth errors

```bash
# Test credentials manually first
rpcclient -U "DOMAIN\username" 10.0.0.1 -c "getusername"

# Try different username formats
# Format 1: domain\user
bloodhound-python -u 'CORP\admin' -p 'pass' -d CORP.LOCAL -dc 10.0.0.1 -c DCOnly

# Format 2: user@domain
bloodhound-python -u 'admin@corp.local' -p 'pass' -d CORP.LOCAL -dc 10.0.0.1 -c DCOnly

# Format 3: just username
bloodhound-python -u 'admin' -p 'pass' -d CORP.LOCAL -dc 10.0.0.1 -c DCOnly
```

---

## Quick Reference

### Common Nmap Commands

```bash
# Quick AD port scan
nmap -p 88,389,445 -sV -oN scan.txt targets.txt

# Comprehensive AD scan
nmap -p 88,389,636,445,3268,3269,53,135 -sV -sC -oN full_scan.txt targets.txt

# Aggressive with scripts
nmap -p 88,389,445 -A --script ldap-rootdse,smb-os-discovery -oN aggressive.txt targets.txt

# Large network scan
nmap -p 88,389,445 -sV -iL large_targets.txt -oN massive.txt --min-rate 1000 -T4
```

### Common BloodHound-AutoConfig Commands

```bash
# Interactive mode
python3 bloodhound-autoconfig.py scan.txt

# JSON export only
python3 bloodhound-autoconfig.py scan.txt --json-only

# Custom output directory
python3 bloodhound-autoconfig.py scan.txt --output ./results

# Verbose debugging
python3 bloodhound-autoconfig.py scan.txt --verbose

# Full workflow
python3 bloodhound-autoconfig.py scan.txt -o results -j && \
jq '.' results/domain_controllers_*.json
```

---

## Tips and Best Practices

1. **Always scan port 88 (Kerberos)** - This is the most reliable DC indicator
2. **Use service detection (-sV)** - Required for accurate DC identification
3. **Save Nmap output as text (-oN)** - XML support coming soon
4. **Test credentials first** - Use CrackMapExec or rpcclient before BloodHound
5. **Start with DCOnly collection** - Faster, less noisy for initial recon
6. **Use JSON export for automation** - Easier to parse in scripts
7. **Keep scan results** - Useful for documentation and reporting

---

For more examples and updates, visit: https://github.com/yourusername/bloodhound-autoconfig
