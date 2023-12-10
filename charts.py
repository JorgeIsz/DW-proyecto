import matplotlib.pyplot as plt
import io


def create_line_chart(name, variable_values):

    # Convert timestamps to (10 AM) format.
    hours = [entry[0].strftime('%I %p') for entry in variable_values]
    values = [entry[1] for entry in variable_values]

    plt.figure(figsize=(8, 6))
    plt.plot(hours, values, marker='o', linestyle='-')
    plt.xlabel('Time of the day')
    plt.xticks(rotation=45, fontsize=8)
    plt.gca().xaxis.set_major_locator(plt.MaxNLocator(10))
    plt.ylabel(name)
    plt.title(f'Hourly {name} Variation')

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)

    return buffer
