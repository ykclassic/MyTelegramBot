import streamlit as st

# MUST be the first streamlit command
st.set_page_config(
    page_title="My App Hub",
    page_icon="🚀",
    layout="wide"
)

# --- HIDE STREAMLIT STYLE (Optional but recommended) ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- MAIN CONTENT ---
st.title("Welcome to My Tool Suite")
st.write("---")

st.markdown("""
### 🛠 Available Applications
Choose a tool from the sidebar to begin. Here is a quick overview of what you'll find:
""")

# Creating a 3-column layout for a dashboard feel
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.info("#### 📈 ForgV1")
    st.write("Description of your first app. Great for data analysis or specific tasks.")

with col2:
    st.success("#### 🤖 Forgev2")
    st.write("Description of your second app. Powered by OpenAI/LLMs.")

with col3:
    st.success("#### 🤖 Forgev3")
    st.write("Description of your second app. Powered by OpenAI/LLMs.")

with col4:
    st.success("#### 🤖 Forgev4")
    st.write("Description of your second app. Powered by OpenAI/LLMs.")

st.write("---")
st.caption("Developed by TechSolute Empire | (c) TechSolute")
