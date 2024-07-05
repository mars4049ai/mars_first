import streamlit as st

st.title('Простой калькулятор')

num1 = st.number_input('Введите первое число:', step=1)
num2 = st.number_input('Введите второе число:', step=1)

operation = st.selectbox('Выберите операцию:', ['Сложение', 'Вычитание', 'Умножение', 'Деление'])

result = 0

if operation == 'Сложение':
    result = num1 + num2
elif operation == 'Вычитание':
    result = num1 - num2
elif operation == 'Умножение':
    result = num1 * num2
elif operation == 'Деление':
    if num2 != 0:
        result = num1 / num2
    else:
        st.error('На ноль делить нельзя!')

st.write(f'Результат операции {operation}: {result}')
