from retry_requests import retry
import requests_cache
import pandas as pd
import openmeteo_requests
from decouple import config

from send_email import send_email

cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

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
	#	"weather_code": ,
}

weather_variables_list = list(weather_variables.keys())
url = "https://api.open-meteo.com/v1/forecast"
def request_weather_data():

	# TODO: change this vancouver coordinates to parameters
	params = {
		"latitude": 49.2497,
		"longitude": -123.1193,
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


if __name__ == "__main__":
	# Get 24-hour weather data from open-meteo API
	weather_data = request_weather_data()

	# Look for variables that indicate bad weather
	bad_weather_forecast = check_for_bad_weather(weather_data)

	# Send email with the bad weather information
	send_email(config('EMAIL_RECIPIENT'), bad_weather_forecast)
