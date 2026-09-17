"""Run: python -m streamlit run app.py"""
import streamlit as st
from dashboard import main

if __name__ == '__main__':
    st.navigation([st.Page(main, title='ภาพรวมธุรกิจ', default=True)], position='hidden').run()
