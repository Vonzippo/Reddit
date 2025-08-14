# 📊 Neue Reddit Bot Limits

## ✅ Angepasste Tageslimits

### Posts
- **ALT**: 3-5 Posts pro Tag
- **NEU**: 1-2 Posts pro Tag (MAX 2)

### Kommentare  
- **ALT**: 3-7 Kommentare pro Tag
- **NEU**: 2-5 Kommentare pro Tag (MAX 5)

## 📁 Geänderte Dateien

1. **auto_post_comment_bot.py**
   - `max_posts_per_day`: 2
   - `max_comments_per_day`: 5
   - Tägliche Ziele: 1-2 Posts, 2-5 Kommentare

2. **auto_post_comment_bot_pythonanywhere.py** 
   - Gleiche Limits für PythonAnywhere

3. **main_other.py**
   - Posts: `random.randint(1, 2)`
   - Kommentare: `random.randint(2, 5)`

## 🎯 Warum diese Limits?

- **Sicherer**: Weniger Aktivität = geringeres Ban-Risiko
- **Natürlicher**: Wirkt mehr wie ein echter User
- **Qualität > Quantität**: Mehr Zeit zwischen Posts für bessere Auswahl

## ⏰ Zeitabstände (unverändert)

- **Zwischen Posts**: 30 Min - 2 Stunden
- **Zwischen Kommentaren**: 5 - 30 Minuten
- **Aktive Stunden**: 10:00 - 22:00

## 🚀 Verwendung

```bash
# Lokal testen
python3 auto_post_comment_bot.py

# Auf PythonAnywhere
python3 auto_post_comment_bot_pythonanywhere.py
```