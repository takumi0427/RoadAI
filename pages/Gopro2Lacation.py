#%%
# https://blog.amedama.jp/entry/streamlit-tutorial
# https://qiita.com/guunonemodemai/items/1b9ffd8702d4e01075dd
import streamlit as st
from streamlit_folium import st_folium 
import os, glob
import pandas as pd
import GoPro2Location as myloc
st.set_page_config(layout="wide")

#%%
# cdir = st.text_input("RoadAIのパスを指定")
st.subheader('GoPro2Location')
st.text('ルートフォルダ')
cdir = "/Users/takumi/Library/CloudStorage/Dropbox/Active/Python/RoadAI"
if cdir=="":
   st.text(cdir)
else:
   st.text(cdir)




Survey_List = []
for si in glob.glob(cdir+"/00_RawData/*"):
    Sname = si.split("/")[-1]
    Survey_List.append(Sname)
Survey_List = tuple(Survey_List)
Survey_Project = st.selectbox('対象フォルダ', Survey_List)

tid = 0
if st.button(label='動画リストの表示'):
    Spath = sorted(glob.glob(cdir+"/00_RawData/"+Survey_Project+"/00_GoPro/*"))
    for si in range(len(Spath)):
        Sname = Spath[si].split("/")[-1]
        st.text("Survey:{:3.0f} {}".format(si, Sname))
        Mpath = sorted(glob.glob(f'{Spath[si]}/*.MP4'))
        for mi in range(len(Mpath)):
            Mname = Mpath[mi].split("/")[-1]
            GPS5 = len(glob.glob(Mpath[mi].replace(".MP4","*GPS5.csv")))
            ACCL = len(glob.glob(Mpath[mi].replace(".MP4","*ACCL.csv")))
            GYRO = len(glob.glob(Mpath[mi].replace(".MP4","*GYRO.csv")))
            st.text("__TID:{:3.0f} GPS5:{} ACCL:{} GYRO:{} Filename:{}".format(tid, GPS5, ACCL, GYRO, Mname))
            tid+=1
    st.text("Finished.")


ALLDF=[]
tid = 0
if st.button(label='確認マップの作成'):
    Spath = sorted(glob.glob(cdir+"/00_RawData/"+Survey_Project+"/00_GoPro/*"))
    for si in range(len(Spath)):
        Sname = Spath[si].split("/")[-1]
        st.text("Survey:{:3.0f} {}".format(si, Sname))
        Mpath = sorted(glob.glob(f'{Spath[si]}/*.MP4'))
        os.makedirs(Spath[si].replace('00_GoPro', '01_GPSMap'), exist_ok=True)
        for mi in range(len(Mpath)):
            Mname = Mpath[mi].split("/")[-1]
            GPS5 = len(glob.glob(Mpath[mi].replace(".MP4","*GPS5.csv")))
            ACCL = len(glob.glob(Mpath[mi].replace(".MP4","*ACCL.csv")))
            GYRO = len(glob.glob(Mpath[mi].replace(".MP4","*GYRO.csv")))
            df = pd.read_csv(glob.glob(Mpath[mi].replace(".MP4","*GPS5.csv"))[0])
            map, totaldis, MaxDist = myloc.makemap(df)
            map.save(Mpath[mi].replace('.MP4', '.html').replace('00_GoPro', '01_GPSMap'))
            st.text("__TID:{:3.0f} GPS5:{} ACCL:{} GYRO:{} Total:{:>6}km MaxDelta:{:>5}m Filename:{} TID:{:3.0f}".format(tid, GPS5, ACCL, GYRO, totaldis, MaxDist, Mname, tid))
            ALLDF.append([tid, si, Sname, Mname, Mpath[mi], GPS5, ACCL, GYRO, totaldis, MaxDist])
            tid+=1      
    ALLDF = pd.DataFrame(ALLDF)
    ALLDF.columns = ["TID","SID","FolderName","MovieName","Path","GPS5","ACCL","GYRO","TotalDistance","MaxDelta"]
    ALLDF["lt_x"]=550; ALLDF["rt_x"]=1250; ALLDF["lb_x"]=-50; ALLDF["rb_x"]=1950
    ALLDF["LLOC"]=250; ALLDF["Route"] = "202399"
    ALLDF.to_csv(cdir+"/00_RawData/"+Survey_Project+"/MovieList1.csv", index=False)
    st.text("Finished.")


Map_List = []
for si in sorted(glob.glob(cdir+"/00_RawData/"+Survey_Project+"/01_GPSMap/*/*.html")):
    Map_List.append(si.split("/")[-2]+"/"+si.split("/")[-1].replace(".html",""))
Map_List = tuple(Map_List)

if st.button(label='確認マップ'):
    Map_Target = st.selectbox('マップ表示', Map_List)
    df = pd.read_csv(glob.glob(cdir+"/00_RawData/"+Survey_Project+"/00_GoPro/"+Map_Target+"*GPS5.csv")[0])
    map, totaldis, MaxDist = myloc.makemap(df)
    st_data = st_folium(map, width=1200, height=800)
