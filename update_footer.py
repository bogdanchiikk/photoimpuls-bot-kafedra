# Обновление футера: логотип крупнее, улучшенный вид
# Загрузите на сервер в /root/photoimpuls-bot/ и выполните: python3 update_footer.py

path = "/root/photoimpuls-bot/schedule/src/App.tsx"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Старый футер (как сейчас)
old_footer = '''      <footer className="mt-16 py-6 border-t border-gray-200 bg-white text-center text-gray-600 text-sm">
        <p className="mb-2">Создано агентством Кафедра</p>
        <img src="/kafedra-logo.png" alt="Кафедра" className="h-12 mx-auto" />
      </footer>'''

# Новый: логотип h-24 (96px), больше отступы, текст чуть крупнее
new_footer = '''      <footer className="mt-20 py-10 border-t border-gray-200 bg-white text-center text-gray-600">
        <p className="mb-4 text-base">Создано агентством Кафедра</p>
        <img src="/kafedra-logo.png" alt="Кафедра" className="h-24 w-auto mx-auto object-contain" />
      </footer>'''

if old_footer in content:
    content = content.replace(old_footer, new_footer, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Футер обновлён: логотип увеличен, отступы улучшены.")
else:
    print("Старый футер не найден. Возможно, разметка уже другая.")
    print("Проверьте файл: nano /root/photoimpuls-bot/schedule/src/App.tsx")
