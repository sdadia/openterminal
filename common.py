import dotenv
from prompt_toolkit.history import FileHistory
from rich import console
from prompt_toolkit import PromptSession

dotenv.load_dotenv()

console = console.Console()
session = PromptSession(
    enable_history_search=True, history=FileHistory(".session_history")
)
