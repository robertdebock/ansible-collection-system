#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Robert de Bock <robert@meinit.nl>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: process
short_description: Manage processes
description:
  - Start and stop processes on Linux systems.
  - Supports both one-shot and long-running processes.
version_added: "1.0.0"
author: Robert de Bock (@robertdebock)
options:
  command:
    description:
      - The command to execute.
    type: str
    required: true
  state:
    description:
      - Whether the process should be running or stopped.
    type: str
    choices: [ present, absent ]
    default: present
  background:
    description:
      - Whether the process should run in the background.
      - If false, the module will wait for the process to complete.
    type: bool
    default: false
  timeout:
    description:
      - Timeout in seconds for one-shot processes.
      - Only used when background is false.
    type: int
    default: 300
  pid_file:
    description:
      - Path to store the PID for long-running processes.
      - Only used when background is true.
    type: str
  working_dir:
    description:
      - Working directory for the process.
    type: str
  environment:
    description:
      - Environment variables for the process.
    type: dict
requirements:
  - python >= 3.6
  - psutil >= 5.0.0
'''

EXAMPLES = r'''
# Start a long-running process
- name: Start nginx
  robertdebock.process.process:
    command: nginx
    state: present
    background: true
    pid_file: /var/run/nginx.pid

# Run a one-shot command
- name: Run backup script
  robertdebock.process.process:
    command: /usr/local/bin/backup.sh
    state: present
    background: false
    timeout: 300
'''

RETURN = r'''
pid:
  description: Process ID (for long-running processes)
  returned: when background is true and state is present
  type: int
  sample: 1234
rc:
  description: Return code (for one-shot processes)
  returned: when background is false
  type: int
  sample: 0
stdout:
  description: Standard output
  returned: always
  type: str
  sample: "Process started successfully"
stderr:
  description: Standard error
  returned: always
  type: str
  sample: ""
changed:
  description: Whether the state changed
  returned: always
  type: bool
  sample: true
status:
  description: Current status of the process
  returned: always
  type: str
  sample: "running"
'''

import os
import signal
import subprocess
import time
import shlex
import psutil
from ansible.module_utils.basic import AnsibleModule

def read_pid_file(pid_file):
    """Read PID from file."""
    if os.path.exists(pid_file):
        with open(pid_file, 'r') as f:
            try:
                return int(f.read().strip())
            except ValueError:
                return None
    return None

def write_pid_file(pid_file, pid):
    """Write PID to file."""
    with open(pid_file, 'w') as f:
        f.write(str(pid))

def is_process_running(pid):
    """Check if process is running."""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False

def get_process_info(pid):
    """Get process information using psutil."""
    try:
        process = psutil.Process(pid)
        return {
            'pid': process.pid,
            'name': process.name(),
            'cmdline': ' '.join(process.cmdline()),
            'status': process.status(),
            'create_time': process.create_time()
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None

def find_process_by_command(command):
    """Find process by command pattern."""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if command in ' '.join(proc.info['cmdline']):
                    return proc.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied, TypeError):
                continue
    except Exception:
        pass
    return None

def kill_process_tree(pid, timeout=10):
    """Kill process and its children."""
    try:
        process = psutil.Process(pid)
        children = process.children(recursive=True)
        
        # First try graceful termination
        process.terminate()
        for child in children:
            try:
                child.terminate()
            except psutil.NoSuchProcess:
                pass
        
        # Wait for processes to terminate
        gone, still_alive = psutil.wait_procs(children + [process], timeout=timeout)
        
        # Force kill if still alive
        for proc in still_alive:
            try:
                proc.kill()
            except psutil.NoSuchProcess:
                pass
                
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False

def main():
    module = AnsibleModule(
        argument_spec=dict(
            command=dict(type='str', required=False),
            state=dict(type='str', choices=['present', 'absent'], default='present'),
            background=dict(type='bool', default=False),
            timeout=dict(type='int', default=300),
            pid_file=dict(type='str'),
            working_dir=dict(type='str'),
            environment=dict(type='dict'),
        ),
        supports_check_mode=True,
    )

    command = module.params['command']
    state = module.params['state']
    background = module.params['background']
    timeout = module.params['timeout']
    pid_file = module.params['pid_file']
    working_dir = module.params['working_dir']
    environment = module.params['environment']
    
    # Validate required parameters
    if state == 'present' and not command:
        module.fail_json(msg="command is required when state is present")

    result = dict(
        changed=False,
        stdout='',
        stderr='',
        status='',
    )

    if module.check_mode:
        module.exit_json(**result)

    # Handle process management
    if state == 'present':
        if background:
            if pid_file:
                pid = read_pid_file(pid_file)
                if pid and is_process_running(pid):
                    # Verify it's actually our process
                    proc_info = get_process_info(pid)
                    if proc_info and command in proc_info['cmdline']:
                        result['status'] = 'running'
                        result['pid'] = pid
                        result['stdout'] = f"Process already running with PID {pid}"
                        module.exit_json(**result)
                    else:
                        # Stale PID file, remove it
                        os.unlink(pid_file)

            try:
                # Use shlex to safely parse command
                cmd_args = shlex.split(command)
                process = subprocess.Popen(
                    cmd_args,
                    shell=False,  # Safer than shell=True
                    cwd=working_dir,
                    env=environment,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    preexec_fn=os.setsid,
                )
                result['changed'] = True
                result['pid'] = process.pid
                result['status'] = 'running'
                result['stdout'] = f"Process started with PID {process.pid}"
                if pid_file:
                    write_pid_file(pid_file, process.pid)
            except Exception as e:
                module.fail_json(msg=f"Failed to start process: {str(e)}")

        else:
            try:
                # Use shlex to safely parse command
                cmd_args = shlex.split(command)
                process = subprocess.Popen(
                    cmd_args,
                    shell=False,  # Safer than shell=True
                    cwd=working_dir,
                    env=environment,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                stdout, stderr = process.communicate(timeout=timeout)
                result['changed'] = True
                result['rc'] = process.returncode
                result['stdout'] = stdout.decode('utf-8')
                result['stderr'] = stderr.decode('utf-8')
                result['status'] = 'completed'
            except subprocess.TimeoutExpired:
                process.kill()
                module.fail_json(msg="Process timed out")
            except Exception as e:
                module.fail_json(msg=f"Failed to run process: {str(e)}")

    else:  # state == 'absent'
        if pid_file:
            pid = read_pid_file(pid_file)
            if pid and is_process_running(pid):
                try:
                    # Use improved process killing
                    if kill_process_tree(pid):
                        result['changed'] = True
                        result['status'] = 'stopped'
                        result['stdout'] = f"Process {pid} and its children stopped"
                        # Clean up PID file
                        os.unlink(pid_file)
                    else:
                        module.fail_json(msg=f"Failed to stop process {pid}")
                except Exception as e:
                    module.fail_json(msg=f"Failed to stop process: {str(e)}")
            else:
                result['status'] = 'not_running'
                result['stdout'] = "Process not running"
                # Clean up stale PID file
                if os.path.exists(pid_file):
                    os.unlink(pid_file)
        else:
            # Try to find process by command
            pid = find_process_by_command(command)
            if pid:
                try:
                    if kill_process_tree(pid):
                        result['changed'] = True
                        result['status'] = 'stopped'
                        result['stdout'] = f"Process {pid} stopped"
                    else:
                        module.fail_json(msg=f"Failed to stop process {pid}")
                except Exception as e:
                    module.fail_json(msg=f"Failed to stop process: {str(e)}")
            else:
                result['status'] = 'not_found'
                result['stdout'] = "Process not found"

    module.exit_json(**result)

if __name__ == '__main__':
    main() 
