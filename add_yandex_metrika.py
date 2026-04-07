# Add Yandex Metrika counter to schedule site
# Usage: python3 add_yandex_metrika.py <COUNTER_ID>
# Example: python3 add_yandex_metrika.py 12345678

import sys
import os
import re

BASE = "/root/photoimpuls-bot/schedule"
INDEX_HTML = os.path.join(BASE, "index.html")
APP_TSX = os.path.join(BASE, "src", "App.tsx")

def get_metrika_code(counter_id):
    """Generate Yandex Metrika counter code."""
    return f'''<!-- Yandex.Metrika counter -->
<script type="text/javascript">
   (function(m,e,t,r,i,k,a){{m[i]=m[i]||function(){{(m[i].a=m[i].a||[]).push(arguments)}};
   m[i].l=1*new Date();
   for (var j = 0; j < document.scripts.length; j++) {{if (document.scripts[j].src === r) {{ return; }}}}
   k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)}})
   (window, document, "script", "https://mc.yandex.ru/metrika/tag.js", "ym");

   ym({counter_id}, "init", {{
        clickmap:true,
        trackLinks:true,
        accurateTrackBounce:true,
        webvisor:true
   }});
</script>
<noscript><div><img src="https://mc.yandex.ru/watch/{counter_id}" style="position:absolute; left:-9999px;" alt="" /></div></noscript>
<!-- /Yandex.Metrika counter -->'''

def add_to_index_html(counter_id):
    """Add Metrika code to index.html (before </head> or </body>)."""
    if not os.path.isfile(INDEX_HTML):
        print(f"File not found: {INDEX_HTML}")
        return False
    with open(INDEX_HTML, "r", encoding="utf-8") as f:
        content = f.read()
    if f"ym({counter_id}" in content or f"yandex.ru/watch/{counter_id}" in content:
        print("index.html: Metrika code already present.")
        return True
    code = get_metrika_code(counter_id)
    if "</head>" in content:
        content = content.replace("</head>", code + "\n</head>", 1)
    elif "</body>" in content:
        content = content.replace("</body>", code + "\n</body>", 1)
    else:
        content = code + "\n" + content
    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(content)
    print("index.html: Metrika code added.")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 add_yandex_metrika.py <COUNTER_ID>")
        print("Example: python3 add_yandex_metrika.py 12345678")
        print("\nTo get COUNTER_ID:")
        print("1. Go to https://metrika.yandex.ru/")
        print("2. Create a counter for http://185.198.152.146:8080")
        print("3. Copy the number from ym(XXXXXX, 'init') - that's your COUNTER_ID")
        sys.exit(1)
    counter_id = sys.argv[1].strip()
    if not counter_id.isdigit():
        print("Error: COUNTER_ID must be a number (e.g., 12345678)")
        sys.exit(1)
    print(f"Adding Yandex Metrika counter {counter_id}...")
    if add_to_index_html(counter_id):
        print("Done! Rebuild the site: cd /root/photoimpuls-bot/schedule && npm run build && sudo systemctl restart schedule")
    else:
        print("Failed to add Metrika code.")
