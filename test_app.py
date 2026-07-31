import streamlit as st

st.set_page_config(page_title="Test", layout="wide")
st.title("✅ Streamlit Working!")
st.write("If you can see this, Streamlit is installed correctly!")

if st.button("Click me"):
    st.balloons()
    st.success("🎉 Success!")
