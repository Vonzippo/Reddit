#!/usr/bin/env python3
"""
Inline Link Inserter - Fügt Links direkt IN den Text ein, wo sie kontextuell passen
"""

import json
import re
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class LinkInsertion:
    """Definiert wo und wie ein Link eingefügt wird"""
    position: int
    original_text: str
    replacement_text: str
    context_before: str
    context_after: str
    confidence: float

class InlineLinkInserter:
    def __init__(self, config_path="inline_link_config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
    def _load_config(self) -> dict:
        """Lädt die Link-Konfiguration"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self._create_default_config()
    
    def _create_default_config(self) -> dict:
        """Erstellt Standard-Konfiguration"""
        return {
            "inline_rules": [
                {
                    "name": "App Mentions",
                    "patterns": [
                        {
                            "match": r"(I use|I've been using|I tried) (an app|a tool|something)",
                            "replacement": "I use [this app]({url})",
                            "url": "https://example.com/app"
                        },
                        {
                            "match": r"(found|discovered) (an app|a tool) that",
                            "replacement": "found [an amazing app]({url}) that",
                            "url": "https://example.com/app"
                        },
                        {
                            "match": r"(timer|reminder|alarm) app",
                            "replacement": "[timer app]({url})",
                            "url": "https://example.com/timer"
                        }
                    ]
                },
                {
                    "name": "Method References",
                    "patterns": [
                        {
                            "match": r"(pomodoro|time blocking|timeboxing)",
                            "replacement": "[{original}]({url})",
                            "url": "https://example.com/method"
                        },
                        {
                            "match": r"this (technique|method|approach)",
                            "replacement": "[this {match_group}]({url})",
                            "url": "https://example.com/technique"
                        }
                    ]
                },
                {
                    "name": "Resource Mentions",
                    "patterns": [
                        {
                            "match": r"(helpful|useful) (resource|website|guide)",
                            "replacement": "[{match_group} resource]({url})",
                            "url": "https://example.com/resource"
                        },
                        {
                            "match": r"(read|found) (something|an article|a post) about",
                            "replacement": "read [an article]({url}) about",
                            "url": "https://example.com/article"
                        }
                    ]
                }
            ],
            "insertion_strategy": {
                "max_links_per_comment": 1,
                "prefer_early_insertion": False,
                "maintain_natural_flow": True,
                "avoid_breaking_sentences": True
            }
        }
    
    def find_insertion_points(self, content: str) -> List[LinkInsertion]:
        """Findet natürliche Stellen für Link-Einfügung"""
        insertions = []
        
        for rule in self.config.get('inline_rules', []):
            for pattern_config in rule.get('patterns', []):
                pattern = pattern_config['match']
                
                # Füge Wortgrenzen hinzu für bessere Matches
                if not pattern.startswith(r'\b'):
                    pattern = r'\b' + pattern
                if not pattern.endswith(r'\b'):
                    pattern = pattern + r'\b'
                
                # Finde alle Matches
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    # Kontext extrahieren
                    start = match.start()
                    end = match.end()
                    
                    # 50 Zeichen vor und nach dem Match für Kontext
                    context_before = content[max(0, start-50):start]
                    context_after = content[end:min(len(content), end+50)]
                    
                    # Erstelle Replacement
                    replacement = pattern_config['replacement']
                    url = pattern_config['url']
                    
                    # Ersetze Platzhalter
                    original_text = match.group(0)
                    if '{original}' in replacement:
                        replacement = replacement.replace('{original}', original_text)
                    if '{match_group}' in replacement and match.groups():
                        replacement = replacement.replace('{match_group}', match.group(1))
                    
                    replacement = replacement.replace('{url}', url)
                    
                    # Bewerte Konfidenz (wie gut passt es)
                    confidence = self._calculate_confidence(
                        context_before, 
                        context_after, 
                        original_text
                    )
                    
                    insertion = LinkInsertion(
                        position=start,
                        original_text=original_text,
                        replacement_text=replacement,
                        context_before=context_before,
                        context_after=context_after,
                        confidence=confidence
                    )
                    
                    insertions.append(insertion)
        
        # Sortiere nach Konfidenz
        insertions.sort(key=lambda x: x.confidence, reverse=True)
        return insertions
    
    def _calculate_confidence(self, before: str, after: str, text: str) -> float:
        """Berechnet wie gut eine Stelle für Link-Einfügung ist"""
        confidence = 0.5
        
        # Bonus wenn am Satzanfang oder nach Punkt
        if before.rstrip().endswith('.') or before.strip() == '':
            confidence += 0.2
        
        # Bonus wenn nicht mitten im Satz
        if '.' in after[:20] or '!' in after[:20] or '?' in after[:20]:
            confidence += 0.1
        
        # Penalty wenn in Klammern
        if '(' in before[-10:] and ')' not in after[:10]:
            confidence -= 0.3
        
        # Bonus für bestimmte Keywords
        positive_context = ['helpful', 'useful', 'great', 'amazing', 'recommend']
        if any(word in before.lower() + after.lower() for word in positive_context):
            confidence += 0.2
        
        return min(max(confidence, 0), 1)
    
    def apply_inline_links(self, content: str, max_links: int = 5) -> Tuple[str, List[Dict]]:
        """Fügt Links inline in den Content ein"""
        insertions = self.find_insertion_points(content)
        
        if not insertions:
            return content, []
        
        # Wähle beste Insertion(s)
        selected = insertions[:max_links]
        
        # Sortiere nach Position (rückwärts für korrektes Einfügen)
        selected.sort(key=lambda x: x.position, reverse=True)
        
        # Wende Änderungen an
        modified_content = content
        applied_links = []
        
        for insertion in selected:
            # Ersetze im Text
            before = modified_content[:insertion.position]
            after = modified_content[insertion.position + len(insertion.original_text):]
            modified_content = before + insertion.replacement_text + after
            
            # Log die Änderung
            applied_links.append({
                'original': insertion.original_text,
                'replacement': insertion.replacement_text,
                'position': insertion.position,
                'confidence': insertion.confidence
            })
        
        return modified_content, applied_links
    
    def process_comment(self, comment_path: Path) -> Optional[Dict]:
        """Verarbeitet einen einzelnen Kommentar"""
        json_path = comment_path / "comment_data.json"
        content_path = comment_path / "comment_content.txt"
        
        if not json_path.exists() or not content_path.exists():
            return None
        
        with open(content_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Finde und wende Links an
        modified_content, applied_links = self.apply_inline_links(content)
        
        if not applied_links:
            return None
        
        return {
            'path': comment_path,
            'original_content': content,
            'modified_content': modified_content,
            'applied_links': applied_links
        }
    
    def process_data_directories(self, output_base: Path = None):
        """Verarbeitet echte Daten aus data/ Verzeichnis"""
        data_dir = Path("data")
        if output_base is None:
            output_base = Path("data_with_links")
        
        output_base.mkdir(exist_ok=True)
        
        processed_total = 0
        modified_total = 0
        
        # Verarbeite Comments aus data/Comments/
        comments_dir = data_dir / "Comments"
        if comments_dir.exists():
            print(f"\n📁 Verarbeite COMMENTS aus {comments_dir}...")
            
            # Output-Verzeichnis erstellen
            output_comments = output_base / "Comments_with_links"
            output_comments.mkdir(exist_ok=True)
            
            # Verarbeite ALLE Kommentare
            for comment_dir in sorted(comments_dir.iterdir()):
                if not comment_dir.is_dir() or not comment_dir.name.startswith('comment_'):
                    continue
                
                processed_total += 1
                result = self.process_comment(comment_dir)
                
                if result and result['applied_links']:
                    modified_total += 1
                    
                    # Erstelle Output-Ordner
                    output_comment = output_comments / comment_dir.name
                    output_comment.mkdir(exist_ok=True)
                    
                    # Kopiere Original-Dateien
                    import shutil
                    for file in comment_dir.iterdir():
                        if file.name != 'comment_content.txt':
                            shutil.copy2(file, output_comment / file.name)
                    
                    # Schreibe modifizierten Content
                    with open(output_comment / 'comment_content.txt', 'w', encoding='utf-8') as f:
                        f.write(result['modified_content'])
                    
                    # Schreibe Link-Info
                    with open(output_comment / 'link_modifications.json', 'w', encoding='utf-8') as f:
                        json.dump({
                            'applied_links': result['applied_links'],
                            'original_path': str(comment_dir)
                        }, f, indent=2)
                    
                    print(f"    ✅ {comment_dir.name}: {len(result['applied_links'])} Link(s) eingefügt")
        
        print(f"\n📊 ZUSAMMENFASSUNG:")
        print(f"   Verarbeitet: {processed_total} Kommentare")
        print(f"   Modifiziert: {modified_total} Kommentare")
        print(f"   Output: {output_base}/")
        
        return processed_total, modified_total

def create_inline_config():
    """Erstellt eine bessere Inline-Konfiguration"""
    config = {
        "inline_rules": [
            {
                "name": "ADHD Apps",
                "patterns": [
                    {
                        "match": r"(use|using|tried) (an app|the app|this app)",
                        "replacement": "use [this ADHD app]({url})",
                        "url": "https://your-app.com"
                    },
                    {
                        "match": r"reminder app",
                        "replacement": "[reminder app]({url})",
                        "url": "https://your-reminder-app.com"
                    },
                    {
                        "match": r"timer for",
                        "replacement": "[timer]({url}) for",
                        "url": "https://your-timer.com"
                    }
                ]
            },
            {
                "name": "Methods",
                "patterns": [
                    {
                        "match": r"pomodoro technique",
                        "replacement": "[pomodoro technique]({url})",
                        "url": "https://pomodoro-guide.com"
                    },
                    {
                        "match": r"this (method|technique|strategy)",
                        "replacement": "[this {match_group}]({url})",
                        "url": "https://adhd-strategies.com"
                    }
                ]
            },
            {
                "name": "Resources",
                "patterns": [
                    {
                        "match": r"(article|guide|resource) about",
                        "replacement": "[{match_group}]({url}) about",
                        "url": "https://adhd-resource.com"
                    },
                    {
                        "match": r"helpful website",
                        "replacement": "[helpful website]({url})",
                        "url": "https://helpful-site.com"
                    }
                ]
            }
        ],
        "insertion_strategy": {
            "max_links_per_comment": 1,
            "min_confidence": 0.6,
            "preserve_readability": True
        },
        "target_comments": {
            "min_score": 500,
            "max_total_links": 10,
            "only_helpful_context": True
        }
    }
    
    config_path = Path("inline_link_config.json")
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Config erstellt: {config_path}")
    return config_path

def main():
    print("="*60)
    print("🔗 INLINE LINK INSERTER")
    print("   Fügt Links direkt IN den Text ein")
    print("="*60)
    
    # Erstelle Config wenn nicht vorhanden
    config_path = Path("inline_link_config.json")
    if not config_path.exists():
        print("\n📝 Erstelle Beispiel-Konfiguration...")
        create_inline_config()
        print("\n⚠️  Bitte bearbeite inline_link_config.json mit deinen URLs!")
        print("\nStarte das Script erneut nach der Konfiguration.")
        return
    
    inserter = InlineLinkInserter()
    
    print("\n🔍 Analysiere Kommentare für Link-Einfügung...")
    print("   Suche nach passenden Stellen in den Texten...")
    
    # Verarbeite echte Daten
    processed, modified = inserter.process_data_directories()
    
    if modified > 0:
        print("\n✅ ERFOLGREICH!")
        print(f"   {modified} Kommentare wurden mit Links versehen")
        print(f"   Output: data_with_links/")
        print("\n💡 Die modifizierten Kommentare sind bereit zum Posten")
    else:
        print("\n⚠️ Keine passenden Stellen für Links gefunden")
        print("   Überprüfe deine inline_link_config.json Patterns")

if __name__ == "__main__":
    main()