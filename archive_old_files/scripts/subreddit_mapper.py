#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Subreddit Mapper - Findet ähnliche/alternative Subreddits für Top Posts
Mappt jeden Top Post zu einem gut durchlaufenen, ähnlichen Subreddit
"""

import json
from pathlib import Path
import random

class SubredditMapper:
    def __init__(self):
        # Definiere Subreddit-Kategorien und deren Alternativen
        # Nur aktive Subreddits mit gutem Traffic
        self.subreddit_categories = {
            'technology': {
                'main': ['technology', 'tech', 'gadgets', 'programming', 'coding'],
                'alternatives': [
                    'technews', 'technologynews', 'futurology', 'geek',
                    'hardware', 'software', 'techsupport', 'buildapc',
                    'pcmasterrace', 'android', 'apple', 'linux'
                ]
            },
            'gaming': {
                'main': ['gaming', 'games', 'pcgaming', 'nintendo', 'playstation', 'xbox'],
                'alternatives': [
                    'truegaming', 'gamernews', 'indiegaming', 'retrogaming',
                    'gamingsuggestions', 'gamingcirclejerk', 'patientgamers',
                    'gaming4gamers', 'casualgaming', 'mobilegaming'
                ]
            },
            'funny_memes': {
                'main': ['funny', 'memes', 'dankmemes', 'wholesomememes', 'me_irl'],
                'alternatives': [
                    'meme', 'meirl', 'comedyheaven', 'okbuddyretard',
                    'shitposting', 'antimeme', 'bonehurtingjuice',
                    'comedycemetery', 'terriblefacebookmemes', 'ComedyNecrophilia'
                ]
            },
            'pics_gifs': {
                'main': ['pics', 'gifs', 'videos', 'BeAmazed', 'oddlysatisfying'],
                'alternatives': [
                    'images', 'pic', 'pictures', 'PhotoshopBattles',
                    'nocontextpics', 'itookapicture', 'perfecttiming',
                    'AccidentalRenaissance', 'mildlyinteresting', 'interestingasfuck'
                ]
            },
            'worldnews_politics': {
                'main': ['worldnews', 'news', 'politics', 'Conservative', 'europe'],
                'alternatives': [
                    'neutralnews', 'qualitynews', 'geopolitics', 'anime_titties',
                    'TrueReddit', 'moderatepolitics', 'politicaldiscussion',
                    'neutralpolitics', 'ukpolitics', 'canadapolitics'
                ]
            },
            'askreddit_discussion': {
                'main': ['AskReddit', 'NoStupidQuestions', 'TooAfraidToAsk', 'ask'],
                'alternatives': [
                    'AskAnAmerican', 'AskEurope', 'AskUK', 'AskWomen', 'AskMen',
                    'casualconversation', 'seriousconversation', 'self',
                    'discussion', 'changemyview', 'unpopularopinion'
                ]
            },
            'science_education': {
                'main': ['science', 'askscience', 'ELI5', 'todayilearned', 'space'],
                'alternatives': [
                    'everythingscience', 'sciences', 'physics', 'chemistry',
                    'biology', 'astronomy', 'geology', 'psychology',
                    'neuroscience', 'dataisbeautiful', 'educationalgifs'
                ]
            },
            'lifestyle_advice': {
                'main': ['LifeProTips', 'GetMotivated', 'selfimprovement', 'getdisciplined'],
                'alternatives': [
                    'decidingtobebetter', 'productivity', 'zenhabits',
                    'simpleliving', 'minimalism', 'frugal', 'personalfinance',
                    'findapath', 'iwanttolearn', 'howto'
                ]
            },
            'relationships': {
                'main': ['relationships', 'relationship_advice', 'dating_advice'],
                'alternatives': [
                    'dating', 'love', 'marriage', 'LongDistance',
                    'RelationshipsOver35', 'datingoverthirty', 'datingoverforty',
                    'healthyrelationships', 'relationship_tips', 'couples'
                ]
            },
            'stories_text': {
                'main': ['tifu', 'AmItheAsshole', 'offmychest', 'TrueOffMyChest'],
                'alternatives': [
                    'confession', 'confessions', 'self', 'rant', 'venting',
                    'unsentletters', 'letters', 'storytelling', 'shortstories',
                    'nosleep', 'LetsNotMeet', 'Glitch_in_the_Matrix'
                ]
            },
            'hobbies_interests': {
                'main': ['DIY', 'crafts', 'art', 'photography', 'music'],
                'alternatives': [
                    'somethingimade', 'crafting', 'handmade', 'maker',
                    'woodworking', 'metalworking', 'leathercraft', 'sewing',
                    'drawing', 'painting', 'digitalart', 'design'
                ]
            },
            'food_cooking': {
                'main': ['food', 'cooking', 'FoodPorn', 'recipes'],
                'alternatives': [
                    'cookingforbeginners', 'eatcheapandhealthy', 'mealprep',
                    'baking', 'breadit', 'pizza', 'bbq', 'vegetarian',
                    'vegan', 'ketorecipes', 'slowcooking', 'instantpot'
                ]
            },
            'fitness_health': {
                'main': ['Fitness', 'gym', 'bodybuilding', 'health'],
                'alternatives': [
                    'gainit', 'loseit', 'progresspics', 'workout',
                    'homegym', 'running', 'cycling', 'yoga', 'flexibility',
                    'nutrition', 'supplements', 'strongman'
                ]
            },
            'mental_health': {
                'main': ['mentalhealth', 'depression', 'anxiety', 'ADHD'],
                'alternatives': [
                    'getting_over_it', 'socialanxiety', 'depression_help',
                    'anxietyhelp', 'panicattack', 'therapy', 'traumatoolbox',
                    'adhdmeme', 'adhd_anxiety', 'neurodiversity'
                ]
            },
            'entertainment': {
                'main': ['movies', 'television', 'netflix', 'anime', 'manga'],
                'alternatives': [
                    'flicks', 'cinema', 'moviesuggestions', 'televisionsuggestions',
                    'bingewatch', 'cordcutters', 'streaming', 'hulu',
                    'amazonprime', 'disneyplus', 'hbomax', 'criterion'
                ]
            },
            'sports': {
                'main': ['sports', 'nba', 'nfl', 'soccer', 'baseball'],
                'alternatives': [
                    'sportsbook', 'fantasyfootball', 'fantasybball',
                    'sportsbetting', 'mma', 'boxing', 'tennis', 'golf',
                    'formula1', 'nascar', 'hockey', 'cricket'
                ]
            },
            'finance_crypto': {
                'main': ['wallstreetbets', 'stocks', 'investing', 'cryptocurrency'],
                'alternatives': [
                    'stockmarket', 'daytrading', 'options', 'forex',
                    'algotrading', 'dividends', 'bogleheads', 'fire',
                    'bitcoin', 'ethereum', 'altcoin', 'defi'
                ]
            },
            'animals_nature': {
                'main': ['aww', 'AnimalsBeingBros', 'NatureIsFuckingLit', 'EarthPorn'],
                'alternatives': [
                    'cats', 'dogs', 'pets', 'animalpics', 'wildlifephotography',
                    'birding', 'cute', 'eyebleach', 'animalsbeingjerks',
                    'animalsbeingderps', 'rarepuppers', 'IllegallySmolCats'
                ]
            }
        }
        
        # Erstelle Reverse-Mapping für schnelle Suche
        self.subreddit_to_category = {}
        for category, data in self.subreddit_categories.items():
            for sub in data['main'] + data['alternatives']:
                self.subreddit_to_category[sub.lower()] = category
    
    def find_similar_subreddit(self, original_subreddit, exclude_original=True):
        """Findet einen ähnlichen Subreddit basierend auf Kategorie"""
        original_lower = original_subreddit.lower()
        
        # Finde Kategorie des Original-Subreddits
        category = self.subreddit_to_category.get(original_lower)
        
        if category:
            # Subreddit ist in unserer Datenbank
            all_alternatives = (
                self.subreddit_categories[category]['main'] + 
                self.subreddit_categories[category]['alternatives']
            )
            
            # Filtere Original raus wenn gewünscht
            if exclude_original:
                all_alternatives = [s for s in all_alternatives if s.lower() != original_lower]
            
            # Wähle zufällig einen alternativen Subreddit
            if all_alternatives:
                return random.choice(all_alternatives)
        
        # Fallback: Versuche ähnliche Kategorien zu finden
        return self.find_fallback_subreddit(original_subreddit)
    
    def find_fallback_subreddit(self, original_subreddit):
        """Fallback-Strategie für unbekannte Subreddits"""
        original_lower = original_subreddit.lower()
        
        # Keyword-basierte Zuordnung
        keyword_mappings = {
            'meme': 'funny_memes',
            'porn': 'pics_gifs',  # SFW Alternativen für "porn" suffix (FoodPorn etc.)
            'circle': 'funny_memes',
            'jerk': 'funny_memes',
            'ask': 'askreddit_discussion',
            'true': 'askreddit_discussion',
            'casual': 'askreddit_discussion',
            'shit': 'funny_memes',
            'best': 'pics_gifs',
            'cool': 'pics_gifs',
            'interesting': 'pics_gifs',
            'beautiful': 'pics_gifs',
            'amazing': 'pics_gifs'
        }
        
        # Suche nach Keywords im Namen
        for keyword, category in keyword_mappings.items():
            if keyword in original_lower:
                alternatives = (
                    self.subreddit_categories[category]['main'] + 
                    self.subreddit_categories[category]['alternatives']
                )
                return random.choice(alternatives)
        
        # Ultimate Fallback: Große, allgemeine Subreddits
        general_subs = [
            'AskReddit', 'pics', 'funny', 'mildlyinteresting',
            'todayilearned', 'videos', 'gifs', 'worldnews',
            'gaming', 'movies', 'television', 'music'
        ]
        return random.choice(general_subs)
    
    def map_posts_to_alternatives(self, posts_file):
        """Mappt alle Posts aus einer Datei zu alternativen Subreddits"""
        input_path = Path(posts_file)
        if not input_path.exists():
            print(f"❌ Datei nicht gefunden: {input_path}")
            return
        
        output_path = input_path.parent / f"{input_path.stem}_mapped.jsonl"
        stats_path = input_path.parent / f"{input_path.stem}_mapping_stats.json"
        
        print(f"📂 Lese Posts aus: {input_path}")
        
        posts = []
        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    posts.append(json.loads(line))
        
        print(f"✅ {len(posts)} Posts geladen")
        
        # Mapping durchführen
        mapping_stats = {}
        mapped_posts = []
        
        for post in posts:
            original_sub = post.get('subreddit', 'unknown')
            
            # Finde Alternative
            alternative_sub = self.find_similar_subreddit(original_sub)
            
            # Erstelle gemappten Post
            mapped_post = post.copy()
            mapped_post['original_subreddit'] = original_sub
            mapped_post['target_subreddit'] = alternative_sub
            mapped_post['mapping_strategy'] = 'category' if original_sub.lower() in self.subreddit_to_category else 'fallback'
            
            mapped_posts.append(mapped_post)
            
            # Statistiken
            if original_sub not in mapping_stats:
                mapping_stats[original_sub] = {}
            if alternative_sub not in mapping_stats[original_sub]:
                mapping_stats[original_sub][alternative_sub] = 0
            mapping_stats[original_sub][alternative_sub] += 1
        
        # Speichere gemappte Posts
        with open(output_path, 'w', encoding='utf-8') as f:
            for post in mapped_posts:
                f.write(json.dumps(post, ensure_ascii=False) + '\n')
        
        print(f"✅ Gemappte Posts gespeichert: {output_path}")
        
        # Speichere Statistiken
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(mapping_stats, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Mapping-Statistiken: {stats_path}")
        
        # Zeige Zusammenfassung
        print("\n📊 MAPPING ZUSAMMENFASSUNG:")
        print(f"Posts gemappt: {len(mapped_posts)}")
        print(f"Unique Original Subreddits: {len(mapping_stats)}")
        
        # Top Mappings
        print("\n🔄 Top 10 Mapping-Paare:")
        all_mappings = []
        for orig, targets in mapping_stats.items():
            for target, count in targets.items():
                all_mappings.append((orig, target, count))
        
        all_mappings.sort(key=lambda x: x[2], reverse=True)
        for orig, target, count in all_mappings[:10]:
            print(f"  r/{orig} → r/{target}: {count} Posts")
        
        return mapped_posts
    
    def generate_posting_schedule(self, mapped_posts, posts_per_day=10):
        """Erstellt einen Posting-Zeitplan mit verteilten Subreddits"""
        from datetime import datetime, timedelta
        
        # Gruppiere Posts nach Target-Subreddit
        by_subreddit = {}
        for post in mapped_posts:
            target = post['target_subreddit']
            if target not in by_subreddit:
                by_subreddit[target] = []
            by_subreddit[target].append(post)
        
        # Erstelle Schedule
        schedule = []
        current_date = datetime.now()
        day_counter = 0
        
        while mapped_posts:
            daily_posts = []
            used_subs = set()
            
            # Versuche verschiedene Subreddits pro Tag zu verwenden
            for _ in range(posts_per_day):
                # Finde Subreddit der noch nicht heute verwendet wurde
                for sub in by_subreddit:
                    if sub not in used_subs and by_subreddit[sub]:
                        post = by_subreddit[sub].pop(0)
                        post['scheduled_date'] = (current_date + timedelta(days=day_counter)).strftime('%Y-%m-%d')
                        daily_posts.append(post)
                        used_subs.add(sub)
                        mapped_posts.remove(post)
                        break
                
                if len(daily_posts) >= posts_per_day:
                    break
            
            if daily_posts:
                schedule.extend(daily_posts)
                day_counter += 1
            else:
                break
        
        # Speichere Schedule
        schedule_path = Path("/Users/patrick/Desktop/Reddit/data_all/posting_schedule.json")
        with open(schedule_path, 'w', encoding='utf-8') as f:
            json.dump(schedule, f, indent=2, ensure_ascii=False)
        
        print(f"\n📅 Posting-Schedule erstellt: {schedule_path}")
        print(f"   Tage geplant: {day_counter}")
        print(f"   Posts geplant: {len(schedule)}")
        
        return schedule

def main():
    mapper = SubredditMapper()
    
    print("🔄 SUBREDDIT MAPPER")
    print("="*60)
    
    # Warte auf Top 1000 Posts Datei
    posts_file = Path("/Users/patrick/Desktop/Reddit/data_all/top_1000_november_posts.jsonl")
    
    if posts_file.exists():
        print("✅ Top 1000 Posts gefunden!")
        
        # Mappe Posts zu alternativen Subreddits
        mapped = mapper.map_posts_to_alternatives(posts_file)
        
        # Erstelle Posting-Schedule
        if mapped:
            mapper.generate_posting_schedule(mapped, posts_per_day=10)
        
    else:
        print("⏳ Warte auf top_1000_november_posts.jsonl...")
        print("\nBeispiel-Mappings:")
        
        # Zeige Beispiele
        examples = [
            'funny', 'AskReddit', 'gaming', 'worldnews', 'pics',
            'technology', 'ADHD', 'relationship_advice', 'tifu'
        ]
        
        for sub in examples:
            alt = mapper.find_similar_subreddit(sub)
            print(f"  r/{sub} → r/{alt}")

if __name__ == "__main__":
    main()