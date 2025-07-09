import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import os

# === KONFIGURASI STREAMLIT ===
st.set_page_config(page_title="Peta & Unduh Gambar", layout="wide")

# === TEMA WARNA NUDE PASTEL SEDERHANA ===
st.markdown("""
    <style>
        .stApp {
            background-color: #f5ebe0;  /* nude pastel lembut */
            color: #5b3a29;  /* coklat medium hangat */
            font-family: Arial, sans-serif;
        }
        h1 {
            color: #7a563f;  /* coklat agak gelap */
            font-weight: 700;
        }
        h2 {
            color: #9c7a55;  /* coklat muda */
            font-weight: 600;
        }
        .stTextInput label,
        .stSelectbox label {
            color: #5b3a29 !important;
            font-weight: 600;
        }
        .stDownloadButton button:hover {
            background-color: #c49e84;
        }
        .stMarkdown, .stDataFrame, .stImage {
            background-color: rgba(255, 255, 255, 0.85);
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 1px 1px 6px rgba(0,0,0,0.1);
            margin-bottom: 1.5rem;
        }
    </style>
""", unsafe_allow_html=True)

st.title("📍 Peta Sebaran Jaringan Alat Klimatologi BMKG")

csv_folder = 'data alat'  # Folder CSV
colors = ['red', 'blue', 'green', 'purple', 'orange']

# Cek folder CSV dan baca file CSV
if not os.path.exists(csv_folder):
    st.error(f"Folder '{csv_folder}' tidak ditemukan. Pastikan folder sudah ada.")
    st.stop()

csv_files = [f for f in os.listdir(csv_folder) if f.endswith('.csv')]
if not csv_files:
    st.warning(f"Tidak ada file CSV di folder '{csv_folder}'.")
    st.stop()

# Load data CSV
data_dict = {}
all_provinces = set()
for file in csv_files[:5]:
    filepath = os.path.join(csv_folder, file)
    try:
        df = pd.read_csv(filepath, sep=';', on_bad_lines='skip', encoding='utf-8')
        required_cols = ['latt_station', 'long_station', 'nama_propinsi']
        if not all(col in df.columns for col in required_cols):
            st.warning(f"File '{file}' tidak memiliki kolom wajib: {', '.join(required_cols)}")
            continue
        data_dict[file] = df
        all_provinces.update(df['nama_propinsi'].dropna().unique())
    except Exception as e:
        st.error(f"Gagal membaca file '{file}': {e}")

if not data_dict:
    st.error("Tidak ada data yang bisa ditampilkan setelah membaca file CSV.")
    st.stop()

all_provinces = sorted(all_provinces)

# Filter UI
st.subheader("Filter Data Berdasarkan Provinsi dan Jenis Alat Pengamatan")

def beautify_filename(name):
    return os.path.splitext(name)[0].replace('_', ' ').upper()

alat_display_map = {file: beautify_filename(file) for file in data_dict}
reverse_alat_map = {v: k for k, v in alat_display_map.items()}

selected_provinsi = st.selectbox("Pilih Provinsi:", options=["Semua Provinsi"] + all_provinces)
selected_alat_display = st.selectbox("Pilih Alat:", options=["Semua Alat"] + list(alat_display_map.values()))
selected_alat = None if selected_alat_display == "Semua Alat" else reverse_alat_map[selected_alat_display]

# Peta
st.subheader("Peta Interaktif Sebaran Jaringan Alat")

m = folium.Map(location=[-2.5, 118], zoom_start=5)
prov_clusters = {}

def should_show(prov, alat_file):
    if selected_provinsi != "Semua Provinsi" and prov != selected_provinsi:
        return False
    if selected_alat and alat_file != selected_alat:
        return False
    return True

marker_count = 0
for i, (file, df) in enumerate(data_dict.items()):
    for _, row in df.iterrows():
        prov = row.get('nama_propinsi', 'Provinsi Tidak Diketahui')
        try:
            lat = float(row['latt_station'])
            lon = float(row['long_station'])
        except:
            continue
        if not should_show(prov, file):
            continue
        popup_html = "<br>".join([f"<b>{col}:</b> {row.get(col, '')}" for col in df.columns if col in row])
        if prov not in prov_clusters:
            prov_clusters[prov] = MarkerCluster(name=prov)
            prov_clusters[prov].add_to(m)
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=prov,
            icon=folium.Icon(color=colors[i % len(colors)])
        ).add_to(prov_clusters[prov])
        marker_count += 1

folium.LayerControl().add_to(m)
st.markdown(f"📌 Total titik ditampilkan: **{marker_count}**")
st_folium(m, width=1000, height=600)

# Unduh gambar
st.subheader("📥 Unduh Hasil Layout Peta")

image_folder = 'pemetaan alat'

if not os.path.exists(image_folder):
    st.error(f"Folder '{image_folder}' tidak ditemukan.")
else:
    image_files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not image_files:
        st.info(f"Tidak ada file gambar ditemukan di folder '{image_folder}'.")
    else:
        selected_image = st.selectbox("Pilih gambar untuk diunduh:", ["- Pilih gambar -"] + image_files)
        if selected_image != "- Pilih gambar -":
            image_path = os.path.join(image_folder, selected_image)
            st.image(image_path, caption=selected_image, use_container_width=True)

            with open(image_path, "rb") as file:
                st.download_button(
                    label="📥 Klik untuk Unduh",
                    data=file,
                    file_name=selected_image,
                    mime="image/png"
                )
