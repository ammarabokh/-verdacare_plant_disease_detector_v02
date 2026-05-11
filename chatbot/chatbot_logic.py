import json
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

    def process_message(self, message, session_id, lang='ar', context=None):
        """
        Process user message and generate response.

        Args:
            message: User's message text
            session_id: Session identifier for memory
            lang: Language code ('ar' or 'en')
            context: Optional context (e.g., last diagnosis)

        Returns:
            Response text
        """
        history = chat_memory.get_history(session_id)
        system_prompt = self._build_system_prompt(lang, context)

        # If user asks about treatment/symptoms/etc for the current diagnosis context,
        # answer directly from local KB to avoid unnecessary remote LLM calls.
        context_response = self._answer_from_context_if_relevant(message, lang, context)
        if context_response:
            chat_memory.add_message(session_id, 'user', message)
            chat_memory.add_message(session_id, 'assistant', context_response)
            return context_response

        kb_response = self._check_knowledge_base(message, lang)
        if kb_response:
            chat_memory.add_message(session_id, 'user', message)
            chat_memory.add_message(session_id, 'assistant', kb_response)
            return kb_response

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
            print(f"Error in chatbot processing: {e}")
            context_response = self._fallback_from_context(lang, context)
            if context_response:
                return context_response
            fallback = {
                'ar': 'تعذر الاتصال بخدمة الذكاء حالياً. يمكنك كتابة اسم المرض وسأعطيك المعلومات المتاحة من قاعدة المعرفة المحلية.',
                'en': 'LLM service is currently unavailable. You can type a disease name and I will answer from the local knowledge base.'
            }
            return fallback.get(lang, fallback['en'])

    def _build_system_prompt(self, lang, context=None):
        """Build system prompt for LLM."""
        base_prompts = {
            'ar': """أنت مساعد زراعي خبير. ساعد المزارعين في:
- تشخيص أمراض النباتات
- نصائح العلاج والوقاية
- الممارسات الزراعية الجيدة
- الإجابة على الأسئلة الزراعية

كن مختصرًا وعمليًا. أجب باللغة العربية.""",
            'en': """You are an expert agricultural assistant. Help farmers with:
- Plant disease diagnosis
- Treatment and prevention advice
- Good agricultural practices
- Answering farming questions

Be concise and practical. Answer in English."""
        }

        prompt = base_prompts.get(lang, base_prompts['en'])
        if context:
            prompt += f"\nContext: The user recently diagnosed their plant with: {context}"

        return prompt

    def _check_knowledge_base(self, message, lang):
        """
        Check if message matches knowledge base for quick answers.
        Returns response or None.
        """
        message_lower = message.lower()

        for _, disease_data in self.knowledge_base.items():
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
        message_lower = (message or "").lower()
        keywords = [
            "treatment", "prevention", "symptoms", "description", "what is",
            "علاج", "الوقاية", "وقاية", "اعراض", "أعراض", "وصف", "ما الحل", "ما هو"
        ]
        if not any(k in message_lower for k in keywords):
            return None
        return self._fallback_from_context(lang, context)


chatbot = ChatbotLogic()
