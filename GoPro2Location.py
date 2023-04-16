import warnings, os
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL']='2'
import math, glob, folium
import numpy as np
import pandas as pd
from scipy import interpolate

# GoProのGPSデータの加工
def MakeLocation(mpath):    
    gpsdf = pd.read_csv(glob.glob(mpath.replace(".MP4","*GPS5.csv"))[0])
    return pd.DataFrame({"LAT":gpsdf["GPS (Lat.) [deg]"],"LON":gpsdf["GPS (Long.) [deg]"]})

#緯度経度から2点間距離を算出
def latlon2dis(df):
  pole_radius = 6356752.314245 # 極半径
  equator_radius = 6378137.0   # 赤道半径   
  DIST=[0]; TDIS=[0]                         
  for i in range(len(df)-1): 
    LAT1 = math.radians(df.LAT[i]);   LON1 = math.radians(df.LON[i])
    LAT2 = math.radians(df.LAT[i+1]); LON2 = math.radians(df.LON[i+1])
    lat_difference = LAT1 - LAT2       # 緯度差
    lon_difference = LON1 - LON2       # 経度差
    lat_average = (LAT1 + LAT2) / 2    # 平均緯度
    e2 = (math.pow(equator_radius, 2) - math.pow(pole_radius, 2)) / math.pow(equator_radius, 2)  # 第一離心率^2
    w = math.sqrt(1- e2 * math.pow(math.sin(lat_average), 2))
    m = equator_radius * (1 - e2) / math.pow(w, 3) # 子午線曲率半径
    n = equator_radius / w                         # 卯酉線曲半径
    distance = math.sqrt(math.pow(m * lat_difference, 2) + math.pow(n * lon_difference * math.cos(lat_average), 2)) # 距離計測m
    DIST.append(distance)
  TDIS = np.cumsum(DIST)
  return pd.DataFrame({"DIST":DIST,"TDIS":TDIS})

# 位置情報の線形補間（フレームタイミングに合わせる）
def Location2Frame(taggis, rawgis, mcount, mtime): 
    # 緯度経度（20Hz）、距離を動画フレームレート60Hzに合わせる
    lframe = np.linspace(0, int(mtime), len(taggis.DIST)); mframe = np.linspace(0, int(mtime), int(mcount))
    # GPS2点間距離の線形補間
    dist2 = taggis.DIST[0:len(lframe)]; f1 = interpolate.interp1d(lframe, dist2); dist_mframe = f1(mframe)
    tdis2 = taggis.TDIS[0:len(lframe)]; f1 = interpolate.interp1d(lframe, tdis2); tdis_mframe = f1(mframe)
    # GPSの線形補間
    gpslon = rawgis.LON[0:len(lframe)]; f1 = interpolate.interp1d(lframe, gpslon); gpslon_mframe = f1(mframe)
    gpslat = rawgis.LAT[0:len(lframe)]; f1 = interpolate.interp1d(lframe, gpslat); gpslat_mframe  = f1(mframe)
    return pd.DataFrame({"TDIS":tdis_mframe, "LON":gpslon_mframe, "LAT":gpslat_mframe, "FrameTime":mframe})

# 動画撮影時のGPSでslenm間隔でポイントを設ける
def MakePoints(OUTDATA, INTERVAL):
    OUTDATA["kp"] = np.floor(OUTDATA["TDIS"]/INTERVAL)
    OUTDATA["FrameNumber"]=OUTDATA.index
    OUTDATA = OUTDATA.groupby("kp").first()
    OUTDATA["METER"] = ((OUTDATA["TDIS"]/INTERVAL)*INTERVAL).astype(int)
    OUTDATA["ImageNumber"] = OUTDATA.index.astype(int)
    OUTDATA.reset_index(drop=True, inplace=True)
    return OUTDATA

#走行方向によって車線側にオフセット
def offsetloc(OUTDATA):
  OFFSET = 0.00002 #緯度経度でのオフセット(約1.5m)
  x0 = np.array(OUTDATA["LON"])
  y0 = np.array(OUTDATA["LAT"])
  x1 = x0[0:len(x0)-1]; x2 = x0[1:len(x0)]
  y1 = y0[0:len(y0)-1]; y2 = y0[1:len(y0)]
  alpa = np.arctan((x2-x1)/(y2-y1))
  dx = OFFSET * np.cos(alpa); dy = OFFSET * np.sin(alpa)
  OLON, OLAT = [], []
  for pi in range(len(OUTDATA)-1):
      px2=x2[pi];px1=x1[pi];pdx=dx[pi]; py2=y2[pi];py1=y1[pi];pdy=dy[pi]
      if (px2-px1)>=0 and (py2-py1)>=0:   OLON.append(px1-pdx); OLAT.append(py1+pdy) #1象限
      elif (px2-px1)>=0 and (py2-py1)<0: OLON.append(px1+pdx); OLAT.append(py1-pdy) #2象限
      elif (px2-px1)<0 and (py2-py1)<0: OLON.append(px1+pdx); OLAT.append(py1-pdy) #3象限  
      elif (px2-px1)<0 and (py2-py1)>=0: OLON.append(px1-pdx); OLAT.append(py1+pdy) #4象限
  if (px2-px1)>=0 and (py2-py1)>=0:   OLON.append(px2-pdx); OLAT.append(py2+pdy) #1象限
  elif (px2-px1)>=0 and (py2-py1)<0: OLON.append(px2+pdx); OLAT.append(py2-pdy) #2象限
  elif (px2-px1)<0 and (py2-py1)<0: OLON.append(px2+pdx); OLAT.append(py2-pdy) #3象限
  elif (px2-px1)<0 and (py2-py1)>=0: OLON.append(px2-pdx); OLAT.append(py2+pdy) #4象限
  OUTDATA["OFFSET_LON"] = OLON; OUTDATA["OFFSET_LAT"] = OLAT
  return OUTDATA

def makemap(df):
  INTERVAL = 5
  df = pd.DataFrame({"LAT":df["GPS (Lat.) [deg]"],"LON":df["GPS (Long.) [deg]"]})
  DIST_TDIS = latlon2dis(df)
  df["DIST"] = DIST_TDIS["DIST"]
  df["TDIS"] = DIST_TDIS["TDIS"]
  df["kp"] = np.floor(df["TDIS"]/INTERVAL)
  df = df.groupby("kp").first()
  df["METER"] = ((df["TDIS"]/INTERVAL)*INTERVAL).astype(int)
  df["DD"]=df["TDIS"].diff(1)
  PLAT = np.array(df.LAT); PLON = np.array(df.LON)
  map = folium.Map(location=[np.mean(PLAT), np.mean(PLON)], tiles='openstreetmap', zoom_start=12, control_scale = True, prefer_canvas=True)
  for i in range(len(df)-1):
      folium.Circle(radius=2, location=[PLAT[i], PLON[i]], color="red", fill=False).add_to(map)
  folium.Marker(location=[PLAT[0], PLON[0]], popup="Start").add_to(map)
  maxdelta = np.round(np.max(df["DD"]),1)
  totaldis = np.round(df["TDIS"].tail(1).values[0],0)/1000
  return map, np.round(totaldis,1), maxdelta