import random


def turn(p: float) -> bool:
    if random.random() <= p:
        return True
    return False
