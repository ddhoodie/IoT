import threading

console_lock = threading.Lock()

def safe_print(*args, **kwargs):
    # garantuje da print i prompt ne upadaju u input
    with console_lock:
        print(*args, **kwargs)

def print_prompt():
    with console_lock:
        print("> ", end="", flush=True)