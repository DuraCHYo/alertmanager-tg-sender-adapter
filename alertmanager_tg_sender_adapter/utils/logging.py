def setup_log_level(level):
    allowed = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "FATAL"}
    level = level.upper()
    return level if level in allowed else "info"
