# --- Registry ---
CHORD_REGISTRY = {}
STYLE_REGISTRY = {}

def register_chord(name):
    def decorator(cls):
        CHORD_REGISTRY[name] = cls
        return cls
    return decorator

def register_style(name):
    def decorator(cls):
        STYLE_REGISTRY[name] = cls
        return cls
    return decorator
