"""
Script to translate knowledge_base.json to German using deep-translator
Run this once to add German translations to all diseases
"""

import json
import time
from deep_translator import GoogleTranslator

def translate_text(text, target_lang='de'):
    """Translate text to target language"""
    try:
        translator = GoogleTranslator(source='en', target=target_lang)
        return translator.translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def translate_knowledge_base():
    """Add German translations to knowledge_base.json"""
    
    print("Loading knowledge_base.json...")
    with open('chatbot/knowledge_base.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    diseases = data.get('diseases', {})
    total = len(diseases)
    
    print(f"Found {total} diseases to translate...")
    
    for idx, (disease_key, disease_data) in enumerate(diseases.items(), 1):
        print(f"\n[{idx}/{total}] Translating: {disease_key}")
        
        if 'de' in disease_data:
            print("  → German translation already exists, skipping...")
            continue
        
        en_data = disease_data.get('en', {})
        
        if not en_data:
            print("  → No English data found, skipping...")
            continue
        
        de_data = {}
        
        fields = ['name', 'description', 'symptoms', 'treatment', 'prevention']
        
        for field in fields:
            if field in en_data:
                print(f"  → Translating {field}...")
                de_data[field] = translate_text(en_data[field], 'de')
                time.sleep(0.5)
        
        if 'products' in en_data:
            de_data['products'] = []
            for product in en_data['products']:
                translated_product = translate_text(product, 'de')
                de_data['products'].append(translated_product)
                time.sleep(0.3)
        
        disease_data['de'] = de_data
        print(f"  ✓ Completed: {de_data.get('name', 'Unknown')}")
    
    print("\n\nSaving updated knowledge_base.json...")
    with open('chatbot/knowledge_base.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("✓ Translation complete!")
    print(f"Total diseases translated: {total}")

if __name__ == '__main__':
    print("=" * 60)
    print("VerdaCare - Knowledge Base German Translation")
    print("=" * 60)
    translate_knowledge_base()
