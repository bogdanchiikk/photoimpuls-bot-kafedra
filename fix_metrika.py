# Fix Yandex Metrika code in index.html (move noscript from head to body)
import os
import re

INDEX_HTML = "/root/photoimpuls-bot/schedule/index.html"

if not os.path.isfile(INDEX_HTML):
    print(f"File not found: {INDEX_HTML}")
    exit(1)

with open(INDEX_HTML, "r", encoding="utf-8") as f:
    content = f.read()

# Find and remove noscript from head
noscript_pattern = r'<noscript><div><img src="https://mc\.yandex\.ru/watch/\d+" style="position:absolute; left:-9999px;" alt="" /></div></noscript>'
noscript_match = re.search(noscript_pattern, content)
if noscript_match:
    noscript_code = noscript_match.group(0)
    # Remove from current location
    content = content.replace(noscript_code, "", 1)
    # Add to body (before </body>)
    if "</body>" in content:
        content = content.replace("</body>", noscript_code + "\n</body>", 1)
        with open(INDEX_HTML, "w", encoding="utf-8") as f:
            f.write(content)
        print("Fixed: moved noscript from head to body.")
    else:
        print("Error: </body> not found.")
else:
    print("Noscript not found or already fixed.")
