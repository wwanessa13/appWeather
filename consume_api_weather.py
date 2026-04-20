import requests
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta

st.set_page_config(page_title="Clima", layout="centered")

st.title("🌤️ Consulta de Clima")

api_key = st.secrets["api_key"]

modo = st.radio("Tipo de consulta:", ["Atual", "Histórico"])
cidade = st.text_input("Digite a cidade:", "Navirai")


def buscar_clima_atual(cidade):
    url = "http://api.weatherapi.com/v1/current.json"
    params = {
        "key": api_key,
        "q": cidade,
        "lang": "pt"
    }
    resposta = requests.get(url, params=params)
    if resposta.status_code == 200:
        return resposta.json()
    return None


def buscar_historico_por_dia(cidade, data_str):
    url = "http://api.weatherapi.com/v1/history.json"
    params = {
        "key": api_key,
        "q": cidade,
        "dt": data_str,
        "lang": "pt"
    }
    resposta = requests.get(url, params=params)
    if resposta.status_code == 200:
        return resposta.json()
    return None


if modo == "Atual":
    if st.button("Buscar clima atual"):
        if cidade:
            dados = buscar_clima_atual(cidade)

            if dados is not None:
                nome = dados["location"]["name"]
                estado = dados["location"]["region"]
                pais = dados["location"]["country"]

                temp = dados["current"]["temp_c"]
                sensacao = dados["current"]["feelslike_c"]
                condicao = dados["current"]["condition"]["text"]
                umidade = dados["current"]["humidity"]
                vento = dados["current"]["wind_kph"]
                icone = "https:" + dados["current"]["condition"]["icon"]

                st.subheader(f"{nome} - {estado} ({pais})")
                st.image(icone, width=100)
                st.write(f"🌡️ Temperatura: {temp}°C")
                st.write(f"🤒 Sensação térmica: {sensacao}°C")
                st.write(f"☁️ Condição: {condicao}")
                st.write(f"💧 Umidade: {umidade}%")
                st.write(f"🌬️ Vento: {vento} km/h")
            else:
                st.error("Não foi possível carregar os dados.")
        else:
            st.warning("Digite uma cidade.")


if modo == "Histórico":
    col1, col2 = st.columns(2)

    with col1:
        data_inicio = st.date_input("Data inicial")
    with col2:
        data_fim = st.date_input("Data final")

    agrupar_dias = st.selectbox(
    "Agrupar dados por:",
    options=[1, 7, 15, 30],
    format_func=lambda x: {
        1: "Diário",
        7: "Semanal (7 dias)",
        15: "Quinzenal (15 dias)",
        30: "Mensal (30 dias)"
    }[x]
    )

    if st.button("Buscar histórico"):
        if not cidade:
            st.warning("Digite uma cidade.")
        elif data_inicio > data_fim:
            st.error("A data inicial não pode ser maior que a data final.")
        else:
            registros = []
            data_atual = data_inicio
            local_info = None

            with st.spinner("Buscando dados históricos..."):
                while data_atual <= data_fim:
                    data_str = data_atual.strftime("%Y-%m-%d")
                    dados = buscar_historico_por_dia(cidade, data_str)

                    if dados is not None:
                        if local_info is None:
                            local_info = dados["location"]

                        dia = dados["forecast"]["forecastday"][0]["day"]

                        registros.append({
                            "data": pd.to_datetime(data_str),
                            "temp_media": dia["avgtemp_c"],
                            "temp_max": dia["maxtemp_c"],
                            "temp_min": dia["mintemp_c"],
                            "umidade_media": dia["avghumidity"],
                            "precipitacao_mm": dia["totalprecip_mm"],
                            "vento_max_kph": dia["maxwind_kph"],
                            "condicao": dia["condition"]["text"]
                        })

                    data_atual += timedelta(days=1)

            if not registros:
                st.error("Não foi possível carregar os dados históricos.")
            else:
                df = pd.DataFrame(registros).sort_values("data").reset_index(drop=True)

                nome = local_info["name"]
                estado = local_info["region"]
                pais = local_info["country"]

                st.subheader(f"{nome} - {estado} ({pais})")
                st.write(
                    f"Período: {data_inicio.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}"
                )

                if agrupar_dias > 1:
                    df["grupo"] = (df.index // agrupar_dias) + 1

                    df_agrupado = df.groupby("grupo").agg(
                        data_inicial=("data", "min"),
                        data_final=("data", "max"),
                        temp_media=("temp_media", "mean"),
                        temp_max=("temp_max", "mean"),
                        temp_min=("temp_min", "mean"),
                        umidade_media=("umidade_media", "mean"),
                        precipitacao_mm=("precipitacao_mm", "sum"),
                        vento_max_kph=("vento_max_kph", "mean")
                    ).reset_index()

                    df_agrupado["periodo"] = (
                        df_agrupado["data_inicial"].dt.strftime("%d/%m/%Y")
                        + " - " +
                        df_agrupado["data_final"].dt.strftime("%d/%m/%Y")
                    )

                    st.write("### Dados agrupados")
                    st.dataframe(
                        df_agrupado[
                            [
                                "periodo",
                                "temp_media",
                                "temp_max",
                                "temp_min",
                                "umidade_media",
                                "precipitacao_mm",
                                "vento_max_kph"
                            ]
                        ],
                        use_container_width=True
                    )

                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.plot(df_agrupado["periodo"], df_agrupado["temp_media"], marker="o")
                    ax.set_title("Temperatura média por período")
                    ax.set_xlabel("Período")
                    ax.set_ylabel("Temperatura média (°C)")
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    st.pyplot(fig)

                else:
                    df["data_formatada"] = df["data"].dt.strftime("%d/%m/%Y")

                    st.write("### Dados diários")
                    st.dataframe(
                        df[
                            [
                                "data_formatada",
                                "temp_media",
                                "temp_max",
                                "temp_min",
                                "umidade_media",
                                "precipitacao_mm",
                                "vento_max_kph",
                                "condicao"
                            ]
                        ],
                        use_container_width=True
                    )

                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.plot(df["data_formatada"], df["temp_media"], marker="o")
                    ax.set_title("Temperatura média por dia")
                    ax.set_xlabel("Data")
                    ax.set_ylabel("Temperatura média (°C)")
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    st.pyplot(fig)
