# Ansible Process Module

An Ansible module for managing processes on Linux systems. This module can start and stop processes, handle both one-shot and long-running processes, and provides robust process management capabilities.

## Features

- Start and stop processes
- Support for both one-shot and background processes
- Process validation and management
- PID file handling
- Environment variable support
- Working directory configuration
- Timeout handling
- Process tree management

## Installation

### From Galaxy (when published)
```bash
ansible-galaxy collection install robertdebock.system
```

### From Source
```bash
# Clone the repository
git clone https://github.com/robertdebock/ansible.module.process.git
cd ansible.module.process

# Install dependencies
pip install -r requirements.txt

# Build and install collection
ansible-galaxy collection build ansible_collections/robertdebock/system
ansible-galaxy collection install robertdebock-system-1.0.0.tar.gz --force
```

## Testing

This collection is automatically tested using GitHub Actions CI/CD pipeline:

### Automated Testing

Every push to the repository triggers comprehensive testing:

- ✅ **Multi-Python Testing**: Tests across Python 3.8, 3.9, 3.10, 3.11
- ✅ **Collection Build**: Builds and validates the collection package
- ✅ **Function Tests**: Tests individual module functions
- ✅ **Module Tests**: Tests the complete module functionality
- ✅ **Ansible Integration**: Tests with actual Ansible playbooks
- ✅ **Installation Test**: Verifies collection installs correctly

### Test Status

Check the latest test results in the [Actions tab](https://github.com/robertdebock/ansible.module.process/actions) of the repository.

## Usage Examples

### Start a long-running process
```yaml
- name: Start nginx
  robertdebock.system.process:
    command: nginx
    state: present
    background: true
    pid_file: /var/run/nginx.pid
```

### Run a one-shot command
```yaml
- name: Run backup script
  robertdebock.system.process:
    command: /usr/local/bin/backup.sh
    state: present
    background: false
    timeout: 300
```

### Stop a process
```yaml
- name: Stop nginx
  robertdebock.system.process:
    state: absent
    pid_file: /var/run/nginx.pid
```

### With environment variables
```yaml
- name: Run script with environment
  robertdebock.system.process:
    command: /path/to/script.sh
    state: present
    background: true
    environment:
      ENV_VAR: "value"
      DEBUG: "true"
    working_dir: /opt/myapp
```

## Module Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| command | str | Yes | - | The command to execute |
| state | str | No | present | Whether the process should be running (present) or stopped (absent) |
| background | bool | No | false | Whether the process should run in the background |
| timeout | int | No | 300 | Timeout in seconds for one-shot processes |
| pid_file | str | No | - | Path to store the PID for long-running processes |
| working_dir | str | No | - | Working directory for the process |
| environment | dict | No | - | Environment variables for the process |

## Requirements

- Python >= 3.6
- psutil >= 5.0.0
- Ansible >= 2.9

## Development

### Prerequisites
```bash
pip install -r requirements.txt
```

### Building Collection
```bash
ansible-galaxy collection build ansible_collections/robertdebock/system
```

### CI/CD Testing

All testing is handled automatically by GitHub Actions:

- **Push to master**: Triggers comprehensive testing across multiple Python versions
- **Create tag**: Triggers testing, building, and publishing to Ansible Galaxy
- **Pull requests**: Triggers testing to ensure code quality

See the [Actions tab](https://github.com/robertdebock/ansible.module.process/actions) for test results.

## License

GPL-3.0-or-later

## Author

Robert de Bock (@robertdebock)
