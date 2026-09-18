"""Run: python -m streamlit run app.py"""
import streamlit as st
from dashboard import main
from dashboard import find_database
from warehouse_setup import prepare_warehouse

if __name__ == '__main__':
    try:
        find_database()
    except RuntimeError:
        with st.spinner('กำลังเตรียมฐานข้อมูลจาก CSV สำหรับการใช้งานครั้งแรก…'):
            try:
                prepare_warehouse(find_database)
            except Exception as error:
                st.error(str(error))
                st.stop()
    st.navigation([st.Page(main, title='ภาพรวมธุรกิจ', default=True)], position='hidden').run()
