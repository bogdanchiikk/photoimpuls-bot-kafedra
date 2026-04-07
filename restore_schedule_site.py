# Restore footer and yellow border on schedule site. Run on server: python3 restore_schedule_site.py
import re
import os

BASE = "/root/photoimpuls-bot/schedule"
APP_PATH = os.path.join(BASE, "src", "App.tsx")
SESSION_CARD_PATH = os.path.join(BASE, "src", "components", "SessionCard.tsx")

# Footer: logo links to kafedra.agency (Russian text as Unicode)
TEXT_FOOTER = "\u0421\u043e\u0437\u0434\u0430\u043d\u043e \u0430\u0433\u0435\u043d\u0442\u0441\u0442\u0432\u043e\u043c \u041a\u0430\u0444\u0435\u0434\u0440\u0430"
TEXT_ALT = "\u041a\u0430\u0444\u0435\u0434\u0440\u0430"

footer_block = '''
      <footer className="mt-20 py-10 border-t border-gray-200 bg-white text-center text-gray-600">
        <p className="mb-4 text-base">''' + TEXT_FOOTER + '''</p>
        <a href="https://kafedra.agency" target="_blank" rel="noopener noreferrer">
          <img src="/kafedra-logo.png" alt="''' + TEXT_ALT + '''" className="h-24 w-auto mx-auto object-contain" />
        </a>
      </footer>
'''

def fix_app_tsx():
    if not os.path.isfile(APP_PATH):
        print("File not found:", APP_PATH)
        return False
    with open(APP_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    if "kafedra-logo.png" in content and "kafedra.agency" not in content:
        old_img = '<img src="/kafedra-logo.png" alt="' + TEXT_ALT + '" className="h-24 w-auto mx-auto object-contain" />'
        new_img = '''<a href="https://kafedra.agency" target="_blank" rel="noopener noreferrer">
          <img src="/kafedra-logo.png" alt="''' + TEXT_ALT + '''" className="h-24 w-auto mx-auto object-contain" />
        </a>'''
        if old_img in content:
            content = content.replace(old_img, new_img, 1)
            with open(APP_PATH, "w", encoding="utf-8") as f:
                f.write(content)
            print("App.tsx: link to kafedra.agency added for logo.")
            return True
    if TEXT_FOOTER in content and "kafedra.agency" in content:
        print("App.tsx: footer already has link.")
        return True
    if TEXT_FOOTER in content and "kafedra-logo.png" in content:
        print("App.tsx: footer already present.")
        return True
    pattern = r'(</main>\s*)(\s*</div>)'
    replacement = r'\1' + footer_block + r'\2'
    new_content, n = re.subn(pattern, replacement, content, count=1)
    if n == 0:
        pattern2 = r'(</main>)(\s*</div>)'
        new_content, n = re.subn(pattern2, replacement, content, count=1)
    if n > 0:
        with open(APP_PATH, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("App.tsx: footer added.")
        return True
    print("App.tsx: could not find </main> ... </div>")
    return False

def fix_session_card_tsx():
    if not os.path.isfile(SESSION_CARD_PATH):
        print("File not found:", SESSION_CARD_PATH)
        return False
    with open(SESSION_CARD_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    if "D1_1200_H5" in content and "ring-yellow" in content:
        print("SessionCard.tsx: yellow border already present.")
        return True
    def replacer(m):
        inner = m.group(1)
        if "cell_id" in inner or "D1_1200" in inner:
            return m.group(0)
        return 'className={`' + inner + " ${data.cell_id === 'D1_1200_H5' ? 'ring-4 ring-yellow-400' : ''}" + '`}'
    pattern = r'className="([^"]*rounded[^"]*)"'
    new_content, n = re.subn(pattern, replacer, content, count=1)
    if n == 0:
        pattern2 = r'className=\{`([^`]*)`\}'
        def replacer2(m):
            inner = m.group(1)
            if "D1_1200_H5" in inner:
                return m.group(0)
            return 'className={`' + inner + " ${data.cell_id === 'D1_1200_H5' ? 'ring-4 ring-yellow-400' : ''}" + '`}'
        new_content, n = re.subn(pattern2, replacer2, content, count=1)
    if n == 0:
        pattern3 = r'className="([^"]+)"'
        def replacer3(m):
            inner = m.group(1)
            if "ring-yellow" in inner or "D1_1200" in inner:
                return m.group(0)
            return 'className={`' + inner + " ${data.cell_id === 'D1_1200_H5' ? 'ring-4 ring-yellow-400' : ''}" + '`}'
        new_content, n = re.subn(pattern3, replacer3, content, count=1)
    if n > 0:
        with open(SESSION_CARD_PATH, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("SessionCard.tsx: yellow border added.")
        return True
    print("SessionCard.tsx: could not find card className.")
    return False

if __name__ == "__main__":
    print("Restoring footer and yellow border...")
    fix_app_tsx()
    fix_session_card_tsx()
    print("Done. Run: cd /root/photoimpuls-bot/schedule && npm run build && sudo systemctl restart schedule")
