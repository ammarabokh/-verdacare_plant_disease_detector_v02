import json
import re
from chatbot.huggingface_client import HuggingFaceClient
from chatbot.chat_memory import chat_memory
from config import Config


class ChatbotLogic:
    def __init__(self):
        self.hf_client = HuggingFaceClient()
        self.knowledge_base = self._load_knowledge_base()

    def _load_knowledge_base(self):
        """Load local knowledge base for quick answers."""
        try:
            with open(Config.KNOWLEDGE_BASE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('diseases', {})
        except Exception:
            return {}

    def process_message(self, message, session_id, lang='ar', context=None, user_name=None):
        """
        Process user message and generate response.

        Strategy:
          1. HuggingFace AI (primary) — natural conversation
          2. Knowledge base (fallback if AI fails)
          3. Context fallback (if KB has no match)
          4. Offline message (if all fail)

        Args:
            message: User's message text
            session_id: Session identifier for memory
            lang: Language code ('ar', 'en', or 'de')
            context: Optional context (e.g., last diagnosis name)
            user_name: Optional user's name for personalized responses

        Returns:
            Response text
        """
        history = chat_memory.get_history(session_id)
        system_prompt = self._build_system_prompt(lang, context, user_name)

        try:
            response = self.hf_client.generate_response(
                prompt=message,
                history=history,
                system_prompt=system_prompt
            )
            chat_memory.add_message(session_id, 'user', message)
            chat_memory.add_message(session_id, 'assistant', response)
            return response
        except Exception as e:
            print(f"AI unavailable: {e}")

        # Fallback 1: knowledge base keyword match
        kb_response = self._check_knowledge_base(message, lang)
        if kb_response:
            chat_memory.add_message(session_id, 'user', message)
            chat_memory.add_message(session_id, 'assistant', kb_response)
            return kb_response

        # Fallback 2: context-based (last diagnosis)
        ctx_response = self._fallback_from_context(lang, context)
        if ctx_response:
            chat_memory.add_message(session_id, 'user', message)
            chat_memory.add_message(session_id, 'assistant', ctx_response)
            return ctx_response

        # Fallback 3: offline message
        chat_memory.add_message(session_id, 'user', message)
        fallback = {
            'ar': 'تعذر الاتصال بخدمة الذكاء الاصطناعي حالياً. يرجى المحاولة لاحقاً.',
            'en': 'AI service is currently unavailable. Please try again later.',
            'de': 'Der KI-Dienst ist derzeit nicht verfügbar. Bitte versuchen Sie es später erneut.'
        }
        fb = fallback.get(lang, fallback['en'])
        chat_memory.add_message(session_id, 'assistant', fb)
        return fb

    def _build_system_prompt(self, lang, context=None, user_name=None):
        """Build system prompt for LLM."""
        base_prompts = {
            'ar': """أنت مساعد زراعي خبير ومتخصص في أمراض النبات. مهمتك مساعدة المزارعين ومحبي النباتات.

تعليمات مهمة:
- تحدث بشكل طبيعي ومحادثة وليس بطريقة تقريرية
- استخدم لغة واضحة وبسيطة
- خاطب المستخدم باسمه إذا كان معروفاً
- إذا سألك المستخدم عن معلومات محددة عن مرض (أعراض، علاج، وقاية) فقدمها بالتفصيل
- إذا سأل سؤالاً عاماً عن الزراعة، فأجب بناءً على معرفتك
- كن مفيداً ودقيقاً ولا تتخيل معلومات غير مؤكدة
- أجب باللغة العربية دائماً""",
            'en': """You are an expert agricultural assistant specializing in plant diseases. Your role is to help farmers and plant enthusiasts.

Important guidelines:
- Speak naturally and conversationally, not in a report style
- Use clear, simple language
- Address the user by their name if known
- If the user asks about specific disease information (symptoms, treatment, prevention), provide detailed answers
- If they ask general farming questions, answer based on your knowledge
- Be helpful, accurate, and do not make up unverified information
- Always answer in English""",
            'de': """Sie sind ein erfahrener landwirtschaftlicher Assistent, spezialisiert auf Pflanzenkrankheiten. Ihre Aufgabe ist es, Landwirten und Pflanzenliebhabern zu helfen.

Wichtige Richtlinien:
- Sprechen Sie natürlich und konversationell, nicht in Berichtsform
- Verwenden Sie klare, einfache Sprache
- Sprechen Sie den Benutzer mit seinem Namen an, falls bekannt
- Wenn der Benutzer nach spezifischen Krankheitsinformationen fragt (Symptome, Behandlung, Prävention), geben Sie detaillierte Antworten
- Bei allgemeinen landwirtschaftlichen Fragen antworten Sie basierend auf Ihrem Wissen
- Seien Sie hilfreich, genau, und erfinden Sie keine unbestätigten Informationen
- Antworten Sie immer auf Deutsch"""
        }

        prompt = base_prompts.get(lang, base_prompts['en'])
        if user_name:
            prompt += f"\n\nThe user's name is: {user_name}. Address them by their name naturally."
        if context:
            prompt += f"\n\nContext: The user has just diagnosed their plant with: {context}. Use this information naturally when answering related questions."

        return prompt

    def _check_knowledge_base(self, message, lang):
        """
        Check if message matches knowledge base for quick answers.
        Returns response or None.
        """
        message_lower = (message or '').lower()
        hinted_crop = self._extract_crop_hint(message_lower)

        for disease_key, disease_data in self.knowledge_base.items():
            if hinted_crop and not disease_key.lower().startswith(hinted_crop + '___'):
                continue

            info = disease_data.get(lang, disease_data.get('en', {}))
            disease_name = info.get('name', '').lower()
            if disease_name and disease_name in message_lower:
                return self._format_disease_info(info, lang)

        return None

    def _format_disease_info(self, info, lang):
        """Format disease information for chat response."""
        products = ', '.join(info.get('products', []))

        if lang == 'ar':
            return f"""**{info.get('name', '')}**

الوصف: {info.get('description', '')}
الأعراض: {info.get('symptoms', '')}
العلاج: {info.get('treatment', '')}
الوقاية: {info.get('prevention', '')}
المنتجات الموصى بها: {products}"""
        elif lang == 'de':
            return f"""**{info.get('name', '')}**

Beschreibung: {info.get('description', '')}
Symptome: {info.get('symptoms', '')}
Behandlung: {info.get('treatment', '')}
Pravention: {info.get('prevention', '')}
Empfohlene Produkte: {products}"""
        else:
            return f"""**{info.get('name', '')}**

Description: {info.get('description', '')}
Symptoms: {info.get('symptoms', '')}
Treatment: {info.get('treatment', '')}
Prevention: {info.get('prevention', '')}
Recommended Products: {products}"""

    def clear_conversation(self, session_id):
        """Clear conversation history."""
        chat_memory.clear_history(session_id)

    def _fallback_from_context(self, lang, context):
        """Return a local KB response when remote LLM is unavailable."""
        if not context:
            return None
        context_lower = context.lower()
        for _, disease_data in self.knowledge_base.items():
            info = disease_data.get(lang, disease_data.get('en', {}))
            disease_name = info.get('name', '').lower()
            if disease_name and disease_name in context_lower:
                return self._format_disease_info(info, lang)
        return None

    def _answer_from_context_if_relevant(self, message, lang, context):
        """Answer from current diagnosis context for common care questions."""
        if not context:
            return None

        message_lower = (message or '').lower()

        # Prevent stale context answers if user explicitly switched crop.
        message_crop = self._extract_crop_hint(message_lower)
        context_crop = self._extract_crop_hint((context or '').lower())
        if message_crop and context_crop and message_crop != context_crop:
            return None

        # Use diagnosis context only when user clearly refers to the previous case.
        # This avoids unrelated fallback answers (e.g., grape info while asking about pepper).
        reference_markers = [
            'this disease', 'that disease', 'same disease', 'this case', 'that case', 'it',
            'هذا المرض', 'هذه الحالة', 'نفس المرض', 'نفس الحالة', 'المرض هذا', 'الحالة هذه',
            'diese krankheit', 'dieser fall', 'gleiche krankheit'
        ]
        refers_to_context = any(m in message_lower for m in reference_markers)
        if context_crop and message_crop == context_crop:
            refers_to_context = True
        if not refers_to_context:
            return None

        keywords = [
            'treatment', 'prevention', 'symptoms', 'description', 'what is',
            'علاج', 'الوقاية', 'وقاية', 'اعراض', 'أعراض', 'وصف', 'ما الحل', 'ما هو', 'اشرح',
            'behandlung', 'pravention', 'symptome', 'beschreibung', 'was ist'
        ]
        if not any(k in message_lower for k in keywords):
            return None

        return self._fallback_from_context(lang, context)

    def _extract_crop_hint(self, text):
        """Extract normalized crop token from Arabic/English/German hints."""
        if not text:
            return None

        aliases = {
            'apple': ['apple', 'تفاح', 'apfel'],
            'blueberry': ['blueberry', 'توت ازرق', 'heidelbeere'],
            'cherry': ['cherry', 'كرز', 'kirsche'],
            'corn': ['corn', 'maize', 'ذرة', 'mais'],
            'grape': ['grape', 'عنب', 'traube'],
            'orange': ['orange', 'برتقال'],
            'peach': ['peach', 'خوخ', 'pfirsich'],
            'pepper': ['pepper', 'bell pepper', 'فلفل', 'paprika'],
            'potato': ['potato', 'بطاطس', 'بطاطا', 'kartoffel'],
            'raspberry': ['raspberry', 'توت العليق', 'himbeere'],
            'soybean': ['soybean', 'soy bean', 'فول الصويا', 'sojabohne'],
            'squash': ['squash', 'قرع', 'kurbis', 'kuerbis'],
            'strawberry': ['strawberry', 'فراولة', 'erdbeere'],
            'tomato': ['tomato', 'طماطم', 'بندورة', 'tomate'],
        }

        for crop, keys in aliases.items():
            for key in keys:
                if re.search(rf"\b{re.escape(key)}\b", text):
                    return crop

        return None


chatbot = ChatbotLogic()
