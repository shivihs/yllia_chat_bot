from langfuse import Langfuse
from config import LANGFUSE_API_KEY, LANGFUSE_HOST

langfuse = Langfuse(secret_key=LANGFUSE_API_KEY, host=LANGFUSE_HOST)

def log_interaction(session_id: str, user_input: str, response: str, feedback: str = None):
    """
    Zapisuje interakcję w Langfuse.
    """
    trace = langfuse.trace(session_id)
    trace.log(user_input=user_input, response=response, feedback=feedback)
