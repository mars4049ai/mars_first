import streamlit as st

st.title('Простой калькулятор')

num1 = st.text_input('Введите Вашу роль в семье:', step=1)
num2 = st.text_input('Введите свой вопрос:', step=1)

operation = st.selectbox('Выберите операцию:', ['Сложение', 'Вычитание', 'Умножение', 'Деление'])

result = 12


st.write(f'Результат операции {operation}: {result}')
