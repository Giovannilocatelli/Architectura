from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/', methods=['GET'])
def obtener_tiempo():
    # Solicitud HTTP para obtener la temperatura en la ubicación actual
    url = "https://www.timeanddate.com/weather/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    temperatura_actual = soup.find("span", class_="my-city__temp").text.strip()

    # Solicitud HTTP para obtener la información del tiempo en San Sebastián
    url_sansebastian = "https://www.timeanddate.com/weather/spain/san-sebastian"
    response_sansebastian = requests.get(url_sansebastian)
    soup_sansebastian = BeautifulSoup(response_sansebastian.content, "html.parser")
    tabla = soup_sansebastian.find("table", class_="table table--left table--inner-borders-rows")

    elemento_humedad = None
    hora = None

    if tabla is not None:
        filas = tabla.find_all("tr")
        for fila in filas:
            encabezado = fila.find("th")
            if encabezado is not None and encabezado.text.strip() == "Humidity:":
                elemento_humedad = fila.find("td").text.strip()
                break
        for fila in filas:
            encabezado = fila.find("th")
            if encabezado is not None and encabezado.text.strip() == "Current Time:":
                hora = fila.find("td").text.strip()
                break

    datos = {
        "temperatura_actual": temperatura_actual,
        "humedad": elemento_humedad,
        "hora": hora
    }

    return jsonify(datos)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
