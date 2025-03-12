import pandas as pd
import streamlit as st
import plotly.express as px

from methods import (
    analyze_city_data_avg_and_std,
    get_temperature_for_city,
    temperature_segment_for_city,
    union_of_two_analysis,
    visualize,
)


def main():
    st.set_page_config(page_title="Анализ температур", page_icon="🌤️", layout="wide")
    st.markdown(
        """
        <h1 style='text-align: center; color: #4CAF50;'>Анализ временных рядов температуры</h1>
        <p style='text-align: center; font-size: 18px;'>Загрузите данные и изучите статистику по городам</p>
    """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader("📂 Выберите CSV файл с данными о погоде")

    if uploaded_file is not None:
        dataframe = pd.read_csv(uploaded_file, parse_dates=["timestamp"])

        if dataframe.empty:
            st.warning("⚠️ Добавленный файл пуст!", icon="⚠️")
            return

        st.sidebar.markdown("### Фильтрация данных")
        city = st.sidebar.selectbox(
            "🏙️ Выберите город", tuple(dataframe["city"].unique()), index=None
        )
        api_key = st.sidebar.text_input("🔑 API ключ для текущей температуры", "Нет")

        if city:
            st.markdown(f"## 📊 Анализ данных для {city}")
            analysis_result = union_of_two_analysis(dataframe)
            fig = visualize(analysis_result, city)
            st.plotly_chart(fig)

            if api_key != "Нет":
                historical_data = temperature_segment_for_city(dataframe, city)
                cur_temp = get_temperature_for_city(city, api_key=api_key)
                with st.expander("🌡️ Текущая температура"):
                    if not cur_temp:
                        st.error("🚨 API ключ неверный!")
                        st.info(
                            "Посетите [OpenWeatherMap](https://openweathermap.org/faq#error401) для получения информации."
                        )
                    else:
                        st.success(f"Текущая температура в {city}: {cur_temp}°C")
                        status = (
                            "нормальной"
                            if abs(historical_data[1] - cur_temp) <= 10
                            else "аномальной"
                        )
                        st.write(f"🔍 Температура является: **{status}**")

            city_data = dataframe[dataframe["city"] == city]
            seasonal_analysis = analyze_city_data_avg_and_std(city_data)

            with st.expander("📈 Основные показатели"):
                st.metric("Количество записей", len(city_data))
                st.metric(
                    "Средняя температура", f"{city_data['temperature'].mean():.2f}°C"
                )
                st.metric(
                    "Минимальная температура", f"{city_data['temperature'].min():.2f}°C"
                )
                st.metric(
                    "Максимальная температура",
                    f"{city_data['temperature'].max():.2f}°C",
                )

            st.markdown("### 📅 Сезонный анализ")
            fig_seasonal = px.box(
                seasonal_analysis,
                x="season",
                y="mean",
                title="Средняя температура по сезонам",
                color="season",
                template="plotly_dark",
            )
            st.plotly_chart(fig_seasonal)


if __name__ == "__main__":
    main()
