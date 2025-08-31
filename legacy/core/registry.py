
REGISTRY = {"extractors": []}

def register_extractor(name: str, version: str):
    def deco(cls):
        cls.__extractor_name__ = name
        cls.__version__ = version
        REGISTRY["extractors"].append(cls)
        return cls
    return deco
