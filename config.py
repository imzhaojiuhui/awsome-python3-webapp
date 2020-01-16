
import config_default

configs = config_default.configs
try:
    import config_override
    # configs = config_override.configs
except ImportError:
    pass