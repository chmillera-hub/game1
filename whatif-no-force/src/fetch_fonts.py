"""Download the open-license (SIL OFL) handwriting fonts used for Kai's sketchbook."""
import os
import re
import urllib.request

import paths

FONTS = os.path.join(paths.BUILD, "fonts")
CSS = "https://fonts.googleapis.com/css2?family=Caveat:wght@600;700&family=Patrick+Hand"
NAMES = ["Caveat-SemiBold.ttf", "Caveat-Bold.ttf", "PatrickHand-Regular.ttf"]


def fetch():
    os.makedirs(FONTS, exist_ok=True)
    if all(os.path.exists(os.path.join(FONTS, n)) for n in NAMES):
        return FONTS
    css = urllib.request.urlopen(CSS).read().decode()
    urls = re.findall(r"https://[^)]+\.ttf", css)
    for name, url in zip(NAMES, urls):
        with open(os.path.join(FONTS, name), "wb") as f:
            f.write(urllib.request.urlopen(url).read())
    return FONTS


if __name__ == "__main__":
    print(fetch())
