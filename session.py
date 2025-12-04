class Session:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance.preps = {'session': {}, 'class': {}, 'method': {}}
            cls.__instance.prep_cache = {'session': {}, 'class': {}}
        return cls.__instance