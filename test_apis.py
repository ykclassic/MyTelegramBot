# test_apis.py

import openai
import google.generativeai as genai

# Paste your keys here temporarily for testing
OPENAI_KEY = "sk-your-real-openai-key"
GEMINI_KEY = "your-real-gemini-key"

# Test OpenAI
print("Testing OpenAI...")
try:
    openai.api_key = OPENAI_KEY
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say 'OpenAI works!'"}],
        max_tokens=10
    )
    print("✅ OpenAI SUCCESS:", response.choices[0].message.content)
except Exception as e:
    print("❌ OpenAI FAILED:", str(e))

# Test Gemini
print("\nTesting Gemini...")
try:
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')  # or 'gemini-1.5-pro'
    response = model.generate_content("Say 'Gemini works!'")
    print("✅ Gemini SUCCESS:", response.text)
except Exception as e:
    print("❌ Gemini FAILED:", str(e))
