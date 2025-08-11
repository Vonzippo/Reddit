# Was ist in den Reddit-Daten enthalten?

## Dateiformat
- **RC_2024-12.zst**: Komprimierte Datei mit ALLEN Reddit-Kommentaren vom Dezember 2024
- Nach Dekompression: JSONL Format (eine JSON-Zeile pro Kommentar)
- Nach Filterung: Nur Kommentare aus deinen 20 Subreddits

## Beispiel eines Reddit-Kommentars (JSON)

```json
{
  "id": "abc123",
  "author": "reddit_username",
  "subreddit": "ADHD",
  "body": "I've found that using timers really helps me stay focused. I set 25-minute work sessions with 5-minute breaks. The Pomodoro technique has been a game changer for my ADHD!",
  "created_utc": 1703001234,
  "score": 42,
  "permalink": "/r/ADHD/comments/xyz789/what_helps_you_focus/abc123/",
  "link_id": "t3_xyz789",
  "parent_id": "t1_def456",
  "gilded": 0,
  "distinguished": null,
  "edited": false,
  "controversiality": 0,
  "retrieved_on": 1703001500,
  "author_flair_text": "ADHD-PI",
  "stickied": false,
  "is_submitter": false,
  "subreddit_id": "t5_2qh61"
}
```

## Wichtige Felder erklärt

### Identifikation
- **id**: Eindeutige Kommentar-ID
- **author**: Username des Verfassers (kann "[deleted]" sein)
- **subreddit**: Name des Subreddits (z.B. "ADHD", "anxiety")

### Inhalt
- **body**: Der eigentliche Kommentartext (kann "[removed]" oder "[deleted]" sein)
- **score**: Upvotes minus Downvotes
- **edited**: Ob der Kommentar bearbeitet wurde (false oder Timestamp)

### Kontext
- **link_id**: ID des Original-Posts (beginnt mit "t3_")
- **parent_id**: ID worauf geantwortet wurde
  - "t3_xxx" = Antwort auf den Post selbst
  - "t1_xxx" = Antwort auf einen anderen Kommentar
- **permalink**: Direktlink zum Kommentar auf Reddit

### Zeitstempel
- **created_utc**: Unix-Timestamp wann erstellt (Sekunden seit 1970)
- **retrieved_on**: Wann die Daten gesammelt wurden

### Zusatzinfo
- **author_flair_text**: User-Flair im Subreddit (z.B. "ADHD-PI", "Diagnosed")
- **gilded**: Anzahl der Reddit Gold/Awards
- **distinguished**: Ob Moderator/Admin-Kommentar
- **stickied**: Ob angepinnt
- **is_submitter**: Ob vom Original-Poster (OP)
- **controversiality**: 1 wenn kontrovers (viele Up- und Downvotes)

## Beispiele aus deinen Subreddits

### r/ADHD Kommentar
```json
{
  "author": "focusing_struggles",
  "subreddit": "ADHD",
  "body": "Does anyone else struggle with executive dysfunction? I know exactly what I need to do but I just... can't start. It's like there's an invisible wall.",
  "score": 156,
  "author_flair_text": "ADHD-C"
}
```

### r/anxiety Kommentar
```json
{
  "author": "calm_seeker",
  "subreddit": "Anxiety",
  "body": "Box breathing (4-4-4-4) has really helped me during panic attacks. Inhale 4, hold 4, exhale 4, hold 4. Simple but effective.",
  "score": 89,
  "author_flair_text": "GAD"
}
```

### r/productivity Kommentar
```json
{
  "author": "task_master",
  "subreddit": "productivity",
  "body": "My game changer: Time blocking. I assign specific hours to specific tasks. No more endless to-do lists, just 'at 2pm I work on project X'.",
  "score": 234
}
```

## Statistiken (geschätzt für Dezember 2024)

### Vor Filterung (alle Reddit)
- **Dateigröße**: ~15-20 GB komprimiert
- **Kommentare**: ~150-200 Millionen
- **Subreddits**: ~150.000+

### Nach Filterung (deine 20 Subreddits)
- **Dateigröße**: ~100-150 MB
- **Kommentare**: ~100.000-200.000
- **Subreddits**: Nur deine 20

## Typische Inhalte in deinen Subreddits

### ADHD-Subreddits
- Tipps für Fokus und Organisation
- Medikamenten-Erfahrungen (Ritalin, Adderall, etc.)
- Alltags-Strategien
- Diagnose-Geschichten
- Beziehungs-Herausforderungen

### Mental Health Subreddits
- Coping-Strategien
- Therapie-Erfahrungen
- Meditations-Techniken
- Support und Ermutigung
- Krisen-Bewältigung

### Productivity Subreddits
- Tool-Empfehlungen (Apps, Software)
- Zeitmanagement-Methoden
- Habit-Tracking
- Work-Life-Balance
- Study-Techniken

## Was kannst du damit machen?

1. **Analyse**: Häufige Themen und Probleme verstehen
2. **Bot-Training**: Realistische Kommentare generieren
3. **Sentiment-Analyse**: Stimmungen in Communities verstehen
4. **Keyword-Extraction**: Wichtige Begriffe und Trends finden
5. **Support-Patterns**: Wie helfen sich Menschen gegenseitig?

## Wichtige Hinweise

- **Gelöschte Inhalte**: Viele Kommentare zeigen "[deleted]" oder "[removed]"
- **Privatsphäre**: Usernames sind öffentlich, aber sei respektvoll
- **Kontext**: Ohne den Original-Post fehlt oft Kontext
- **Zeitlich**: Daten sind Snapshots, nicht live

## Nächste Schritte nach Download

1. **Durchsuchen**: 
   ```bash
   # Zeige erste 5 Kommentare
   head -5 pushshift_dumps/2024_filtered/RC_2024-12_filtered.jsonl | jq .
   ```

2. **Statistiken**:
   ```bash
   # Zähle Kommentare pro Subreddit
   cat RC_2024-12_filtered.jsonl | jq -r .subreddit | sort | uniq -c | sort -rn
   ```

3. **Bot-Training**: Die Daten können für Markov-Chains oder andere Textgenerierung verwendet werden