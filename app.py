import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="建築規制マップ", layout="wide")
st.title('🏗️ 建築規制・用途地域マップ')

# --- 1. 記憶領域 ---
if 'lat' not in st.session_state:
    st.session_state.lat = None
if 'lon' not in st.session_state:
    st.session_state.lon = None
if 'address_searched' not in st.session_state:
    st.session_state.address_searched = ""

# --- 2. サイドバー ---
with st.sidebar:
    st.header("検索・設定")
    input_address = st.text_input('住所を入力', '東京都新宿区西新宿2-8-1')
    search_btn = st.button('検索する')
    st.divider()
    opacity_val = st.slider('色の濃さ', 0.0, 1.0, 0.4)
    st.caption("※ストリートビュー機能を追加しました！")

# --- 3. 検索処理 ---
if search_btn:
    geo_url = "https://msearch.gsi.go.jp/address-search/AddressSearch"
    try:
        response = requests.get(geo_url, params={'q': input_address})
        data = response.json()

        if len(data) > 0:
            location = data[0]['geometry']['coordinates']
            st.session_state.lon = location[0]
            st.session_state.lat = location[1]
            st.session_state.address_searched = input_address
        else:
            st.error("住所が見つかりませんでした。")
    except Exception as e:
        st.error(f"エラー: {e}")

# --- 4. メイン画面 ---
if st.session_state.lat is not None:
    
    col_map, col_info = st.columns([2, 1])
    
    with col_map:
        st.success(f"📍 {st.session_state.address_searched}")
        
        # --- ここが新機能！ストリートビューへのリンクボタン ---
        # GoogleマップのURLを裏技的に生成します
        # layer=c & cbll=緯度,経度 でストリートビューを強制的に開きます
        sv_url = f"https://www.google.com/maps?layer=c&cbll={st.session_state.lat},{st.session_state.lon}"
        
        # リンクボタンを表示
        st.link_button("🏃‍♂️ この場所のストリートビューを開く（Googleマップ）", sv_url, type="primary")

        # 地図表示
        m = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=18) # ズームを少しアップ
        
        folium.TileLayer(
            tiles='https://cyberjapandata.gsi.go.jp/xyz/ort/{z}/{x}/{y}.jpg',
            attr='国土地理院 航空写真',
            name='航空写真',
        ).add_to(m)
        
        folium.TileLayer(
            tiles='https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png',
            attr='国土地理院 淡色地図',
            name='標準地図',
        ).add_to(m)

        folium.TileLayer(
            tiles='https://cyberjapandata.gsi.go.jp/xyz/youl/{z}/{x}/{y}.png',
            attr='国土地理院 用途地域データ',
            name='用途地域（色分け）',
            opacity=opacity_val,
            overlay=True
        ).add_to(m)

        folium.Marker([st.session_state.lat, st.session_state.lon], popup="現場").add_to(m)
        folium.LayerControl().add_to(m)
        st_folium(m, height=500, use_container_width=True)

    with col_info:
        st.subheader("📖 色の見方と法律の目安")
        
        tab1, tab2, tab3 = st.tabs(["住居系", "商業系", "工業系"])
        with tab1:
            st.markdown("**🟩 緑色系（住居）**\n* 建ぺい率: 30-60%\n* 容積率: 50-200%")
        with tab2:
            st.markdown("**🟥 赤色系（商業）**\n* 建ぺい率: 80%\n* 容積率: 300-1300%")
        with tab3:
            st.markdown("**🟦 青色系（工業）**\n* 建ぺい率: 60%\n* 容積率: 200-400%")
            
        st.warning("※正確な数値は役所の都市計画図を確認してください。")
        st.image("https://maps.gsi.go.jp/help/legend/youl.png")

else:
    st.info("👈 左側で住所を検索してください")