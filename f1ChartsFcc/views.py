from django.shortcuts import render
import fastf1
import fastf1.plotting
import plotly.graph_objects as go
import plotly.io as pio
import os
import json
import pandas as pd
from .lists.races_list import races_2025
from .lists.drivers_list import drivers_2025


def _setup_cache():
    """Initializes cache directory for FastF1."""
    os.makedirs('cache', exist_ok=True)
    fastf1.Cache.enable_cache('cache')


def _extract_driver_code(driver_full_name):
    """Extracts driver shortcode from full name string format 'Name (CODE)'."""
    return driver_full_name.split("(")[-1].replace(")", "")


def _normalize_race_short_name(race_short_name):
    """Normalizes race short name for file paths."""
    return race_short_name.replace(" ", "_").lower()


def _load_or_scrape_lap_data(driver_code, race_name, race_short):
    """Loads lap data from cache or scrapes from FastF1 if not available.
    
    Args:
        driver_code: Driver shortcode (e.g., 'HAM')
        race_name: Full race name (e.g., 'Hungarian Grand Prix')
        race_short: Short race name (e.g., 'Hungary')
    
    Returns:
        List of lap data dictionaries with LapNumber and LapTime
    """
    _setup_cache()
    os.makedirs('data-scrapped', exist_ok=True)
    
    race_short_normalized = _normalize_race_short_name(race_short)
    outname = f"data-scrapped/{driver_code}_gp_{race_short_normalized}_2025.json"
    
    if os.path.exists(outname):
        with open(outname, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # Scrape data
    session = fastf1.get_session(2025, race_name, 'R')
    session.load(telemetry=False)
    laps = session.laps.pick_driver(driver_code)
    
    laps_data = []
    for idx, row in laps.iterrows():
        laps_data.append({
            "LapNumber": int(row.LapNumber),
            "LapTime": _format_lap_time(row.LapTime)
        })
    
    with open(outname, "w", encoding="utf-8") as f:
        json.dump(laps_data, f, ensure_ascii=False)
    
    return laps_data


def _format_lap_time(value):
    """Devuelve el tiempo en formato M:SS.mmm a partir de un Timedelta o string.
    Si no puede parsearse, retorna el string original.
    """
    try:
        td = pd.to_timedelta(value)
        if pd.isna(td):
            return None
        total_ms = int(td.total_seconds() * 1000)
        minutes = total_ms // 60000
        seconds = (total_ms % 60000) // 1000
        millis = total_ms % 1000
        return f"{minutes}:{seconds:02d}.{millis:03d}"
    except Exception:
        return str(value)


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
        height=900,
        width=None,  # se adapta al ancho del contenedor
        autosize=True,
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

def qualy_delta_view(request):
    """Gráfico de diferencias a la pole por piloto (Qualy). Datos cacheados en media/qualy-delta-charts."""
    selected_race = request.GET.get('race')
    if not selected_race:
        selected_race = races_2025[0]["full_name"]
    race_obj = next(r for r in races_2025 if r["full_name"] == selected_race)
    race_short = race_obj["short_name"]

    data_dir = os.path.join("media", "qualy-delta-charts")
    os.makedirs(data_dir, exist_ok=True)
    json_path = os.path.join(data_dir, f"2025_{race_short.lower()}_qualy_delta.json")

    payload = None
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception:
            payload = None

    if payload is None:
        try:
            # Intentar cargar sesión de Qualy
            session = fastf1.get_session(2025, race_short, 'Q')
            session.load(telemetry=False)

            laps = session.laps.dropna(subset=["LapTime"])  # descartar NaT
            if laps.empty:
                raise RuntimeError("Sin laptimes en la sesión de Qualy")

            best_by_driver = laps.groupby("Driver")["LapTime"].min().sort_values()
            pole_driver = best_by_driver.index[0]
            pole_time = best_by_driver.iloc[0]

            data = []
            for drv, t in best_by_driver.items():
                delta = (t - pole_time).total_seconds()
                # Color por equipo si está disponible
                try:
                    drv_info = session.get_driver(drv)
                    team_name = drv_info.get("TeamName")
                    color = fastf1.plotting.get_team_color(team_name) if team_name else "#4b5663"
                except Exception:
                    color = "#4b5663"
                data.append({
                    "driver": drv,
                    "best_lap": _format_lap_time(t),
                    "delta": round(float(delta), 3),
                    "color": color
                })

            payload = {
                "race": selected_race,
                "pole": {"driver": pole_driver, "time": _format_lap_time(pole_time)},
                "data": data
            }

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False)

        except Exception:
            payload = None

    chart_html = None
    error_message = None
    if payload and payload.get("data"):
        try:
            # Construir gráfico
            rows = sorted(payload["data"], key=lambda x: x["delta"])  # orden por delta asc
            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=[r["driver"] for r in rows],
                x=[r["delta"] for r in rows],
                orientation='h',
                marker_color=[r.get("color", "#4b5663") for r in rows],
                hovertemplate="Driver: %{y}<br>Delta: %{x:.3f}s<extra></extra>"
            ))
            pole = payload.get("pole", {})
            fig.update_layout(
                title=f"Qualy Delta vs Pole – {race_short} 2025 (Pole: {pole.get('driver', '-')}, {pole.get('time', '-')})",
                xaxis_title="Delta a la pole (s)",
                yaxis_title="Piloto",
                template="plotly_dark",
                height=800,
                margin=dict(l=100, r=40, t=80, b=60)
            )
            chart_html = pio.to_html(fig, full_html=False)
        except Exception as e:
            error_message = f"No se pudo generar el gráfico: {e}"
    else:
        error_message = "No hay datos de Qualy disponibles para esta carrera (verifica conexión o caché)."

    return render(request, "qualy_delta.html", {
        "chart_html": chart_html,
        "races": [r["full_name"] for r in races_2025],
        "selected_race": selected_race,
        "error_message": error_message
    })

def laptimes_view(request):
    
    driver_names = [f"{d['name']} ({d['shortcode']})" for d in drivers_2025]
    race_names = [r['full_name'] for r in races_2025]

    selected_driver = request.GET.get('driver')
    selected_race = request.GET.get('race')
    laptimes = []

    if selected_driver and selected_race:
        driver_code = _extract_driver_code(selected_driver)
        race_obj = next(r for r in races_2025 if r['full_name'] == selected_race)
        race_short = race_obj['short_name']
        
        laptimes = _load_or_scrape_lap_data(driver_code, selected_race, race_short)
        # Normalizar formato para mostrar sin "0 days"
        for lap in laptimes:
            lap["LapTime"] = _format_lap_time(lap.get("LapTime"))

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
        code1 = _extract_driver_code(driver1)
        code2 = _extract_driver_code(driver2)
        race_obj = next(r for r in races_2025 if r['full_name'] == selected_race)
        race_short = race_obj['short_name']

        # Load or scrape lap data for both drivers
        laptimes1 = _load_or_scrape_lap_data(code1, selected_race, race_short)
        laptimes2 = _load_or_scrape_lap_data(code2, selected_race, race_short)

        # Calculate differences (soporta formato '0 days 00:01:14.821000')
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