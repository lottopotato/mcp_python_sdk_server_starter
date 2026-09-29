from dataclasses import dataclass

@dataclass
class ModuleConfig:
    pass

class Module:
    def __init__(self, config: ModuleConfig):
        self.config = config