# Ansible Process Module

This Ansible module allows you to manage processes on Linux systems. It supports both one-shot and long-running processes.

## Features

- Start and stop processes
- Support for one-shot and long-running processes
- PID file management for long-running processes
- Environment variable support
- Working directory specification
- Timeout handling for one-shot processes

## Requirements

- Python 3.6 or higher
- Ansible 2.9 or higher

## Installation

Place the `process.py` file in your Ansible library path, typically:

   ```bash
   mkdir -p ~/.ansible/plugins/modules/
   cp process.py ~/.ansible/plugins/modules/
   ```

## Usage

### Start a long-running process

   ```yaml
   - name: Start nginx
     process:
       command: nginx
       state: present
       background: true
       pid_file: /var/run/nginx.pid
   ```

### Run a one-shot command

   ```yaml
   - name: Run backup script
     process:
       command: /usr/local/bin/backup.sh
       state: present
       background: false
       timeout: 300
   ```

### Stop a process

   ```yaml
   - name: Stop nginx
     process:
       state: absent
       pid_file: /var/run/nginx.pid
   ```

## Parameters

| Parameter | Required | Default | Choices | Comments |
|-----------|----------|---------|---------|----------|
| command | yes | | | The command to execute |
| state | no | present | present, absent | Whether the process should be running or stopped |
| background | no | false | | Whether the process should run in the background |
| timeout | no | 300 | | Timeout in seconds for one-shot processes |
| pid_file | no | | | Path to store the PID for long-running processes |
| working_dir | no | | | Working directory for the process |
| environment | no | | | Environment variables for the process |

## Return Values

| Name | Description | Returned | Type |
|------|-------------|----------|------|
| pid | Process ID | when background is true and state is present | int |
| rc | Return code | when background is false | int |
| stdout | Standard output | always | str |
| stderr | Standard error | always | str |
| changed | Whether the state changed | always | bool |
| status | Current status of the process | always | str |

## License

GNU General Public License v3.0 or later

## Author

Robert de Bock (@robertdebock)
