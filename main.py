from typing import Union
from retry_requests import retry
import requests_cache
import pandas as pd
import openmeteo_requests
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from emailing import send_email
from store_db import insert_forecast_data, get_subscriber_list, get_city_list, register_subscriber

cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)


class Range:
    def __init__(self, min, max):
        self.min = min
        self.max = max

    def is_bad_weather(self, value):
        return (self.min != None and value <= self.min) or (self.max != None and value >= self.max)


weather_variables = {
    "temperature_2m": Range(8, 30),
    "precipitation_probability": Range(None, 70),
    "precipitation": Range(None, 8),
    "snowfall": Range(None, 8),
    "wind_speed_10m": Range(None, 50),
}

weather_variables_list = list(weather_variables.keys())
url = "https://api.open-meteo.com/v1/forecast"


def request_weather_data(latitude, longitude):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": weather_variables_list,
        "forecast_days": 1
    }
    responses = openmeteo.weather_api(url, params=params)

    response = responses[0]
    print(f"Coordinates {response.Latitude()}°E {response.Longitude()}°N")
    print(f"Elevation {response.Elevation()} m asl")
    print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

    hourly = response.Hourly()
    hourly_data = {"datetime": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s"),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s"),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    )}
    for i in range(len(weather_variables_list)):
        variable_name = weather_variables_list[i]
        values = hourly.Variables(i).ValuesAsNumpy()
        hourly_data[variable_name] = values

    return hourly_data


def check_for_bad_weather(data):
    bad_weather_results = {}
    for i in range(len(data["datetime"])):
        datetime = data["datetime"][i]
        for variable, delimiter in weather_variables.items():
            value = data[variable][i]
            if delimiter.is_bad_weather(value):
                if variable in bad_weather_results:
                    bad_weather_results[variable].append((datetime, value))
                else:
                    bad_weather_results[variable] = [(datetime, value)]

    return bad_weather_results


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/")
def read_root(request: Request, sub: Union[int, None] = None):
    return templates.TemplateResponse("index.html", {"request": request, "sub": sub})


@app.post("/subscribe/")
async def post_create_subscriber(request: Request):
    form = await request.form()
    email = form.get("email")
    city_id = int(form.get("city_id"))

    register_subscriber(email, city_id)

    cities = get_city_list()
    city = list(filter(lambda x: x[0] == city_id, cities))[0]

    send_bad_weather_forecast_to_email(email, city)
    return RedirectResponse(url="/?sub=1", status_code=303)


def send_bad_weather_forecast_to_email(email, city):
    latitude = city[2]
    longitude = city[3]

    # Get 24-hour weather data from open-meteo API
    weather_data = request_weather_data(latitude, longitude)

    # Look for variables that indicate bad weather
    bad_weather_forecast = check_for_bad_weather(weather_data)

    insert_forecast_data(weather_data)

    # Send email with the bad weather information
    send_email(email, bad_weather_forecast, city)


if __name__ == "__main__":
    subscribers = get_subscriber_list()

    cities = get_city_list()

    for subscriber in subscribers:
        city = list(filter(lambda x: x[0] == subscriber[1], cities))[0]
        email = subscriber[0]

        send_bad_weather_forecast_to_email(email, city)
