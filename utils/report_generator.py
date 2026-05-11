from flask import render_template_string
import json

# HTML template for the report
REPORT_TEMPLATE = """
<!DOCTYPE html>
<html lang="{{ lang }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #4CAF50, #8BC34A); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }
        .header h1 { margin: 0; font-size: 28px; }
        .confidence { font-size: 48px; font-weight: bold; text-align: center; margin: 20px 0; }
        .confidence.high { color: #4CAF50; }
        .confidence.medium { color: #FF9800; }
        .confidence.low { color: #F44336; }
        .section { background: #f9f9f9; padding: 20px; margin-bottom: 20px; border-radius: 8px; border-right: 4px solid #4CAF50; }
        .section h2 { color: #333; margin-top: 0; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }
        .section p { color: #555; font-size: 16px; }
        .products { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px; }
        .product-tag { background: #4CAF50; color: white; padding: 5px 15px; border-radius: 20px; font-size: 14px; }
        .footer { text-align: center; margin-top: 40px; padding: 20px; color: #888; font-size: 12px; }
        @media print {
            body { padding: 0; }
            .no-print { display: none; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ report_title }}</h1>
        <p>{{ diagnosis_date }}</p>
    </div>

    <div class="confidence {{ confidence_class }}">
        {{ confidence }}%
    </div>
    <p style="text-align: center; color: #666;">{{ confidence_text }}</p>

    <div class="section">
        <h2>{{ sections.name }}</h2>
        <p><strong>{{ disease_name }}</strong></p>
    </div>

    <div class="section">
        <h2>{{ sections.description }}</h2>
        <p>{{ description }}</p>
    </div>

    <div class="section">
        <h2>{{ sections.symptoms }}</h2>
        <p>{{ symptoms }}</p>
    </div>

    <div class="section">
        <h2>{{ sections.treatment }}</h2>
        <p>{{ treatment }}</p>
    </div>

    <div class="section">
        <h2>{{ sections.prevention }}</h2>
        <p>{{ prevention }}</p>
    </div>

    {% if products %}
    <div class="section">
        <h2>{{ sections.products }}</h2>
        <div class="products">
            {% for product in products %}
            <span class="product-tag">{{ product }}</span>
            {% endfor %}
        </div>
    </div>
    {% endif %}

    <div class="footer no-print">
        <p>{{ footer_text }}</p>
        <button onclick="window.print()" style="padding: 10px 30px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px;">
            {{ print_button }}
        </button>
    </div>
</body>
</html>
"""

def generate_report(disease_info, confidence, lang='ar'):
    """
    Generate HTML report for disease diagnosis.

    Args:
        disease_info: Dictionary with disease information
        confidence: Prediction confidence (0-1)
        lang: Language code ('ar' or 'en')

    Returns:
        HTML string
    """
    info = disease_info.get(lang, disease_info.get('en', {}))

    # Determine confidence class
    conf_percent = round(confidence * 100, 1)
    if conf_percent >= 80:
        conf_class = 'high'
        conf_text = 'High Confidence' if lang == 'en' else 'ثقة عالية'
    elif conf_percent >= 50:
        conf_class = 'medium'
        conf_text = 'Medium Confidence' if lang == 'en' else 'ثقة متوسطة'
    else:
        conf_class = 'low'
        conf_text = 'Low Confidence' if lang == 'en' else 'ثقة منخفضة'

    # Translations
    translations = {
        'ar': {
            'title': 'تقرير تشخيص مرض النبات',
            'report_title': 'تقرير التشخيص',
            'diagnosis_date': 'تاريخ التشخيص: ',
            'sections': {
                'name': 'اسم المرض',
                'description': 'الوصف',
                'symptoms': 'الأعراض',
                'treatment': 'العلاج',
                'prevention': 'الوقاية',
                'products': 'المنتجات الموصى بها'
            },
            'footer_text': 'تم إنشاء هذا التقرير بواسطة نظام اكتشاف أمراض النبات',
            'print_button': 'طباعة التقرير'
        },
        'en': {
            'title': 'Plant Disease Diagnosis Report',
            'report_title': 'Diagnosis Report',
            'diagnosis_date': 'Diagnosis Date: ',
            'sections': {
                'name': 'Disease Name',
                'description': 'Description',
                'symptoms': 'Symptoms',
                'treatment': 'Treatment',
                'prevention': 'Prevention',
                'products': 'Recommended Products'
            },
            'footer_text': 'This report was generated by the Plant Disease Detection System',
            'print_button': 'Print Report'
        }
    }

    t = translations.get(lang, translations['en'])

    from datetime import datetime

    return render_template_string(
        REPORT_TEMPLATE,
        lang=lang,
        title=t['title'],
        report_title=t['report_title'],
        diagnosis_date=t['diagnosis_date'] + datetime.now().strftime('%Y-%m-%d %H:%M'),
        confidence=conf_percent,
        confidence_class=conf_class,
        confidence_text=conf_text,
        sections=t['sections'],
        disease_name=info.get('name', 'Unknown'),
        description=info.get('description', 'No description available.'),
        symptoms=info.get('symptoms', 'No symptoms information available.'),
        treatment=info.get('treatment', 'No treatment information available.'),
        prevention=info.get('prevention', 'No prevention information available.'),
        products=info.get('products', []),
        footer_text=t['footer_text'],
        print_button=t['print_button']
    )
