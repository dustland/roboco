"""
RoboCo UI package.

This package provides a web interface for RoboCo.
"""

from roboco.ui.app import main
from roboco.ui.utils import init_session_state, check_api_connection, get_api_url, load_css, hide_raw_css, clean_ui_display
from roboco.ui.chat import chat_view, handle_chat_input
from roboco.ui.files import explore_project_files, display_file_content
from roboco.ui.status import update_execution_log, display_execution_status
from roboco.ui.settings import settings_view
from roboco.ui.sidebar import sidebar_content

__all__ = [
    "main",
    "init_session_state",
    "check_api_connection",
    "get_api_url",
    "load_css",
    "hide_raw_css",
    "clean_ui_display",
    "chat_view",
    "handle_chat_input",
    "explore_project_files",
    "display_file_content",
    "update_execution_log",
    "display_execution_status",
    "settings_view",
    "sidebar_content"
] 