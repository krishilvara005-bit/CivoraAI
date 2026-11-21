from . import cost, structure, vastu


def analyze_all(inputs, has_plan, ctx=None):
    """ctx (optional) carries where each value came from and facts read off the drawing."""
    return {
        "structure": structure.analyze(inputs, has_plan, ctx),
        "cost": cost.analyze(inputs, has_plan, ctx),
        "vastu": vastu.analyze(inputs, has_plan, ctx),
    }
