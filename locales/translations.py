import json

with open('locales/translations.json', 'r', encoding="utf-8") as file:
    translations = json.load(file)

async def _(text, lang='text'):
    global translations
    if lang == 'text':
        return text
    else:
        try:
            return translations[lang][text]
        except:
            return text
