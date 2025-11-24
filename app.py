import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# ページの設定（ワイド表示にする）
st.set_page_config(page_title="建築規制マップ", layout="wide")

# --- 【セキュリティ機能】 ---
# サイドバーで合言葉を求めます
st.sidebar.title("🔐 認証")
password = st.sidebar.text_input("合言葉を入力してください", type="password")

# 合言葉が合っていない場合はここでストップ
# ※ "0525" の部分は好きなパスワードに変えてください
if password != "0525":
    st.sidebar.warning("合言葉を入力するとアプリが使えます。")
    st.title("🔒 ロックされています")
    st.write("サイドバーに合言葉を入力してください。")
    st.stop()  # ここで処理を強制終了

# --- ここからメインアプリの処理 ---

st.title('🏗️ 建築規制・用途地域マップ')

# --- 1. 記憶領域（セッションステート）の初期化 ---
if 'lat' not in st.session_state:
    st.session_state.lat = None
if 'lon' not in st.session_state:
    st.session_state.lon = None
if 'address_searched' not in st.session_state:
    st.session_state.address_searched = ""

# --- 2. サイドバー（検索・設定） ---
with st.sidebar:
    st.divider()
    st.header("検索・設定")
    input_address = st.text_input('住所を入力', '東京都新宿区西新宿2-8-1')
    search_btn = st.button('検索する')
    
    st.divider()
    opacity_val = st.slider('色の濃さ（透明度）', 0.0, 1.0, 0.4)
    st.caption("※地図右上のレイヤーボタンで航空写真に切り替え可能")

# --- 3. 検索ボタンが押された時の処理 ---
if search_btn:
    geo_url = "https://msearch.gsi.go.jp/address-search/AddressSearch"
    try:
        response = requests.get(geo_url, params={'q': input_address})
        data = response.json()

        if len(data) > 0:
            location = data[0]['geometry']['coordinates']
            # 記憶領域に保存
            st.session_state.lon = location[0]
            st.session_state.lat = location[1]
            st.session_state.address_searched = input_address
        else:
            st.error("住所が見つかりませんでした。")

    except Exception as e:
        st.error(f"エラー: {e}")

# --- 4. メイン画面表示（検索済みのときだけ表示） ---
if st.session_state.lat is not None:
    
    # 画面を左右に分割（2:1）
    col_map, col_info = st.columns([2, 1])
    
    # 左側：地図エリア
    with col_map:
        st.success(f"📍 {st.session_state.address_searched}")
        
        # Googleマップ（ストリートビュー）へのリンクURL作成
        sv_url = f"https://www.google.com/maps?layer=c&cbll={st.session_state.lat},{st.session_state.lon}"
        st.link_button("🏃‍♂️ この場所のストリートビューを開く（Googleマップ）", sv_url, type="primary")

        # 地図の作成
        m = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=18)

        # 1. 航空写真レイヤー
        folium.TileLayer(
            tiles='https://cyberjapandata.gsi.go.jp/xyz/ort/{z}/{x}/{y}.jpg',
            attr='国土地理院 航空写真',
            name='航空写真',
        ).add_to(m)

        # 2. 標準地図レイヤー
        folium.TileLayer(
            tiles='https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png',
            attr='国土地理院 淡色地図',
            name='標準地図',
        ).add_to(m)

        # 3. 用途地域レイヤー（スライダーの透明度を反映）
        folium.TileLayer(
            tiles='https://cyberjapandata.gsi.go.jp/xyz/youl/{z}/{x}/{y}.png',
            attr='国土地理院 用途地域データ',
            name='用途地域（色分け）',
            opacity=opacity_val,
            overlay=True
        ).add_to(m)

        # ピンとレイヤーコントロール
        folium.Marker([st.session_state.lat, st.session_state.lon], popup="検索地").add_to(m)
        folium.LayerControl().add_to(m)

        # 地図描画
        st_folium(m, height=600, use_container_width=True)

    # 右側：情報の目安エリア
    with col_info:
        st.subheader("📖 色の見方と法律の目安")
        
        # タブで表示切り替え
        tab1, tab2, tab3 = st.tabs(["住居系", "商業系", "工業系"])
        
        with tab1:
            st.markdown("""
            **🟩 緑色系（第一種・第二種低層など）**
            * **特徴**: 静かな住宅街。
            * **建ぺい率**: 30%〜60%
            * **容積率**: 50%〜200%
            """)
            
        with tab2:
            st.markdown("""
            **🟥 赤色・ピンク系（商業・近隣商業）**
            * **特徴**: 駅前、幹線道路沿い。
            * **建ぺい率**: 80%
            * **容積率**: 300%〜1300%
            """)
            
        with tab3:
            st.markdown("""
            **🟦 水色・青色系（準工業・工業など）**
            * **特徴**: 工場と住宅が混在、または工場地帯。
            * **建ぺい率**: 60%
            * **容積率**: 200%〜400%
            """)
        
        st.info("※正確な数値は必ず各自治体の都市計画図を確認してください。")
        st.image("https://maps.gsi.go.jp/help/legend/youl.png", caption="国土地理院 凡例")

else:
    # まだ検索していない時の表示
    st.info("👈 左側のサイドバーに合言葉を入力し、住所を検索してください。")