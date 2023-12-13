import psycopg2

def _get_forecast_insert_sql(data):
    full = "INSERT INTO forecast_weather_data VALUES "

    for hour in range(24):
        datetime = data['datetime'][hour]
        temperature_2m = data['temperature_2m'][hour]
        precipitation_probability = data['precipitation_probability'][hour]
        precipitation = data['precipitation'][hour]
        snowfall = data['snowfall'][hour]
        wind_speed_10m = data['wind_speed_10m'][hour]
        values = f"('{datetime}', {temperature_2m}, {precipitation_probability}, {precipitation}, {snowfall}, {wind_speed_10m})"

        full += values
        if hour != 23:
            full += ","

    full += ";"
    return full

def create_connection():
    return psycopg2.connect(
        database="forecast",
        host="localhost",
        user="jorge",
        password="isaza",
        port="5432"
    )

def insert_forecast_data(data):
    conn = create_connection()

    sql = _get_forecast_insert_sql(data)
    cursor = conn.cursor()
    cursor.execute(sql)
    conn.commit()

    cursor.close()
    conn.close()


def get_subscriber_list():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("select email, city_id from subscriber;")
    lista = cursor.fetchall()

    return lista

def get_city_list():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("select city_id, name, latitude, longitude from city;")
    lista = cursor.fetchall()

    return lista

