"""Enhanced UI/UX components with ASCII art and rich formatting.

This module provides beautiful ASCII-based UI elements for the CMD chat client.
"""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# ANSI Color Codes
class Colors:
    """ANSI color codes for terminal output."""

    # Basic colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'

    # Reset
    RESET = '\033[0m'


# Unicode Box Drawing Characters
class BoxChars:
    """Unicode box drawing characters for borders."""

    # Single line
    HORIZONTAL = '─'
    VERTICAL = '│'
    TOP_LEFT = '┌'
    TOP_RIGHT = '┐'
    BOTTOM_LEFT = '└'
    BOTTOM_RIGHT = '┘'
    T_RIGHT = '├'
    T_LEFT = '┤'
    T_DOWN = '┬'
    T_UP = '┴'
    CROSS = '┼'

    # Double line
    D_HORIZONTAL = '═'
    D_VERTICAL = '║'
    D_TOP_LEFT = '╔'
    D_TOP_RIGHT = '╗'
    D_BOTTOM_LEFT = '╚'
    D_BOTTOM_RIGHT = '╝'

    # Rounded corners
    R_TOP_LEFT = '╭'
    R_TOP_RIGHT = '╮'
    R_BOTTOM_LEFT = '╰'
    R_BOTTOM_RIGHT = '╯'


# Emojis and Icons
class Icons:
    """Common icons and emojis."""

    USER = '👤'
    MESSAGE = '💬'
    FILE = '📁'
    SEND = '📤'
    RECEIVE = '📥'
    CONNECTED = '🟢'
    DISCONNECTED = '🔴'
    WARNING = '⚠️'
    ERROR = '❌'
    SUCCESS = '✅'
    INFO = 'ℹ️'
    LOCK = '🔒'
    KEY = '🔑'
    CLOCK = '🕐'
    ARROW_RIGHT = '→'
    ARROW_LEFT = '←'
    BULLET = '•'
    STAR = '⭐'
    ROCKET = '🚀'


def get_terminal_width() -> int:
    """Get terminal width, default to 80 if unavailable."""
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return 80


def create_banner() -> str:
    """Create ASCII art banner for CMD Chat."""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   ██████╗███╗   ███╗██████╗      ██████╗██╗  ██╗ █████╗     ║
    ║  ██╔════╝████╗ ████║██╔══██╗    ██╔════╝██║  ██║██╔══██╗    ║
    ║  ██║     ██╔████╔██║██║  ██║    ██║     ███████║███████║    ║
    ║  ██║     ██║╚██╔╝██║██║  ██║    ██║     ██╔══██║██╔══██║    ║
    ║  ╚██████╗██║ ╚═╝ ██║██████╔╝    ╚██████╗██║  ██║██║  ██║    ║
    ║   ╚═════╝╚═╝     ╚═╝╚═════╝      ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝    ║
    ║                                                               ║
    ║          {Colors.YELLOW}Secure In-Memory Command Line Chat{Colors.CYAN}              ║
    ║              {Colors.GREEN}{Icons.LOCK} End-to-End Encrypted {Icons.LOCK}{Colors.CYAN}                   ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
{Colors.RESET}
"""
    return banner


def create_welcome_box(name: str, room: str, server: str) -> str:
    """Create a welcome message box.

    Args:
        name: Username
        room: Room name
        server: Server address

    Returns:
        Formatted welcome box
    """
    width = min(get_terminal_width(), 70)

    lines = [
        f"{Icons.USER} Username: {Colors.BRIGHT_CYAN}{name}{Colors.RESET}",
        f"{Icons.MESSAGE} Room: {Colors.BRIGHT_GREEN}{room}{Colors.RESET}",
        f"{Icons.CONNECTED} Server: {Colors.BRIGHT_YELLOW}{server}{Colors.RESET}",
    ]

    return create_box("Connected", lines, color=Colors.GREEN, width=width)


def create_box(title: str, content: list[str], color: str = Colors.CYAN, width: int = 60, style: str = "rounded") -> str:
    """Create a bordered box with title.

    Args:
        title: Box title
        content: List of content lines
        color: ANSI color code
        width: Box width
        style: Border style ("single", "double", "rounded")

    Returns:
        Formatted box string
    """
    if style == "double":
        tl, tr, bl, br = BoxChars.D_TOP_LEFT, BoxChars.D_TOP_RIGHT, BoxChars.D_BOTTOM_LEFT, BoxChars.D_BOTTOM_RIGHT
        h, v = BoxChars.D_HORIZONTAL, BoxChars.D_VERTICAL
    elif style == "rounded":
        tl, tr, bl, br = BoxChars.R_TOP_LEFT, BoxChars.R_TOP_RIGHT, BoxChars.R_BOTTOM_LEFT, BoxChars.R_BOTTOM_RIGHT
        h, v = BoxChars.HORIZONTAL, BoxChars.VERTICAL
    else:
        tl, tr, bl, br = BoxChars.TOP_LEFT, BoxChars.TOP_RIGHT, BoxChars.BOTTOM_LEFT, BoxChars.BOTTOM_RIGHT
        h, v = BoxChars.HORIZONTAL, BoxChars.VERTICAL

    # Calculate content width
    content_width = width - 4

    # Top border with title
    title_str = f" {title} "
    title_padding = (width - len(title_str) - 2) // 2
    top_line = f"{color}{tl}{h * title_padding}{title_str}{h * (width - title_padding - len(title_str) - 2)}{tr}{Colors.RESET}"

    # Content lines
    lines = [top_line]
    for line in content:
        # Strip ANSI codes for length calculation
        import re
        clean_line = re.sub(r'\033\[[0-9;]+m', '', line)
        padding = content_width - len(clean_line)
        lines.append(f"{color}{v}{Colors.RESET} {line}{' ' * padding} {color}{v}{Colors.RESET}")

    # Bottom border
    bottom_line = f"{color}{bl}{h * (width - 2)}{br}{Colors.RESET}"
    lines.append(bottom_line)

    return '\n'.join(lines)


def create_separator(width: int = 60, char: str = BoxChars.HORIZONTAL, color: str = Colors.CYAN) -> str:
    """Create a separator line.

    Args:
        width: Line width
        char: Character to use
        color: ANSI color code

    Returns:
        Formatted separator
    """
    return f"{color}{char * width}{Colors.RESET}"


def create_message_box(sender: str, message: str, timestamp: str, is_own: bool = False) -> str:
    """Create a styled message box.

    Args:
        sender: Message sender
        message: Message content
        timestamp: Message timestamp
        is_own: Whether this is the user's own message

    Returns:
        Formatted message box
    """
    if is_own:
        sender_color = Colors.BRIGHT_MAGENTA
        border_color = Colors.MAGENTA
        prefix = Icons.SEND
    else:
        sender_color = Colors.BRIGHT_CYAN
        border_color = Colors.CYAN
        prefix = Icons.RECEIVE

    header = f"{prefix} {sender_color}{Colors.BOLD}{sender}{Colors.RESET} {Colors.DIM}{timestamp}{Colors.RESET}"

    # Word wrap message
    width = min(get_terminal_width(), 80) - 6
    wrapped_lines = []
    words = message.split()
    current_line = ""

    for word in words:
        if len(current_line) + len(word) + 1 <= width:
            current_line += (word + " ")
        else:
            if current_line:
                wrapped_lines.append(current_line.rstrip())
            current_line = word + " "
    if current_line:
        wrapped_lines.append(current_line.rstrip())

    # Build box
    result = [header]
    for line in wrapped_lines:
        result.append(f"  {border_color}{BoxChars.VERTICAL}{Colors.RESET} {line}")

    return '\n'.join(result)


def create_system_message(message: str, msg_type: str = "info") -> str:
    """Create a styled system message.

    Args:
        message: Message content
        msg_type: Type of message ("info", "success", "warning", "error")

    Returns:
        Formatted system message
    """
    icon_map = {
        "info": (Icons.INFO, Colors.BLUE),
        "success": (Icons.SUCCESS, Colors.GREEN),
        "warning": (Icons.WARNING, Colors.YELLOW),
        "error": (Icons.ERROR, Colors.RED),
    }

    icon, color = icon_map.get(msg_type, (Icons.INFO, Colors.BLUE))
    return f"{color}{icon} {Colors.BOLD}System:{Colors.RESET} {message}"


def create_progress_bar(current: int, total: int, width: int = 40, label: str = "") -> str:
    """Create a progress bar.

    Args:
        current: Current progress value
        total: Total value
        width: Bar width in characters
        label: Optional label

    Returns:
        Formatted progress bar
    """
    if total == 0:
        percent = 0
    else:
        percent = min(100, int((current / total) * 100))

    filled = int((current / total) * width) if total > 0 else 0
    bar = '█' * filled + '░' * (width - filled)

    color = Colors.GREEN if percent == 100 else Colors.YELLOW if percent >= 50 else Colors.RED

    progress_str = f"{color}[{bar}] {percent}%{Colors.RESET}"
    if label:
        progress_str = f"{label}: {progress_str}"

    if current < total:
        progress_str += f" ({current}/{total})"

    return progress_str


def create_file_transfer_box(filename: str, filesize: int, sender: str, progress: float = 0.0) -> str:
    """Create a file transfer notification box.

    Args:
        filename: Name of the file
        filesize: File size in bytes
        sender: Sender name
        progress: Transfer progress (0.0 to 1.0)

    Returns:
        Formatted file transfer box
    """
    from ..utils import format_filesize

    size_str = format_filesize(filesize)

    if progress == 0.0:
        # Initial notification
        lines = [
            f"{Icons.FILE} File: {Colors.BRIGHT_YELLOW}{filename}{Colors.RESET}",
            f"{Icons.USER} From: {Colors.BRIGHT_CYAN}{sender}{Colors.RESET}",
            f"📊 Size: {Colors.BRIGHT_GREEN}{size_str}{Colors.RESET}",
        ]
        return create_box("Incoming File", lines, color=Colors.YELLOW, width=60)
    # Progress update
    current_bytes = int(filesize * progress)
    bar = create_progress_bar(current_bytes, filesize, width=40, label="Transfer")
    return f"{Icons.FILE} {filename}: {bar}"


def create_help_menu() -> str:
    """Create a help menu with available commands.

    Returns:
        Formatted help menu
    """
    commands = [
        ("/help", "Show this help message"),
        ("/quit", "Disconnect and exit"),
        ("/name <name>", "Change your display name"),
        ("/room <room>", "Switch to a different room"),
        ("/send <file>", "Send a file to the room"),
        ("/clear", "Clear the screen"),
    ]

    lines = []
    for cmd, desc in commands:
        lines.append(f"{Colors.BRIGHT_GREEN}{cmd:<20}{Colors.RESET} {BoxChars.VERTICAL} {desc}")

    return create_box("Available Commands", lines, color=Colors.BLUE, width=70)


def clear_screen() -> None:
    """Clear the terminal screen."""
    import os
    import shutil
    import subprocess

    # Prefer running the clear command directly without a shell.
    cmd = "cls" if os.name == "nt" else "clear"
    exe = shutil.which(cmd)
    if exe:
        # Run without shell to avoid shell injection risks flagged by bandit
        subprocess.run([exe], check=False)
    else:
        # Fallback: print newlines to simulate a clear
        print("\n" * 100)


def create_status_line(room: str, users_count: int = 0, connected: bool = True) -> str:
    """Create a status line for the bottom of the screen.

    Args:
        room: Current room name
        users_count: Number of users in room
        connected: Connection status

    Returns:
        Formatted status line
    """
    width = get_terminal_width()

    status_icon = Icons.CONNECTED if connected else Icons.DISCONNECTED
    status_color = Colors.GREEN if connected else Colors.RED

    status_text = f"{status_color}{status_icon} {room}{Colors.RESET}"
    if users_count > 0:
        status_text += f" {Colors.DIM}({users_count} users){Colors.RESET}"

    # Pad to full width
    import re
    clean_text = re.sub(r'\033\[[0-9;]+m', '', status_text)
    padding = width - len(clean_text) - 1

    return f"{status_text}{' ' * padding}"
