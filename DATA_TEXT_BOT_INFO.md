# 📝 Bot mit Data_Text (Nur Text-Posts)

## ✅ Änderungen an `auto_post_comment_bot_pythonanywhere.py`

Der Bot nutzt jetzt **Data_Text** statt data_all:
- **100 Top Text-Posts** (ohne Bilder)
- Alle mit hohem Score (25k bis 3k+)
- ADHD-relevant und emotional

## 🎯 Vorteile

1. **Sicherer**: Text-Posts werden seltener entfernt
2. **Einfacher**: Keine Bild-Probleme
3. **Universeller**: Funktioniert in allen Subreddits
4. **Qualität**: Nur die besten Posts (Top 100)

## 📂 Struktur auf PythonAnywhere

```
/home/lucawahl/Reddit/
├── Data_Text/
│   ├── Posts/
│   │   ├── text_001_*/
│   │   ├── text_002_*/
│   │   └── ... (100 Posts)
│   └── TOP_100_TEXT_POSTS.md
└── auto_post_comment_bot_pythonanywhere.py
```

## 🚀 Verwendung

```bash
# Auf PythonAnywhere
cd /home/lucawahl/Reddit
python3 auto_post_comment_bot_pythonanywhere.py
```

## 📊 Bot-Einstellungen

- **Posts**: 1-2 pro Tag (an aktiven Tagen)
- **Kommentare**: 2-5 pro Tag
- **Pausentage**: 55% (mehr Pause als Aktivität)
- **Nur Text-Posts**: Keine Bilder!

## 📝 Top 5 Posts (Beispiele)

1. **Score 25,114**: "I teach English at a university..."
2. **Score 14,183**: "My son's ADHD saved his sister's life"
3. **Score 11,745**: "I've been leaving secret mystery gifts..."
4. **Score 10,020**: "I Hired A Cleaner To Help Me..."
5. **Score 9,958**: "Something I've never told my husband..."

## ⚠️ Upload zu PythonAnywhere

1. Upload `Data_Text` Ordner komplett
2. Upload neuen `auto_post_comment_bot_pythonanywhere.py`
3. Bot startet automatisch mit Text-Posts

## 🔧 Technische Details

- Entfernt: Bild-Download-Funktionen
- Vereinfacht: Nur `submit()` mit `selftext`
- Sicherer: Keine URL-Posts mehr