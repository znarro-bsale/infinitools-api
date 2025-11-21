import subprocess
import re
from typing import Dict, Any
from config import settings


class CommandError(Exception):
    """Custom exception for command execution errors"""
    pass


def clear_special_characters(text: str) -> str:
    """Remove ANSI escape sequences from text"""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def format_response(output: str) -> tuple[str, str]:
    """
    Extract country code and format response from Go command output

    Returns:
        tuple: (country_code, formatted_output)
    """
    lines = output.strip().split('\n')
    country_code = ""

    for line in lines:
        if line.strip().startswith('País:'):
            country_match = re.search(r'País:\s*([A-Z]{2})', line)
            if country_match:
                country_code = country_match.group(1)
            break

    clean_output = clear_special_characters(output)
    return country_code, clean_output


async def call_command(command: str, **kwargs) -> str:
    """
    Execute Go binary command with provided arguments

    Args:
        command: Command name to execute (e.g., 'tobeta')
        **kwargs: Command arguments as key-value pairs

    Returns:
        str: Command output

    Raises:
        CommandError: If command execution fails
    """
    env = settings.environment

    # Determine command path based on environment
    if env == 'prod':
        path = settings.prod_executable_path
        executable_name = settings.prod_executable_name
        cmd = [f"{path}/{executable_name}", command]
    else:
        path = settings.dev_go_project_path
        cmd = ["go", "run", "main.go", command]

    # Convert kwargs to command-line arguments
    for key, value in kwargs.items():
        if isinstance(value, bool) and value:
            cmd.append(f"--{key}")
        elif not isinstance(value, bool):
            cmd.append(f"--{key}={value}")

    try:
        # Execute command
        completed_process = subprocess.run(
            cmd,
            cwd=path,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8',
            errors='replace'
        )

        return completed_process.stdout

    except subprocess.CalledProcessError as e:
        error_message = clear_special_characters(e.stderr) if e.stderr else str(e)
        raise CommandError(error_message)
    except FileNotFoundError as e:
        raise CommandError(f"Executable not found: {e}")
    except Exception as e:
        raise CommandError(f"Unexpected error: {str(e)}")


async def execute_tobeta(cpn: int, dest: str, git_user: str, motive: str) -> Dict[str, Any]:
    """
    Execute tobeta command for a single CPN

    Args:
        cpn: Company identifier
        dest: Destination environment ('beta' or 'master')
        git_user: GitHub username
        motive: Reason for the change

    Returns:
        dict: Result with success status and output/error
    """
    try:
        output = await call_command(
            command="tobeta",
            cpn=cpn,
            dest=dest,
            git_user=git_user,
            motive=motive
        )

        country_code, formatted_output = format_response(output)

        return {
            "success": True,
            "cpn": cpn,
            "country_code": country_code,
            "output": formatted_output
        }

    except CommandError as e:
        return {
            "success": False,
            "cpn": cpn,
            "error": str(e)
        }
