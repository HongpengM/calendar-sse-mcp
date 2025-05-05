"""
Utilities for dynamically managing macOS Launch Agents for the Calendar MCP server
"""
import os
import subprocess
import sys
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List


def find_python_executable() -> Optional[str]:
    """
    Find the best Python executable to use for the launch agent
    
    Returns:
        Path to Python executable or None if not found
    """
    # First try the current Python executable
    current_python = sys.executable
    if current_python and os.path.exists(current_python):
        return current_python
    
    # Try uv executable
    uv_path = shutil.which("uv")
    if uv_path:
        return uv_path
    
    # Try python3 from PATH
    python3_path = shutil.which("python3")
    if python3_path:
        return python3_path
    
    # Try python from PATH
    python_path = shutil.which("python")
    if python_path:
        return python_path
    
    return None


def detect_system_paths() -> Dict[str, Any]:
    """
    Detect system paths and configuration for the launch agent
    
    Returns:
        Dictionary with detected configuration
    """
    # Find executable paths
    python_exec = find_python_executable()
    
    # Get module path
    module_path = Path(__file__).parent.resolve()
    
    # Get current working directory
    current_dir = Path.cwd()
    
    # Get user home directory
    user_home = Path.home()
    
    # Get launch agents directory
    launch_agents_dir = user_home / "Library" / "LaunchAgents"
    
    # Get log directory
    log_dir = os.environ.get("LOG_DIR", "/tmp")
    
    return {
        "python_exec": python_exec,
        "module_path": module_path,
        "current_dir": current_dir,
        "user_home": user_home,
        "launch_agents_dir": launch_agents_dir,
        "log_dir": log_dir
    }


def get_agent_name(name: Optional[str] = None) -> str:
    """
    Get the launch agent name, either from parameters or environment
    
    Args:
        name: Optional custom agent name
        
    Returns:
        Launch agent name
    """
    return name or os.environ.get("LAUNCH_AGENT_NAME", "com.calendar-sse-mcp")


def generate_launch_agent_plist(
    agent_name: str,
    port: int = 3000,
    log_dir: str = "/tmp",
    python_exec: Optional[str] = None,
    working_dir: Optional[str] = None
) -> str:
    """
    Generate a Launch Agent plist for the Calendar MCP server
    
    Args:
        agent_name: Name of the launch agent
        port: Server port
        log_dir: Directory for log files
        python_exec: Path to Python executable (detected if None)
        working_dir: Working directory (current directory if None)
        
    Returns:
        Launch Agent plist XML content
    """
    # Get detected paths if not provided
    if python_exec is None:
        python_exec = find_python_executable()
        if not python_exec:
            raise ValueError("Could not find Python executable")
    
    if working_dir is None:
        working_dir = str(Path.cwd())
    
    # Create plist content
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{agent_name}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_exec}</string>
        <string>-m</string>
        <string>calendar_sse_mcp</string>
        <string>server</string>
        <string>--port</string>
        <string>{port}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>{working_dir}</string>
    <key>StandardOutPath</key>
    <string>{log_dir}/{agent_name}-stdout.log</string>
    <key>StandardErrorPath</key>
    <string>{log_dir}/{agent_name}-stderr.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
        <key>SERVER_PORT</key>
        <string>{port}</string>
    </dict>
</dict>
</plist>
"""
    return plist_content


def create_launch_agent(
    agent_name: Optional[str] = None,
    port: Optional[int] = None,
    log_dir: Optional[str] = None,
    auto_load: bool = False
) -> Tuple[bool, str, Optional[Path]]:
    """
    Create and optionally load a Launch Agent for the Calendar MCP server
    
    Args:
        agent_name: Optional custom name for the agent
        port: Optional custom port
        log_dir: Optional custom log directory
        auto_load: Whether to automatically load the agent
        
    Returns:
        Tuple of (success, message, plist_path)
    """
    try:
        # Get system paths
        paths = detect_system_paths()
        
        # Get parameters or defaults
        name = get_agent_name(agent_name)
        port_num = port or int(os.environ.get("SERVER_PORT", "3000"))
        logs_dir = log_dir or paths["log_dir"]
        
        # Create the LaunchAgents directory if it doesn't exist
        paths["launch_agents_dir"].mkdir(parents=True, exist_ok=True)
        
        # Create the log directory if it doesn't exist
        Path(logs_dir).mkdir(parents=True, exist_ok=True)
        
        # Generate plist content
        plist_content = generate_launch_agent_plist(
            agent_name=name,
            port=port_num,
            log_dir=logs_dir,
            python_exec=paths["python_exec"],
            working_dir=str(paths["current_dir"])
        )
        
        # Write the plist file
        plist_path = paths["launch_agents_dir"] / f"{name}.plist"
        with open(plist_path, "w") as f:
            f.write(plist_content)
        
        message = f"Launch Agent created at: {plist_path}"
        
        # Auto-load if specified
        if auto_load:
            try:
                subprocess.run(["launchctl", "unload", str(plist_path)], check=False)
                subprocess.run(["launchctl", "load", str(plist_path)], check=True)
                message += "\nLaunch Agent loaded successfully!"
            except subprocess.CalledProcessError as e:
                message += f"\nError loading Launch Agent: {e}"
        else:
            message += f"\nTo load the Launch Agent, run: launchctl load {plist_path}"
        
        return True, message, plist_path
    except Exception as e:
        return False, f"Error creating Launch Agent: {str(e)}", None


def check_launch_agent(agent_name: Optional[str] = None, show_logs: bool = False) -> Tuple[bool, Dict[str, Any]]:
    """
    Check the status of an installed launch agent
    
    Args:
        agent_name: Optional custom name for the agent
        show_logs: Whether to include log file contents in the report
        
    Returns:
        Tuple of (is_loaded, status_info)
    """
    name = get_agent_name(agent_name)
    paths = detect_system_paths()
    plist_path = paths["launch_agents_dir"] / f"{name}.plist"
    
    # Initialize status information
    status = {
        "installed": False,
        "loaded": False,
        "plist_path": str(plist_path),
        "log_dir": paths["log_dir"],
        "stdout_log": None,
        "stderr_log": None,
        "stdout_content": None,
        "stderr_content": None,
        "process_info": None
    }
    
    # Check if the plist file exists
    if not plist_path.exists():
        return False, status
    
    status["installed"] = True
    
    # Check if the agent is loaded
    try:
        result = subprocess.run(
            ["launchctl", "list"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        if name in result.stdout:
            status["loaded"] = True
            
            # Get PID if available
            try:
                pid_result = subprocess.run(
                    ["launchctl", "list", name],
                    capture_output=True,
                    text=True,
                    check=True
                )
                status["process_info"] = pid_result.stdout
            except subprocess.CalledProcessError:
                status["process_info"] = "Could not get detailed status information"
    except subprocess.CalledProcessError:
        status["loaded"] = False
    
    # Check log files
    log_dir = paths["log_dir"]
    stdout_log = Path(log_dir) / f"{name}-stdout.log"
    stderr_log = Path(log_dir) / f"{name}-stderr.log"
    
    if stdout_log.exists():
        status["stdout_log"] = str(stdout_log)
        if show_logs:
            try:
                with open(stdout_log, "r") as f:
                    status["stdout_content"] = f.readlines()[-10:]  # Last 10 lines
            except Exception:
                status["stdout_content"] = ["Could not read log file"]
    
    if stderr_log.exists():
        status["stderr_log"] = str(stderr_log)
        if show_logs and stderr_log.stat().st_size > 0:
            try:
                with open(stderr_log, "r") as f:
                    status["stderr_content"] = f.readlines()[-10:]  # Last 10 lines
            except Exception:
                status["stderr_content"] = ["Could not read log file"]
    
    return status["loaded"], status


def uninstall_launch_agent(agent_name: Optional[str] = None) -> Tuple[bool, str]:
    """
    Uninstall a launch agent
    
    Args:
        agent_name: Optional custom name for the agent
        
    Returns:
        Tuple of (success, message)
    """
    name = get_agent_name(agent_name)
    paths = detect_system_paths()
    plist_path = paths["launch_agents_dir"] / f"{name}.plist"
    
    if not plist_path.exists():
        return False, f"Launch Agent not installed at: {plist_path}"
    
    # Unload the agent if it's loaded
    try:
        subprocess.run(["launchctl", "unload", str(plist_path)], check=True)
    except subprocess.CalledProcessError as e:
        pass  # Continue even if unload fails
    
    # Remove the plist file
    try:
        plist_path.unlink()
        return True, f"Launch Agent uninstalled: {plist_path}"
    except Exception as e:
        return False, f"Error removing Launch Agent: {str(e)}" 