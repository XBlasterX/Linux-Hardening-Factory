# Linux Hardening Factory

**RHEL security hardening, configuration management, compliance assessment, and SSH recovery — automated with Ansible.**

[![Linux Hardening CI](https://github.com/XBlasterX/Linux-Hardening-Factory/actions/workflows/validate.yml/badge.svg)](https://github.com/XBlasterX/Linux-Hardening-Factory/actions/workflows/validate.yml)

Linux Hardening Factory is a hands-on infrastructure security project built on **Red Hat Enterprise Linux, Ansible, OpenSCAP, SELinux, firewalld, auditd, AIDE, Bash, and GitHub Actions**. It applies repeatable security controls to three lab web servers, collects CIS Server Level 1 assessment evidence, and explores recovery from SSH configuration failures.

**Workflow:** assess → harden → validate → recover when needed → reassess.

> This is an educational lab, **not** a fully CIS-compliant or production-ready hardening solution.

## Architecture

```text
                      macOS / Ansible controller
                             SSH + privilege escalation
                                       |
                              Private VM network
                             /         |         \
                          web01       web02       web03
                          RHEL        RHEL        RHEL
                            \           |          /
                            Ansible security roles
                                       |
                          OpenSCAP CIS Level 1 scans
                                       |
                         XML / HTML reports (per host)
                                       |
                       Python parser -> Markdown summary

                GitHub Actions: independent static validation
```

- **Controller:** macOS workstation running Ansible.
- **Managed nodes:** three RHEL VMs in the `webservers` inventory group.
- **Deployment:** `site.yml` composes dedicated Ansible roles.
- **Assessment:** `scan.yml` invokes OpenSCAP and collects XML/HTML reports.
- **CI:** GitHub Actions checks syntax and lint rules on push / pull request; it does **not** apply changes to the RHEL VMs.

## Security Controls

| Component | Implemented behavior |
| --- | --- |
| **SSH** | Disables root login, password and keyboard-interactive authentication, empty passwords and X11 forwarding; limits authentication attempts; validates `sshd` configuration before replacement. |
| **SSH recovery** | Keeps a configuration backup, installs a Bash rollback script, and schedules a temporary systemd rollback before a planned SSH configuration change. |
| **Sudo** | Requires a pseudo-terminal, writes a sudo log, configures a five-minute authentication timestamp, and validates sudoers changes with `visudo`. |
| **Login banners** | Configures local and remote login notices. |
| **Kernel / networking** | Disables IPv4 forwarding, ICMP redirects and source routing; enables TCP SYN cookies; restricts `dmesg` access and process tracing. |
| **firewalld** | Enables the firewall, permits SSH and HTTP in the public zone, and removes the Cockpit service rule from that zone. |
| **SELinux** | Enforces the targeted policy and labels Apache content at `/srv/prodapp/public` as `httpd_sys_content_t`. |
| **AIDE** | Installs AIDE, initializes its file-integrity database, adds rules for available audit tools, and schedules a daily integrity check. |
| **auditd** | Installs and enables auditd, deploys rules monitoring identity, sudo and SSH configuration changes, and reloads the audit rules. |
| **OpenSCAP** | Runs a RHEL 10 CIS Server Level 1 assessment; saves per-host XML/HTML reports for comparison. |

The roles are organized under [`roles/`](roles/) to keep individual controls independently understandable and maintainable.

## Measured Results

The checked-in reports document the following change for **web02 and web03**; the final `after` report contains matching values for all three hosts. The original `before` summary has a malformed web01 heading, so the comparison uses hosts with complete baseline entries.

| Metric | Before | After | Change |
| --- | ---: | ---: | ---: |
| OpenSCAP score | 70.867912 | **75.647675** | **+4.779763** |
| Passed checks | 170 | **189** | **+19** |
| Failed checks | 124 | **105** | **−19** |
| Not applicable | 30 | 30 | — |
| Pass rate (PASS / [PASS + FAIL]) | 57.8% | **64.3%** | **+6.5 pp** |

An intermediate [checkpoint](reports/checkpoint3/summary.md) recorded an OpenSCAP score of 75.183395 and a pass rate of 63.6%; the latest adjustments improved the result further.

**Evidence:** [before](reports/before/summary.md) · [checkpoint 3](reports/checkpoint3/summary.md) · [after](reports/after/summary.md).

The **OpenSCAP score** and **pass rate** are different metrics. Neither is a percentage of project completion, and **64.3% does not mean full CIS compliance**. Remaining failures include areas such as crypto policies, separate filesystem partitions, and PAM/password controls. Results depend on the exact RHEL image, SCAP content, and starting configuration.

## SSH Failure and Recovery Lab

Remote SSH hardening is risky because an incorrect configuration can lock out the administrator. This repository contains both a tested **manual recovery experiment** and an Ansible workflow intended to protect SSH updates.

1. A root-owned backup of `/etc/ssh/sshd_config.d/00-hardening.conf` is stored under `/var/lib/ssh-hardening/`.
2. [`ssh-rollback.sh`](roles/ssh_hardening/files/ssh-rollback.sh) restores the backup, checks the configuration with `sshd -t`, and reloads `sshd`.
3. The Ansible role previews changes and, when necessary, schedules a one-shot rollback using `systemd-run --on-active=180s` **before** deploying the updated SSH template.
4. Ansible reloads SSH, resets its connection and waits for connectivity, then attempts to cancel the pending timer.

In a deliberate lockout test, the scheduled rollback restored SSH access. The service journal showed successful execution (`Result=success`, `ExecMainStatus=0`).

**Important limitations:** The current backup task expects the SSH drop-in to exist already; it is **not** a fresh-install bootstrap mechanism. The backup is created only if absent and may become stale. The cancellation logic checks Ansible reconnection, not an independent authorized login with the intended credentials. These limitations must be addressed before unattended or production use.

## Validation and GitHub Actions

The [CI workflow](.github/workflows/validate.yml) runs on `push` and `pull_request` using an Ubuntu runner. It performs:

- Checkout and Python environment setup.
- Installation of Ansible and the collections listed in [`collections/requirements.yml`](collections/requirements.yml).
- `ansible-playbook site.yml --syntax-check`.
- `ansible-lint .`.
- Python syntax compilation for [`scripts/parse_oscap.py`](scripts/parse_oscap.py).

A passing CI run verifies **static checks**, not end-to-end hardening or compliance. Runtime verification — SELinux/Apache access, audit events, firewall behavior, SSH recovery, service state, and OpenSCAP assessments — was performed separately on the lab VMs. Repeated playbook runs also demonstrated `changed=0` in specific host states; this is evidence of idempotence for those states, not a universal guarantee.

## Repository Structure

```text
.
├── .github/workflows/validate.yml    # Static CI pipeline
├── collections/requirements.yml      # Ansible collections
├── inventory/hosts.ini               # Example RHEL VM inventory
├── roles/
│   ├── baseline/                      # Security tools and sudo timeout
│   ├── users/                         # Sudo defaults
│   ├── banners/                       # Login banners
│   ├── integrity/                     # AIDE
│   ├── ssh_hardening/                 # SSH template and rollback
│   ├── kernel_hardening/              # sysctl controls
│   ├── firewall/                      # firewalld
│   ├── selinux/                       # SELinux labels and permissions
│   ├── auditd/                        # Audit monitoring rules
│   └── compliance/                    # OpenSCAP assessment tasks
├── scripts/parse_oscap.py            # XML -> Markdown summary
├── reports/                           # Scans and checkpoints
├── bootstrap.yml                      # Automation account provisioning
├── site.yml                           # Apply security controls
├── scan.yml                           # Run compliance scan
└── ansible.cfg
```

## Requirements and Usage

**Environment assumptions:** RHEL 10 lab VMs, working administrative SSH access, Python/Ansible on the controller, privilege escalation, suitable RHEL package repositories, and the RHEL 10 SCAP Security Guide data stream (`/usr/share/xml/scap/ssg/content/ssg-rhel10-ds.xml`). The current configuration also assumes an existing Apache content tree at `/srv/prodapp/public` and an existing SSH drop-in at `/etc/ssh/sshd_config.d/00-hardening.conf`. **These playbooks are not plug-and-play on a fresh or arbitrary RHEL machine.**

```bash
# 1. Install Ansible collections
ansible-galaxy collection install -r collections/requirements.yml

# 2. Set up inventory/hosts.ini for your own lab and verify SSH access
ansible webservers -m ping

# 3. Baseline assessment and report summary
ansible-playbook scan.yml -e "scan_phase=before"
python3 scripts/parse_oscap.py reports/before

# 4. Apply security hardening
ansible-playbook site.yml

# 5. Reassess
ansible-playbook scan.yml -e "scan_phase=after"
python3 scripts/parse_oscap.py reports/after
```

[`bootstrap.yml`](bootstrap.yml) is provided to create the Ansible administration account and install the controller's SSH public key, but it needs **working initial administrative credentials**. It also grants `NOPASSWD: ALL` sudo privileges to that account; do not adopt this model unchanged for production systems.

Local static validation:

```bash
ansible-playbook site.yml --syntax-check
ansible-lint .
python3 -m py_compile scripts/parse_oscap.py
```

## Limitations and Future Work

- The assessed VMs still have numerous CIS failures; **no full compliance claim** is made.
- The roles depend on specific RHEL paths, services, packages and existing host state.
- The SSH rollback should be made more robust, especially on fresh installations and when handling stale backups or verifying login semantics.
- OpenSCAP and SSH recovery tests are not yet automated on disposable RHEL runners in CI.
- Further improvements could add fixture-based Python tests, role integration tests, host-specific configuration variables, and machine-readable compliance deltas.

## Skills Demonstrated

**Linux administration · RHEL · Ansible · configuration management · SSH hardening and recovery · SELinux · firewalld · sysctl · auditd · AIDE · OpenSCAP · Bash · Python · GitHub Actions · troubleshooting**

---

*Personal infrastructure security lab built for practical learning. All deployment and failure tests were performed on controlled virtual machines.*
