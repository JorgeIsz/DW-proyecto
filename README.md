# Data Warehouse Concepts project

## What does this code do?

1. Fetch data from weather API (open-meteo)
2. Determine what can be considered bad weather
3. Send the bad weather report to the email list periodically with a scheduler
4. Store processed weather data in database
5. Provides a web UI for users to subscribe to the email list


# Database structure
This project relies on a Postgres database with 3 tables: `forecast_weather_data`, `subscriber` and `city`

## `forecast_weather_data`

This is where we store the historical forecast data. Every entry has a related `city_id` that represents which city's weather
data it was.

`forecast_id | datetime | temperature_2m | precipitation_probability | precipitation | snowfall | wind_speed_10m | city_id`

## `subscriber`
This is where we store the email list. It also stores the city that the subscriber wants to receive weather alerts of.

`subscriber_id | email | city_id`

# `city`
This is where we store the coordinates of each city/town, that the weather API needs to properly locate the weather variables.
We manually added a few entries to this table with large cities in BC.

Example: `insert into city (name, latitude, longitude) values, ('Surrey', 49.1063, -122.8251), ('Vancouver', 49.2497, -123.1193), ('Richmond', 49.17, -123.1368), ('Delta', 49.144, -122.9068), ('Burnaby', 49.241526, -122.979801);`

`city_id | name | latitude | longitude`



