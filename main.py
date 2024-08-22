import streamlit as st

number = st.number_input(
    "Insert a number", value=None, placeholder="Type a number..."
)
number1 = st.number_input(
    "Insert a number", value=None, placeholder="Type a number..."
)
st.write(number + number1)
