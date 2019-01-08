from lidske_aktivity.config import Config


class BaseDialog:
    def __init__(self, *args, **kwargs):
        pass


class BaseConfigDialog(BaseDialog):
    config: Config

    def __init__(self, config: Config, *args, **kwargs):
        self.config = config
        super().__init__(*args, **kwargs)
