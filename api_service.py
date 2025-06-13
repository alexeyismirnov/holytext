import requests
import json
import streamlit as st
from typing import Dict, List, Optional

def call_openrouter_api(messages: List[Dict], model: str, api_key: str) -> Optional[str]:
    """Call OpenRouter API with the given messages and model"""
    if not api_key:
        st.error("❌ Please set your OpenRouter API key in the settings.")
        return None
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://streamlit.io",
        "X-Title": "Orthodox Translation Assistant"
    }
    
    data = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    try:
        with st.spinner("🤔 Thinking..."):
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    st.error("❌ No choices in API response")
                    return None
            else:
                st.error(f"❌ API Error: {response.status_code}")
                try:
                    error_data = response.json()
                    st.error(f"Error details: {error_data}")
                except:
                    st.error(f"Response text: {response.text}")
                return None
                
    except requests.exceptions.Timeout:
        st.error("⏰ Request timed out. Please try again.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("🌐 Connection error. Please check your internet connection.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"📡 Request failed: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        st.error(f"📄 JSON decode error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"💥 Unexpected error: {str(e)}")
        return None

def test_api_connection(api_key: str, model_id: str):
    """Test the API connection with a simple message"""
    if not api_key:
        st.error("❌ Please set your API key first")
        return
    
    test_messages = [{"role": "user", "content": "Hello, please respond with just 'API test successful'"}]
    
    st.write("🧪 Testing API connection...")
    response = call_openrouter_api(test_messages, model_id, api_key)
    
    if response:
        st.success(f"✅ API Test Successful! Response: {response}")
    else:
        st.error("❌ API Test Failed")