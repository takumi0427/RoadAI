#%%
# https://blog.amedama.jp/entry/streamlit-tutorial
# https://qiita.com/guunonemodemai/items/1b9ffd8702d4e01075dd
# https://sakizo-blog.com/524/
import streamlit as st

st.set_page_config(layout="wide")

st.header('RoadAI by Asada Laboratory')
st.text("RoadAI")
# source venv/bin/activate
# streamlit run Welcome.py


from PIL import Image

image = Image.open('data/img_0685_003425.png')
st.image(image, caption='',use_column_width=True)


