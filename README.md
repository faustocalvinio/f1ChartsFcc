# F1 Charts App

Aplicación web desarrollada con Django para visualizar y comparar datos de la temporada 2025 de Fórmula 1 utilizando la API FastF1.

![F1 Charts App](media/f1-charts-screenshot.png)

## Características

- **Estrategias de Neumáticos**: Visualización de las estrategias de neumáticos utilizadas por cada piloto en una carrera.
- **Tiempos de Vuelta**: Consulta de los tiempos de vuelta para cualquier piloto y carrera.
- **Comparación de Pilotos**: Comparación directa de los tiempos de vuelta entre dos pilotos en la misma carrera.

## Tecnologías Utilizadas

- **Backend**: Django 5.2.4
- **Datos F1**: API FastF1
- **Visualización**: Plotly
- **Procesamiento de Datos**: Pandas
- **Frontend**: HTML, CSS, JavaScript

## Requisitos

- Python 3.10+
- Django 5.2+
- FastF1
- Plotly
- Pandas

## Instalación

1. Clona este repositorio:
   ```
   git clone https://github.com/faustocalvinio/f1ChartsFcc.git
   cd f1ChartsFcc
   ```

2. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```

3. Ejecuta las migraciones:
   ```
   python manage.py migrate
   ```

4. Inicia el servidor de desarrollo:
   ```
   python manage.py runserver
   ```

5. Accede a la aplicación en tu navegador:
   ```
   http://127.0.0.1:8000/
   ```

## Estructura del Proyecto

```
f1ChartsFcc/
├── f1ChartsFcc/           # Configuración del proyecto Django
│   ├── __init__.py
│   ├── settings.py        # Configuración de Django
│   ├── urls.py            # Definición de URLs
│   ├── views.py           # Lógica de vistas
│   ├── wsgi.py
│   └── lists/             # Listas de referencia
│       ├── drivers_list.py
│       └── races_list.py
├── templates/             # Plantillas HTML
│   ├── homepage.html
│   ├── laptimes.html
│   ├── comparison.html
│   └── tyre_chart.html
├── media/                 # Archivos generados por la aplicación
│   └── tyre-strat-charts/ # Datos y gráficos de estrategias
├── data-scrapped/         # Datos descargados y procesados
├── cache/                 # Caché de FastF1
├── manage.py
└── requirements.txt
```

## Uso

1. **Página Principal**: Accede a la página principal para ver las opciones disponibles.
2. **Estrategias de Neumáticos**: Selecciona una carrera para ver las estrategias de neumáticos.
3. **Tiempos de Vuelta**: Elige un piloto y una carrera para ver sus tiempos de vuelta.
4. **Comparación**: Selecciona dos pilotos y una carrera para comparar sus tiempos de vuelta.

## Datos

La aplicación utiliza datos de la temporada 2025 de Fórmula 1, obtenidos a través de la API FastF1. Los datos se almacenan en caché para mejorar el rendimiento y reducir las solicitudes a la API.

## Contribuir

Las contribuciones son bienvenidas. Por favor, abre un issue para discutir los cambios importantes antes de enviar un pull request.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## Autor

Fausto Calviño - [@faustocalvinio](https://github.com/faustocalvinio)
