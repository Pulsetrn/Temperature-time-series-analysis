import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go


def analyze_city_data_window(city_data, window=30):
    df = city_data.sort_values("timestamp").copy()
    df["rolling_mean"] = df["temperature"].rolling(window=window).mean()
    df["rolling_std"] = df["temperature"].rolling(window=window).std()

    df["anomaly"] = False
    mask_anomaly = (df["temperature"] > df["rolling_mean"] + 2 * df["rolling_std"]) | (
        df["temperature"] < df["rolling_mean"] - 2 * df["rolling_std"]
    )
    df.loc[mask_anomaly, "anomaly"] = True

    df["day_number"] = (df["timestamp"] - df["timestamp"].min()).dt.days
    coeffs = np.polyfit(df["day_number"], df["temperature"], deg=1)
    df["trend"] = coeffs[0] * df["day_number"] + coeffs[1]

    return df


def analyze_city_data_avg_and_std(city_data):
    df = city_data.groupby(["city", "season"])["temperature"].agg(["mean", "std"])
    df.reset_index(inplace=True)

    return df


def union_of_two_analysis(df):
    first = analyze_city_data_avg_and_std(df)
    second = analyze_city_data_window(df)
    result = second.merge(first, on=["city", "season"])
    return result


def get_temperature_for_city(city, api_key):
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&appid={api_key}"
    geo_response = requests.get(geo_url)
    geo_data = geo_response.json()

    if not geo_data or not isinstance(geo_data, list):
        print(
            f"Ошибка: API не вернул данные о координатах для города {city}. Ответ: {geo_data}"
        )
        return None

    lat, lon = geo_data[0].get("lat"), geo_data[0].get("lon")
    if lat is None or lon is None:
        print(
            f"Ошибка: не удалось получить координаты для города {city}. Ответ: {geo_data}"
        )
        return None

    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    weather_response = requests.get(weather_url)
    weather_data = weather_response.json()

    if "main" not in weather_data or "temp" not in weather_data["main"]:
        print(
            f"Ошибка: API не вернул данные о температуре для города {city}. Ответ: {weather_data}"
        )
        return None

    return weather_data["main"]["temp"]


def visualize(df, city_example):
    city_df = df[df["city"] == city_example].copy()
    city_df = city_df.sort_values("timestamp")

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=city_df["timestamp"],
            y=city_df["temperature"],
            mode="lines",
            name="Температура",
            opacity=0.3,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=city_df["timestamp"],
            y=city_df["rolling_mean"],
            mode="lines",
            name="Скользящее среднее",
            line=dict(color="green"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=city_df["timestamp"],
            y=city_df["rolling_std"],
            mode="lines",
            name="Стандартное отклонение",
            line=dict(color="violet"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=city_df["timestamp"],
            y=city_df["trend"],
            mode="lines",
            name="Тренд",
            line=dict(color="red"),
        )
    )

    anomalies = city_df[city_df["anomaly"]]
    fig.add_trace(
        go.Scatter(
            x=anomalies["timestamp"],
            y=anomalies["temperature"],
            mode="markers",
            name="Аномалия",
            marker=dict(color="red", size=4),
        )
    )

    fig.update_layout(
        title=f"Город: {city_example} — температура, скользящее среднее, аномалии и тренд",
        xaxis_title="Дата",
        yaxis_title="Температура",
        template="plotly_white",
    )

    return fig


def temperature_segment_for_city(df, city: str):
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["day_of_year"] = df["timestamp"].dt.dayofyear
    df_berlin = df[df["city"] == city]
    historical_range = (
        df_berlin.groupby("day_of_year")["temperature"]
        .agg(["min", "max"])
        .reset_index()
    )
    historical_avg = (
        df_berlin.groupby("day_of_year")["temperature"].mean().reset_index()
    )
    today_day_of_year = pd.Timestamp.today().day_of_year
    temp_range = historical_range.loc[
        historical_range["day_of_year"] == today_day_of_year, ["min", "max"]
    ]
    avg_temp = historical_avg.loc[
        historical_avg["day_of_year"] == today_day_of_year, "temperature"
    ].values
    return temp_range, avg_temp
