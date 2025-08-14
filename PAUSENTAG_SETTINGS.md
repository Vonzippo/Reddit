# 😴 Pausentag-Einstellungen

## ✅ NEUE EINSTELLUNG: 55% Pausentage!

Der Bot macht jetzt **mehr Pausen als er aktiv ist** - das wirkt viel natürlicher!

## 📊 Statistik

### Pro Monat (30 Tage):
- **~17 Pausentage** (Bot macht nichts)
- **~13 aktive Tage** (Bot postet/kommentiert)

### Pro Woche (7 Tage):
- **~4 Pausentage** 
- **~3 aktive Tage**

## 🎯 An aktiven Tagen:
- **1-2 Posts** (max 2)
- **2-5 Kommentare** (max 5)

## 😴 An Pausentagen:
- **0 Posts**
- **0 Kommentare**
- Bot wartet bis zum nächsten Tag

## 💡 Warum ist das gut?

1. **Natürlicher**: Echte User sind auch nicht jeden Tag aktiv
2. **Sicherer**: Weniger Aktivität = geringeres Ban-Risiko  
3. **Realistischer**: Niemand postet wirklich JEDEN Tag
4. **Unregelmäßig**: Kein erkennbares Muster

## 🔧 Anpassung

In `auto_post_comment_bot.py`:
```python
'pause_day_chance': 0.55  # 55% Chance
```

Mögliche Werte:
- `0.30` = 30% Pausentage (aktiver)
- `0.50` = 50% Pausentage (ausgewogen)
- `0.55` = 55% Pausentage (AKTUELL)
- `0.70` = 70% Pausentage (sehr inaktiv)

## 📝 Logs

An Pausentagen siehst du:
```
😴 Heute ist ein Pausentag - Bot macht heute nichts
```

Der Bot checkt jeden Tag neu und entscheidet zufällig!