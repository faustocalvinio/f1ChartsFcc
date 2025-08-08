from django.shortcuts import render
import fastf1
import fastf1.plotting
import plotly.graph_objects as go
import plotly.io as pio
import os
import json
import pandas as pd

races_2025 = [
    {"full_name": "Australian Grand Prix", "short_name": "Australia"},
    {"full_name": "Saudi Arabian Grand Prix", "short_name": "Saudi Arabia"},
    {"full_name": "Chinese Grand Prix", "short_name": "China"},
    {"full_name": "Japanese Grand Prix", "short_name": "Japan"},
    {"full_name": "Bahrain Grand Prix", "short_name": "Bahrain"},
    {"full_name": "Miami Grand Prix", "short_name": "Miami"},
    {"full_name": "Emilia Romagna Grand Prix", "short_name": "Emilia Romagna"},
    {"full_name": "Monaco Grand Prix", "short_name": "Monaco"},
    {"full_name": "Canadian Grand Prix", "short_name": "Canada"},
    {"full_name": "Spanish Grand Prix", "short_name": "Spain"},
    {"full_name": "Austrian Grand Prix", "short_name": "Austria"},
    {"full_name": "British Grand Prix", "short_name": "Great Britain"},
    {"full_name": "Hungarian Grand Prix", "short_name": "Hungary"},
    {"full_name": "Belgian Grand Prix", "short_name": "Belgium"},
    {"full_name": "Dutch Grand Prix", "short_name": "Netherlands"},
    {"full_name": "Italian Grand Prix", "short_name": "Italy"},
    {"full_name": "Azerbaijan Grand Prix", "short_name": "Azerbaijan"},
    {"full_name": "Singapore Grand Prix", "short_name": "Singapore"},
    {"full_name": "United States Grand Prix", "short_name": "United States"},
    {"full_name": "Mexican Grand Prix", "short_name": "Mexico"},
    {"full_name": "Brazilian Grand Prix", "short_name": "Brazil"},
    {"full_name": "Las Vegas Grand Prix", "short_name": "Las Vegas"},
    {"full_name": "Qatar Grand Prix", "short_name": "Qatar"},
    {"full_name": "Abu Dhabi Grand Prix", "short_name": "Abu Dhabi"},
]
drivers_2025 = [
    {"name": "Max Verstappen", "shortcode": "VER"},
    {"name": "Liam Lawson", "shortcode": "LAW"},
    {"name": "Lewis Hamilton", "shortcode": "HAM"},
    {"name": "George Russell", "shortcode": "RUS"},
    {"name": "Charles Leclerc", "shortcode": "LEC"},
    {"name": "Andrea Kimi Antonelli", "shortcode": "ANT"},
    {"name": "Lando Norris", "shortcode": "NOR"},
    {"name": "Oscar Piastri", "shortcode": "PIA"},
    {"name": "Fernando Alonso", "shortcode": "ALO"},
    {"name": "Lance Stroll", "shortcode": "STR"},
    {"name": "Esteban Ocon", "shortcode": "OCO"},
    {"name": "Jack Doohan", "shortcode": "DOO"},
    {"name": "Pierre Gasly", "shortcode": "GAS"},
    {"name": "Yuki Tsunoda", "shortcode": "TSU"},
    {"name": "Isack Hadjar", "shortcode": "HAD"},
    {"name": "Alexander Albon", "shortcode": "ALB"},
    {"name": "Carlos Sainz", "shortcode": "SAI"},
    {"name": "Nico Hülkenberg", "shortcode": "HUL"},
    {"name": "Gabriel Bortoleto", "shortcode": "BOR"},
    {"name": "Franco Colapinto", "shortcode": "COL"},
]



def tyre_strategy_chart(request):
    selected_race = request.GET.get('race')
    if not selected_race:
        selected_race = races_2025[0]["full_name"]
    race_obj = next(r for r in races_2025 if r["full_name"] == selected_race)
    race_short = race_obj["short_name"]

    # Ruta para almacenar los datos procesados
    data_dir = "media/tyre-strat-charts"
    os.makedirs(data_dir, exist_ok=True)
    json_path = os.path.join(data_dir, f"2025_{race_short.lower()}_stints.json")

    if os.path.exists(json_path):
        # Leer datos procesados
        with open(json_path, "r", encoding="utf-8") as f:
            chart_data = json.load(f)
    else:
        # Procesar y guardar datos
        session = fastf1.get_session(2025, race_short, 'R')
        session.load(telemetry=False)

        laps = session.laps
        drivers = session.drivers
        drivers = [session.get_driver(driver)["Abbreviation"] for driver in drivers]

        stints = laps[["Driver", "Stint", "Compound", "LapNumber"]]
        stints = stints.groupby(["Driver", "Stint", "Compound"])
        stints = stints.count().reset_index()
        stints = stints.rename(columns={"LapNumber": "StintLength"})

        chart_data = []
        for driver in drivers:
            driver_stints = stints.loc[stints["Driver"] == driver]
            previous_stint_end = 0
            for idx, row in driver_stints.iterrows():
                try:
                    # Manejar el caso 'NONE' o None para los compuestos
                    if row["Compound"] == 'NONE' or pd.isna(row["Compound"]):
                        compound_color = '#888888'  # Color gris para compuestos desconocidos
                    else:
                        compound_color = fastf1.plotting.get_compound_color(row["Compound"], session=session)
                except Exception:
                    # Si hay cualquier error obteniendo el color, usar gris
                    compound_color = '#888888'
                
                chart_data.append({
                    "driver": driver,
                    "stint_length": int(row["StintLength"]),
                    "stint": int(row["Stint"]),
                    "compound": str(row["Compound"]),
                    "base": int(previous_stint_end),
                    "color": compound_color
                })
                previous_stint_end += row["StintLength"]
        # Guardar datos en JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(chart_data, f, ensure_ascii=False)

    # Crear gráfico con Plotly usando los datos guardados
    fig = go.Figure()
    for item in chart_data:
        fig.add_trace(go.Bar(
            y=[item["driver"]],
            x=[item["stint_length"]],
            base=[item["base"]],
            orientation='h',
            marker_color=item["color"],
            name=item["compound"],
            hovertemplate=f"Driver: {item['driver']}<br>Compound: {item['compound']}<br>Stint: {item['stint']}<br>Laps: {item['stint_length']}"
        ))

    fig.update_layout(
        title=f"2025 {race_short} Grand Prix Strategies",
        xaxis_title="Lap Number",
        yaxis_title="Driver",
        barmode='stack',
        height=800,
        width=1400,
        showlegend=True,
        yaxis=dict(autorange='reversed'),
        margin=dict(l=100, r=40, t=80, b=80)
    )

    chart_html = pio.to_html(fig, full_html=False)
    return render(request, "tyre_chart.html", {
        "chart_html": chart_html,
        "races": [r["full_name"] for r in races_2025],
        "selected_race": selected_race
    })

def laptimes_view(request):
    
    driver_names = [f"{d['name']} ({d['shortcode']})" for d in drivers_2025]
    race_names = [r['full_name'] for r in races_2025]

    selected_driver = request.GET.get('driver')
    selected_race = request.GET.get('race')
    laptimes = []

    if selected_driver and selected_race:
        driver_code = selected_driver.split("(")[-1].replace(")", "")
        race_obj = next(r for r in races_2025 if r['full_name'] == selected_race)
        race_short = race_obj['short_name'].replace(" ", "_").lower()
        os.makedirs('cache', exist_ok=True)
        fastf1.Cache.enable_cache('cache')
        os.makedirs('data-scrapped', exist_ok=True)
        outname = f"data-scrapped/{driver_code}_gp_{race_short}_2025.json"

        if os.path.exists(outname):
            with open(outname, "r", encoding="utf-8") as f:
                laptimes = json.load(f)
        else:
            session = fastf1.get_session(2025, selected_race, 'R')
            session.load(telemetry=False)
            laps = session.laps.pick_driver(driver_code)
            laptimes = [
                {"LapNumber": int(row.LapNumber), "LapTime": str(row.LapTime)}
                for idx, row in laps.iterrows()
            ]
            with open(outname, "w", encoding="utf-8") as f:
                json.dump(laptimes, f, ensure_ascii=False)

    return render(request, "laptimes.html", {
        "driver_names": driver_names,
        "race_names": race_names,
        "selected_driver": selected_driver,
        "selected_race": selected_race,
        "laptimes": laptimes
})


def home(request):
    return render(request, "homepage.html")


def comparison_view(request):
    
    driver_names = [f"{d['name']} ({d['shortcode']})" for d in drivers_2025]
    race_names = [r['full_name'] for r in races_2025]

    driver1 = request.GET.get('driver1')
    driver2 = request.GET.get('driver2')
    selected_race = request.GET.get('race')
    laptimes1, laptimes2, diff = [], [], []
    chart_html = None
    avg_delta = None

    if driver1 and driver2 and selected_race:
        code1 = driver1.split("(")[-1].replace(")", "")
        code2 = driver2.split("(")[-1].replace(")", "")
        race_obj = next(r for r in races_2025 if r['full_name'] == selected_race)
        race_short = race_obj['short_name'].replace(" ", "_").lower()
        os.makedirs('cache', exist_ok=True)
        fastf1.Cache.enable_cache('cache')
        os.makedirs('data-scrapped', exist_ok=True)
        file1 = f"data-scrapped/{code1}_gp_{race_short}_2025.json"
        file2 = f"data-scrapped/{code2}_gp_{race_short}_2025.json"

        # Scrape if not exists
        for code, file in [(code1, file1), (code2, file2)]:
            if not os.path.exists(file):
                session = fastf1.get_session(2025, selected_race, 'R')
                session.load(telemetry=False)
                laps = session.laps.pick_driver(code)
                laps_data = [
                    {"LapNumber": int(row.LapNumber), "LapTime": str(row.LapTime)}
                    for idx, row in laps.iterrows()
                ]
                with open(file, "w", encoding="utf-8") as f:
                    json.dump(laps_data, f, ensure_ascii=False)

        # Load laptimes
        with open(file1, "r", encoding="utf-8") as f:
            laptimes1 = json.load(f)
        with open(file2, "r", encoding="utf-8") as f:
            laptimes2 = json.load(f)

        # Calculate differences (soporta formato '0 days 00:01:14.821000')
        import pandas as pd
        laps1 = {lap["LapNumber"]: lap["LapTime"] for lap in laptimes1}
        laps2 = {lap["LapNumber"]: lap["LapTime"] for lap in laptimes2}
        common_laps = sorted(set(laps1.keys()) & set(laps2.keys()))
        diff = []
        for lap in common_laps:
            try:
                t1 = pd.to_timedelta(laps1[lap])
                t2 = pd.to_timedelta(laps2[lap])
                delta = (t1 - t2).total_seconds()
                diff.append({"LapNumber": lap, "Delta": delta})
            except Exception:
                diff.append({"LapNumber": lap, "Delta": None})

        # Calculate avg delta
        valid_deltas = [d["Delta"] for d in diff if d["Delta"] is not None]
        avg_delta = sum(valid_deltas) / len(valid_deltas) if valid_deltas else None

        # Plotly chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[d["LapNumber"] for d in diff],
            y=[d["Delta"] for d in diff],
            mode='lines+markers',
            name='Delta (s)',
            line=dict(color='#ffd369'),
            marker=dict(color='#393e46')
        ))
        fig.update_layout(
            title=f"Diferencia de tiempos por vuelta: {driver1} vs {driver2} ({selected_race})",
            xaxis_title="Lap Number",
            yaxis_title="Delta (s) (positivo = driver1 más lento)",
            template="plotly_dark",
            height=900,
            width=None,  # Se ajusta al ancho del contenedor
            autosize=True,
            yaxis=dict(
                range=[-3, 3],      # muestra hasta ±3.0 s
                dtick=0.1,          # ticks cada 0.1 s
                tickformat=".1f",  # formato 0.1
                zeroline=True,
                zerolinecolor='rgba(255, 211, 105, 0.9)',
                zerolinewidth=2,
                gridcolor='rgba(255,255,255,0.08)'
            ),
            margin=dict(l=80, r=40, t=80, b=80)
        )
        chart_html = pio.to_html(fig, full_html=False)

    return render(request, "comparison.html", {
        "driver_names": driver_names,
        "race_names": race_names,
        "driver1": driver1,
        "driver2": driver2,
        "selected_race": selected_race,
        "chart_html": chart_html,
        "diff": diff,
        "avg_delta": avg_delta
    })