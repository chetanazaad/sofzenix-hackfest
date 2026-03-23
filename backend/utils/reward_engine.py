import random


def generate_reward(min_amount: float = 50.0, max_amount: float = 350.0) -> float:
    raw = random.uniform(min_amount, max_amount)
    rounded = round(raw / 10) * 10
    return max(min_amount, min(max_amount, rounded))


def bulk_generate_rewards(count: int, min_amount: float = 50.0, max_amount: float = 350.0) -> list:
    return [generate_reward(min_amount, max_amount) for _ in range(count)]
