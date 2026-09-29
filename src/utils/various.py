import uuid

def random_uuid() -> str:
    return str(uuid.uuid4())

def random_uuid4() -> str:
    return random_uuid()