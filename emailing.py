import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from decouple import config

from charts import create_line_chart


sender = config('SENDER_EMAIL')
password = config('SENDER_PASSWORD')
smtp_server = config('SMTP_SERVER')
smtp_port = config('SMTP_PORT')

variables_text = {
    'temperature_2m': {
        'name': 'Temperature',
        'bad_desc': 'unideal temperature',
    },
    'apparent_temperature': {
        'name': 'Apparent Temperature',
        'bad_desc': 'unideal apparent temperature',
    },
    "precipitation_probability": {
        'name': 'Precipitation Change',
        'bad_desc': 'high precipitation change',
    },
    "precipitation": {
        'name': 'Precipitation',
        'bad_desc': "heavy precipitation"
    },
    "snowfall": {
        'name': 'Snowfall',
        'bad_desc': 'heavy snowfall'
    },
    "wind_speed_10m": {
        'name': 'Wind Speed (km/h)',
        'bad_desc': "high wind speed"
    }
}


def create_email_body(bad_weather_forecast, city_name):
    variables = list(bad_weather_forecast.keys())
    variables_description = ""
    variables_charts = ""
    for i in range(len(variables)):
        variable = variables[i]
        variables_description += variables_text[variable]['bad_desc']
        variables_charts += f"<h2>{variables_text[variable]['name']}</h2>"
        variables_charts += f'<img src="cid:{variable}">'
        if i == len(variables) - 2:
            variables_description += " and "
        elif i != len(variables) - 1:
            variables_description += ", "

    body = f"""
    <html>
  		<body style="font-size: 18px">
  		
		<bold>Hello.</bold>
		
		<p>You're receiving this email because the forecast suggests bad weather in {city_name}.
		More specifically: {variables_description}.</p>
		
		<p>Here's the full report:</p>
		{variables_charts}
  	    </body>
	</html>
	"""
    return body


def send_email(recipient, bad_weather_forecast, city):
    city_name = city[1]

    email = MIMEMultipart()
    email['From'] = f'Data Warehouse group project <{sender}>'
    email['To'] = recipient
    email['Subject'] = f'Bad Weather Report for the city of {city_name}'

    body = create_email_body(bad_weather_forecast, city_name)
    email.attach(MIMEText(body, 'html'))

    # Create a line chart for each bad weather variable's forecast
    for variable, values in bad_weather_forecast.items():
        buffer = create_line_chart(variables_text[variable]['name'], values)

        # attach the chart to the email
        image = MIMEImage(buffer.read())
        image.add_header('Content-ID', f'<{variable}>')
        image.add_header('Content-Disposition', 'attachment', filename=f'{variable}_chart.png')
        email.attach(image)

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender, password)
        server.send_message(email)
