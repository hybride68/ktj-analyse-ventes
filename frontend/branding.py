import os

HERE = os.path.dirname(__file__)
PAGE_ICON = os.path.join(HERE, "page_icon.png")

if not os.path.isfile(PAGE_ICON):
    PAGE_ICON = "✨"
