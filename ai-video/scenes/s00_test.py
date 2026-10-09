from engine.core import *
def render(ctx, t, info):
    bg(ctx, "ai_bg")
    o, w = info.mouth("ai", t)
    ellipse(ctx, 540, 800, 200 + 60*w, 20 + 160*o); fill(ctx, "ai_eye")
    text(ctx, f"t={t:.2f}", 540, 300, 80, "white", "title")
