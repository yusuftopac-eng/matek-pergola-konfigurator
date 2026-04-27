import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Sayfa Ayarları
st.set_page_config(page_title="Matek Grup - Pergola Konfigüratör", layout="wide")

st.title("Yüksek Segment Manuel Pergola - 3D Konfigüratör ve ERP Arayüzü")

# 1. SOL MENÜ (SIDEBAR) - Kullanıcı Girdileri
st.sidebar.header("Konfigürasyon (cm)")
width = st.sidebar.slider("Genişlik (X Eksen)", 200, 600, 300, step=10)
length = st.sidebar.slider("Açılım / Uzunluk (Y Eksen)", 200, 800, 400, step=10)
height = st.sidebar.slider("Dikme Yüksekliği (Z Eksen)", 200, 300, 250, step=10)

color = st.sidebar.selectbox("Profil Rengi", ["Antrasit Gri (RAL 7016)", "Beyaz (RAL 9016)", "Siyah (RAL 9005)"])
mechanism = st.sidebar.selectbox("Şanzıman Tipi", ["Standart Şanzıman", "Ağır Yük (High Segment) Şanzıman"])

# 2. 3D ÇİZİM FONKSİYONU (Plotly ile dinamik modelleme)
def draw_pergola_3d(w, l, h):
    fig = go.Figure()
    
    # Ana İskelet Köşe Koordinatları
    x = [0, w, w, 0, 0, w, w, 0]
    y = [0, 0, l, l, 0, 0, l, l]
    z = [0, 0, 0, 0, h, h, h, h]
    
    # 4 Adet Dikme (Pillars)
    for i in range(4):
        fig.add_trace(go.Scatter3d(x=[x[i], x[i+4]], y=[y[i], y[i+4]], z=[z[i], z[i+4]], 
                                   mode='lines', line=dict(color='gray', width=15), name=f'Dikme {i+1}'))
        
    # Üst Çevre Kirişleri
    fig.add_trace(go.Scatter3d(x=[0, w, w, 0, 0], y=[0, 0, l, l, 0], z=[h, h, h, h, h], 
                               mode='lines', line=dict(color='darkblue', width=12), name='Çevre Kirişleri'))
    
    # Tavan Lamelleri (Uzunluğa göre dinamik olarak hesaplanıp çizilir)
    lamel_araligi = 25 # cm
    num_lamels = int(l / lamel_araligi) 
    for i in range(1, num_lamels):
        y_pos = i * lamel_araligi
        fig.add_trace(go.Scatter3d(x=[0, w], y=[y_pos, y_pos], z=[h, h], 
                                   mode='lines', line=dict(color='lightblue', width=8), showlegend=False))

    # Kamera ve Sahne Ayarları
    fig.update_layout(scene=dict(
                        xaxis=dict(range=[0, max(w,l)], title='Genişlik'),
                        yaxis=dict(range=[0, max(w,l)], title='Açılım'),
                        zaxis=dict(range=[0, h+50], title='Yükseklik')),
                      margin=dict(l=0, r=0, b=0, t=0), height=500)
    return fig

# 3. SEKMELİ YAPI (TABS)
tab1, tab2, tab3 = st.tabs(["📐 3D Görüntüleme", "📋 BOM (Ürün Ağacı)", "💰 Maliyet Analizi"])

# --- TAB 1: 3D Önizleme ---
with tab1:
    st.subheader(f"3D Önizleme - {width}x{length}x{height} cm")
    fig = draw_pergola_3d(width, length, height)
    st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: BOM Hesaplama ---
with tab2:
    st.subheader("Dinamik Ürün Ağacı (BOM)")
    
    # Girdileri metreye çevirerek metraj hesaplama
    dikme_boyu = height / 100 
    kiris_x_boyu = width / 100
    kiris_y_boyu = length / 100
    lamel_sayisi = int(length / 25)
    lamel_boyu = width / 100
    
    bom_data = [
        {"Stok Kodu": "PROF-AL-001", "Tanım": "Ana Taşıyıcı Dikme", "Miktar": 4 * dikme_boyu, "Birim": "m"},
        {"Stok Kodu": "PROF-AL-002", "Tanım": "Yan Kiriş Profili (Açılım)", "Miktar": 2 * kiris_y_boyu, "Birim": "m"},
        {"Stok Kodu": "PROF-AL-003", "Tanım": "Ön/Arka Kayıt Profili", "Miktar": 2 * kiris_x_boyu, "Birim": "m"},
        {"Stok Kodu": "ROOF-LML-01", "Tanım": "Hareketli Tavan Lameli", "Miktar": lamel_sayisi * lamel_boyu, "Birim": "m"},
        {"Stok Kodu": "MEK-GBX", "Tanım": mechanism, "Miktar": 1, "Birim": "Adet"},
        {"Stok Kodu": "HW-BRK", "Tanım": "Paslanmaz Braket Seti", "Miktar": 1, "Birim": "Set"}
    ]
    df_bom = pd.DataFrame(bom_data)
    st.dataframe(df_bom, use_container_width=True)
    
    # İleride eklenebilecek SQL butonu
    st.button("ERP Sistemine Aktar (SQL Insert)")

# --- TAB 3: Maliyet Analizi ---
with tab3:
    st.subheader("Maliyet ve Karlılık Simülasyonu")
    
    # Temsili Birim Fiyatlar (Veritabanından çekilecek kısımlar)
    fiyatlar = {
        "m_aluminyum": 450, # TL/m
        "mekanizma_std": 2500,
        "mekanizma_high": 5500,
        "braket_set": 1200
    }
    
    toplam_aluminyum_m = (4 * dikme_boyu) + (2 * kiris_y_boyu) + (2 * kiris_x_boyu) + (lamel_sayisi * lamel_boyu)
    alu_maliyet = toplam_aluminyum_m * fiyatlar["m_aluminyum"]
    mek_maliyet = fiyatlar["mekanizma_high"] if "High" in mechanism else fiyatlar["mekanizma_std"]
    diger_maliyet = fiyatlar["braket_set"]
    
    toplam_maliyet = alu_maliyet + mek_maliyet + diger_maliyet
    satis_fiyati = toplam_maliyet * 1.60 # %60 Kar Marjı
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Toplam Hammadde Maliyeti", f"{toplam_maliyet:,.2f} ₺")
    col2.metric("Önerilen E-Ticaret Satış Fiyatı", f"{satis_fiyati:,.2f} ₺")
    col3.metric("Tahmini Kar Marjı", "%60")
    
    st.markdown("### Maliyet Kırılımı")
    maliyet_df = pd.DataFrame({
        "Kalem": ["Alüminyum Profiller", "Şanzıman Mekanizması", "Braket ve Hırdavat"],
        "Tutar (TL)": [alu_maliyet, mek_maliyet, diger_maliyet]
    })
    st.bar_chart(maliyet_df.set_index("Kalem"))