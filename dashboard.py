import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd
import warnings
import json
from datetime import datetime
from datetime import timedelta
from datetime import datetime as dt
from pmdarima.arima import auto_arima
from statsmodels.tsa.statespace.sarimax import SARIMAX
from pandas.tseries.offsets import DateOffset
import numpy as np
import pandas as pd
from database import Database


warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.filterwarnings("ignore")
warnings.warn("ValueWarning")
warnings.warn("Do not show this message")

#####################################################################################

db = Database()

db.create_recoveries()
db.create_infection()
db.create_deaths()
db.create_barangay_infection()
db.create_barangay_recoveries()
db.create_barangay_deaths()
db.create_vaccination()
db.create_zones()

len_infection = db.selecting_infection()
len_barangay_infection = db.selecting_barangay_infection()

if len(len_infection) > 0:

    print("Their is data in database ........................................")
    weekly_infection = db.selecting_infection()
    weekly_recoveries = db.selecting_recoveries()
    weekly_deaths = db.selecting_deaths()

    zone_infection_barangay = db.selecting_barangay_infection()
    zone_recoveries_barangay = db.selecting_barangay_recoveries()
    zone_deaths_barangay = db.selecting_barangay_deaths()

    vaccination = db.selecting_vaccination()
    vaccination = vaccination.rename(
        columns={
            "datevaccination": "Date",
            "firstdose": "FirstDose",
            "seconddose": "SecondDose",
            "thirddose": "ThirdDose",
        }
    )
    vaccination["Date"] = pd.to_datetime(vaccination["Date"])

    zone_infection_barangay = zone_infection_barangay.rename(
        columns={
            "dateinfection": "Infection",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )
    zone_recoveries_barangay = zone_recoveries_barangay.rename(
        columns={
            "daterecoveries": "Recoveries",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )
    zone_deaths_barangay = zone_deaths_barangay.rename(
        columns={
            "datedeaths": "Deaths",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )

    zone_infection_barangay["Infection"] = zone_infection_barangay["Infection"].astype(
        str
    )
    zone_recoveries_barangay["Recoveries"] = zone_recoveries_barangay[
        "Recoveries"
    ].astype(str)
    zone_deaths_barangay["Deaths"] = zone_deaths_barangay["Deaths"].astype(str)

    weekly_infection = weekly_infection.rename(
        columns={"dateinfection": "DateInfection", "infection": "Infection"}
    )
    weekly_recoveries = weekly_recoveries.rename(
        columns={"daterecoveries": "DateRecoveries", "recoveries": "Recoveries"}
    )
    weekly_deaths = weekly_deaths.rename(
        columns={"datedeaths": "DateDeaths", "deaths": "Deaths"}
    )

    weekly_recoveries["DateRecoveries"] = pd.to_datetime(
        weekly_recoveries["DateRecoveries"]
    )
    weekly_infection["DateInfection"] = pd.to_datetime(
        weekly_infection["DateInfection"]
    )
    weekly_deaths["DateDeaths"] = pd.to_datetime(weekly_deaths["DateDeaths"])

    weekly_deaths.set_index("DateDeaths", inplace=True)
    weekly_recoveries.set_index("DateRecoveries", inplace=True)
    weekly_infection.set_index("DateInfection", inplace=True)
    vaccination.set_index("Date", inplace=True)

    weekly_vaccination = (
        vaccination[["FirstDose", "SecondDose", "ThirdDose"]].resample("W").sum()
    )
    weekly_vaccination = weekly_vaccination.reset_index()
    weekly_vaccination["Year"] = weekly_vaccination["Date"].apply(
        lambda x: str(x).split("-")[0]
    )
    weekly_vaccination["Date"] = pd.to_datetime(weekly_vaccination["Date"])
    weekly_vaccination["months"] = weekly_vaccination["Date"].dt.month_name()
    vaccination_year = weekly_vaccination["Year"].unique()

    vaccination_month = weekly_vaccination["months"].unique()
    vaccination_month = vaccination_month = sorted(
        vaccination_month, key=lambda m: datetime.strptime(m, "%B")
    )
    vaccination_month.append("All")

    raw_data_deaths = weekly_deaths["Deaths"].resample("W").sum()
    raw_data_recoveries = weekly_recoveries["Recoveries"].resample("W").sum()
    raw_data_infection = weekly_infection["Infection"].resample("W").sum()

    raw_data_weekly_deaths = raw_data_deaths.reset_index()
    raw_data_weekly_recoveries = raw_data_recoveries.reset_index()
    raw_data_weekly_infection = raw_data_infection.reset_index()

    raw_data_weekly_infection = raw_data_weekly_infection.rename(
        columns={"DateInfection": "Date"}
    )
    raw_data_weekly_recoveries = raw_data_weekly_recoveries.rename(
        columns={"DateRecoveries": "Date"}
    )
    raw_data_weekly_deaths = raw_data_weekly_deaths.rename(
        columns={"DateDeaths": "Date"}
    )

    df_infection_recoveries_deaths = pd.concat(
        [raw_data_weekly_infection, raw_data_weekly_recoveries, raw_data_weekly_deaths]
    )

    df_infection_recoveries_deaths = df_infection_recoveries_deaths.fillna(0)

    covid_data_weekly = (
        df_infection_recoveries_deaths.groupby(["Date"])[
            ["Infection", "Recoveries", "Deaths"]
        ]
        .sum()
        .reset_index()
    )

    total_recoveries = covid_data_weekly["Recoveries"].sum()
    total_infection = covid_data_weekly["Infection"].sum()
    _total_deaths = covid_data_weekly["Deaths"].sum()

    male_female = ["Male", "Female", "All"]
    age_range = [
        "1-10 Years Old",
        "11-20 Years Old",
        "21-30 Years Old",
        "31-40 Years Old",
        "41-50 Years Old",
        "51-60 Years Old",
        "61-70 Years Old",
        "71-80 Years Old",
        "81-90 Years Old",
    ]

    person_age_range = []
    zone_age_range = []
    demo_age_range = []
    person_demo_age_range = []
    sql_operation = ["Insert", "Update"]

    covid_19_cases = ["Infection", "Recoveries", "Deaths"]
    last_update_cases = str(covid_data_weekly["Date"].iloc[-1]).split(" ")
    
    zone_data = db.selecting_zones()
    zones = list(zone_data["zone"].unique())
    zone_data = zone_data.rename(columns={"zone":"Zone", "male":"Male", "female":"Female"})
    vaccination_doses = ["1st Dose", "2nd Dose", "3rd Dose"]

    def convertion_date(max_date):
        date_format_str = "%Y-%m-%d"
        timestamp = str(max_date)
        given_time = datetime.strptime(timestamp, date_format_str)
        final_convertion_time = given_time.strftime("%B %d, %Y")

        return final_convertion_time

    raw_data_weekly_infection["Date"] = raw_data_weekly_infection["Date"].astype(str)
    raw_data_weekly_recoveries["Date"] = raw_data_weekly_recoveries["Date"].astype(str)
    raw_data_weekly_deaths["Date"] = raw_data_weekly_deaths["Date"].astype(str)
    latest_infection = str(convertion_date(max(raw_data_weekly_infection["Date"])))
    latest_recoveries = str(convertion_date(max(raw_data_weekly_recoveries["Date"])))
    latest_deaths = str(convertion_date(max(raw_data_weekly_deaths["Date"])))

    covid_data_weekly["Date"] = pd.to_datetime(covid_data_weekly["Date"])
    raw_data_weekly_infection["Date"] = pd.to_datetime(
        raw_data_weekly_infection["Date"]
    )
    raw_data_weekly_recoveries["Date"] = pd.to_datetime(
        raw_data_weekly_recoveries["Date"]
    )
    raw_data_weekly_deaths["Date"] = pd.to_datetime(raw_data_weekly_deaths["Date"])

else:

    print("creating ..............................................")
    weekly_recoveries_deaths_infection = pd.read_csv(
        "Cases.csv",
        parse_dates=["daterecoveries", "datedeaths", "dateinfection"],
        encoding="latin-1",
    )

    weekly_infection_df = weekly_recoveries_deaths_infection[
        ["dateinfection", "infection"]
    ]
    weekly_recoveries_df = weekly_recoveries_deaths_infection[
        ["daterecoveries", "recoveries"]
    ]
    weekly_deaths_df = weekly_recoveries_deaths_infection[["datedeaths", "deaths"]]

    weekly_infection_df = weekly_infection_df.dropna(subset=["infection"])
    weekly_recoveries_df = weekly_recoveries_df.dropna(subset=["recoveries"])
    weekly_deaths_df = weekly_deaths_df.dropna(subset=["deaths"])

    weekly_infection_df["infection"] = weekly_infection_df["infection"].astype(int)
    weekly_recoveries_df["recoveries"] = weekly_recoveries_df["recoveries"].astype(int)
    weekly_deaths_df["deaths"] = weekly_deaths_df["deaths"].astype(int)

    db.insert_infection(weekly_infection_df)
    db.insert_recoveries(weekly_recoveries_df)
    db.insert_deaths(weekly_deaths_df)

    zones_infection_recoveries_deaths = pd.read_csv(
        "carmen_zones.csv",
        parse_dates=["Infection", "Deaths", "Recoveries"],
        encoding="latin-1",
    )
    zones_infection_recoveries_deaths = zones_infection_recoveries_deaths.rename(
        columns={
            "Infection": "dateinfection",
            "Age": "age",
            "Sex": "gender",
            "Recoveries": "daterecoveries",
            "Deaths": "datedeaths",
            "Zones": "zones",
            "Address": "address",
        }
    )

    zones_infection_barangay = zones_infection_recoveries_deaths[
        ["dateinfection", "age", "gender", "zones", "address"]
    ]
    zones_recoveries_barangay = zones_infection_recoveries_deaths[
        ["daterecoveries", "age", "gender", "zones", "address"]
    ]
    zones_deaths_barangay = zones_infection_recoveries_deaths[
        ["datedeaths", "age", "gender", "zones", "address"]
    ]

    zones_deaths_barangay = zones_deaths_barangay.dropna(subset=["datedeaths"])
    zones_infection_barangay = zones_infection_barangay.dropna(subset=["dateinfection"])
    zones_recoveries_barangay = zones_recoveries_barangay.dropna(
        subset=["daterecoveries"]
    )

    db.insert_create_barangay_infection(zones_infection_barangay)
    db.insert_create_barangay_recoveries(zones_recoveries_barangay)
    db.insert_create_barangay_deaths(zones_deaths_barangay)

    weekly_vaccination = pd.read_csv(
        "Vaccinations.csv", parse_dates=["Date"], encoding="latin-1"
    )

    weekly_vaccination["FirstDose"] = weekly_vaccination["FirstDose"].astype(int)

    weekly_vaccination["SecondDose"] = weekly_vaccination["SecondDose"].astype(int)

    weekly_vaccination["ThirdDose"] = weekly_vaccination["ThirdDose"].astype(int)

    weekly_vaccination = weekly_vaccination.rename(
        columns={
            "Date": "datevaccination",
            "FirstDose": "firstdose",
            "SecondDose": "seconddose",
            "ThirdDose": "thirddose",
        }
    )

    db.insert_vaccination(weekly_vaccination)

    
    data_zone = pd.read_csv("zone.csv", encoding="latin-1")
    db.insert_zones(data_zone)

    weekly_infection = db.selecting_infection()
    weekly_recoveries = db.selecting_recoveries()
    weekly_deaths = db.selecting_deaths()

    zone_infection_barangay = db.selecting_barangay_infection()
    zone_recoveries_barangay = db.selecting_barangay_recoveries()
    zone_deaths_barangay = db.selecting_barangay_deaths()

    vaccination = db.selecting_vaccination()
    vaccination = vaccination.rename(
        columns={
            "datevaccination": "Date",
            "firstdose": "FirstDose",
            "seconddose": "SecondDose",
            "thirddose": "ThirdDose",
        }
    )
    vaccination["Date"] = pd.to_datetime(vaccination["Date"])

    zone_infection_barangay = zone_infection_barangay.rename(
        columns={
            "dateinfection": "Infection",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )
    zone_recoveries_barangay = zone_recoveries_barangay.rename(
        columns={
            "daterecoveries": "Recoveries",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )
    zone_deaths_barangay = zone_deaths_barangay.rename(
        columns={
            "datedeaths": "Deaths",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )

    zone_infection_barangay["Infection"] = zone_infection_barangay["Infection"].astype(
        str
    )
    zone_recoveries_barangay["Recoveries"] = zone_recoveries_barangay[
        "Recoveries"
    ].astype(str)
    zone_deaths_barangay["Deaths"] = zone_deaths_barangay["Deaths"].astype(str)

    weekly_infection = weekly_infection.rename(
        columns={"dateinfection": "DateInfection", "infection": "Infection"}
    )
    weekly_recoveries = weekly_recoveries.rename(
        columns={"daterecoveries": "DateRecoveries", "recoveries": "Recoveries"}
    )
    weekly_deaths = weekly_deaths.rename(
        columns={"datedeaths": "DateDeaths", "deaths": "Deaths"}
    )

    weekly_recoveries["DateRecoveries"] = pd.to_datetime(
        weekly_recoveries["DateRecoveries"]
    )
    weekly_infection["DateInfection"] = pd.to_datetime(
        weekly_infection["DateInfection"]
    )
    weekly_deaths["DateDeaths"] = pd.to_datetime(weekly_deaths["DateDeaths"])

    weekly_deaths.set_index("DateDeaths", inplace=True)
    weekly_recoveries.set_index("DateRecoveries", inplace=True)
    weekly_infection.set_index("DateInfection", inplace=True)
    vaccination.set_index("Date", inplace=True)

    weekly_vaccination = (
        vaccination[["FirstDose", "SecondDose", "ThirdDose"]].resample("W").sum()
    )
    weekly_vaccination = weekly_vaccination.reset_index()
    weekly_vaccination["Year"] = weekly_vaccination["Date"].apply(
        lambda x: str(x).split("-")[0]
    )
    weekly_vaccination["Date"] = pd.to_datetime(weekly_vaccination["Date"])
    weekly_vaccination["months"] = weekly_vaccination["Date"].dt.month_name()
    vaccination_year = weekly_vaccination["Year"].unique()

    vaccination_month = weekly_vaccination["months"].unique()
    vaccination_month = vaccination_month = sorted(
        vaccination_month, key=lambda m: datetime.strptime(m, "%B")
    )
    vaccination_month.append("All")

    raw_data_deaths = weekly_deaths["Deaths"].resample("W").sum()
    raw_data_recoveries = weekly_recoveries["Recoveries"].resample("W").sum()
    raw_data_infection = weekly_infection["Infection"].resample("W").sum()

    raw_data_weekly_deaths = raw_data_deaths.reset_index()
    raw_data_weekly_recoveries = raw_data_recoveries.reset_index()
    raw_data_weekly_infection = raw_data_infection.reset_index()

    raw_data_weekly_infection = raw_data_weekly_infection.rename(
        columns={"DateInfection": "Date"}
    )
    raw_data_weekly_recoveries = raw_data_weekly_recoveries.rename(
        columns={"DateRecoveries": "Date"}
    )
    raw_data_weekly_deaths = raw_data_weekly_deaths.rename(
        columns={"DateDeaths": "Date"}
    )

    df_infection_recoveries_deaths = pd.concat(
        [raw_data_weekly_infection, raw_data_weekly_recoveries, raw_data_weekly_deaths]
    )

    df_infection_recoveries_deaths = df_infection_recoveries_deaths.fillna(0)

    covid_data_weekly = (
        df_infection_recoveries_deaths.groupby(["Date"])[
            ["Infection", "Recoveries", "Deaths"]
        ]
        .sum()
        .reset_index()
    )

    total_recoveries = covid_data_weekly["Recoveries"].sum()
    total_infection = covid_data_weekly["Infection"].sum()
    _total_deaths = covid_data_weekly["Deaths"].sum()
    
    zone_data = db.selecting_zones()
    zones = list(zone_data["zone"].unique())

    zone_data = zone_data.rename(columns={"zone":"Zone", "male":"Male", "female":"Female"})

    male_female = ["Male", "Female", "All"]
    age_range = [
        "1-10 Years Old",
        "11-20 Years Old",
        "21-30 Years Old",
        "31-40 Years Old",
        "41-50 Years Old",
        "51-60 Years Old",
        "61-70 Years Old",
        "71-80 Years Old",
        "81-90 Years Old",
    ]

    person_age_range = []
    zone_age_range = []
    demo_age_range = []
    person_demo_age_range = []

    covid_19_cases = ["Infection", "Recoveries", "Deaths"]
    last_update_cases = str(covid_data_weekly["Date"].iloc[-1]).split(" ")
    vaccination_doses = ["1st Dose", "2nd Dose", "3rd Dose"]

    def convertion_date(max_date):
        date_format_str = "%Y-%m-%d"
        timestamp = str(max_date)
        given_time = datetime.strptime(timestamp, date_format_str)
        final_convertion_time = given_time.strftime("%B %d, %Y")

        return final_convertion_time

    raw_data_weekly_infection["Date"] = raw_data_weekly_infection["Date"].astype(str)
    raw_data_weekly_recoveries["Date"] = raw_data_weekly_recoveries["Date"].astype(str)
    raw_data_weekly_deaths["Date"] = raw_data_weekly_deaths["Date"].astype(str)
    latest_infection = str(convertion_date(max(raw_data_weekly_infection["Date"])))
    latest_recoveries = str(convertion_date(max(raw_data_weekly_recoveries["Date"])))
    latest_deaths = str(convertion_date(max(raw_data_weekly_deaths["Date"])))

    covid_data_weekly["Date"] = pd.to_datetime(covid_data_weekly["Date"])
    raw_data_weekly_infection["Date"] = pd.to_datetime(
        raw_data_weekly_infection["Date"]
    )
    raw_data_weekly_recoveries["Date"] = pd.to_datetime(
        raw_data_weekly_recoveries["Date"]
    )
    raw_data_weekly_deaths["Date"] = pd.to_datetime(raw_data_weekly_deaths["Date"])


app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}]
)

app.index_string = '''<!DOCTYPE html>
<html>
<head>
<title>My app title</title>
<link rel="manifest" href="./assets/manifest.json" />
{%metas%}
{%favicon%}
{%css%}
</head>
<script type="module">
    import 'https://cdn.jsdelivr.net/npm/@pwabuilder/pwaupdate';
    const el = document.createElement('pwa-update');
    document.body.appendChild(el);
</script>
<body>
<script>
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', ()=> {
        navigator
        .serviceWorker
        .register('./assets/sw01.js')
        .then(()=>console.log("Ready."))
        .catch(()=>console.log("Err..."));
        });
    }
</script>
{%app_entry%}
<footer>
{%config%}
{%scripts%}
{%renderer%}
</footer>
</body>
</html>
'''

server = app.server

app.layout = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        html.Img(
                            src=app.get_asset_url("corona-logo-1.jpg"),
                            id="corona-image",
                            style={
                                "height": "60px",
                                "width": "auto",
                                "margin-bottom": "25px",
                            },
                        )
                    ],
                    className="one-third column",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.H3(
                                    "Barangay Carmen Covid - 19",
                                    style={
                                        "margin-bottom": "0px",
                                        "color": "white",
                                        "font-weight": "bold",
                                        "letter-spacing": "0.5px",
                                    },
                                ),
                                html.H5(
                                    "Track Covid - 19 Cases",
                                    style={
                                        "margin-top": "0px",
                                        "color": "white",
                                        "font-weight": "bold",
                                        "letter-spacing": "0.5px",
                                    },
                                ),
                            ]
                        )
                    ],
                    className="one-half column",
                    id="title",
                ),
                html.Div(
                    [
                        html.H6(
                            "Last Updated: "
                            + str(convertion_date(last_update_cases[0]))
                            + "  00:01 (UTC)",
                            style={"color": "orange"},
                        ),
                    ],
                    className="one-third column",
                    id="title1",
                ),
            ],
            id="header",
            className="row flex-display",
            style={"margin-bottom": "25px"},
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.H6(
                            children="Infection Cases",
                            style={
                                "textAlign": "center",
                                "color": "white",
                                "font-weight": "bold",
                                "letter-spacing": "0.5px",
                            },
                        ),
                        html.P(
                            id="total_cases_infection",
                            style={
                                "textAlign": "center",
                                "color": "orange",
                                "fontSize": 40,
                            },
                        ),
                        html.P(
                            id="total_cases_infection_update",
                            style={
                                "textAlign": "center",
                                "color": "orange",
                                "fontSize": 15,
                                "margin-top": "-18px",
                            },
                        ),
                        html.P(
                            id="infection_latest_update",
                            style={
                                "textAlign": "center",
                                "color": "orange",
                                "fontSize": 15,
                                "margin-top": "-10px",
                            },
                        ),
                    ],
                    className="card_container three columns",
                ),
                html.Div(
                    [
                        html.H6(
                            children="Recoveries Cases",
                            style={
                                "textAlign": "center",
                                "color": "white",
                                "font-weight": "bold",
                                "letter-spacing": "0.5px",
                            },
                        ),
                        html.P(
                            id="total_cases_recoveries",
                            style={
                                "textAlign": "center",
                                "color": "green",
                                "fontSize": 40,
                            },
                        ),
                        html.P(
                            id="total_cases_recoveries_update",
                            style={
                                "textAlign": "center",
                                "color": "green",
                                "fontSize": 15,
                                "margin-top": "-18px",
                            },
                        ),
                        html.P(
                            id="recoveries_latest_update",
                            style={
                                "textAlign": "center",
                                "color": "green",
                                "fontSize": 15,
                                "margin-top": "-10px",
                            },
                        ),
                    ],
                    className="card_container three columns",
                ),
                html.Div(
                    [
                        html.H6(
                            children="Death Cases",
                            style={
                                "textAlign": "center",
                                "color": "white",
                                "font-weight": "bold",
                                "letter-spacing": "0.5px",
                            },
                        ),
                        html.P(
                            id="total_cases_deaths",
                            style={
                                "textAlign": "center",
                                "color": "#dd1e35",
                                "fontSize": 40,
                            },
                        ),
                        html.P(
                            id="total_cases_deaths_update",
                            style={
                                "textAlign": "center",
                                "color": "#dd1e35",
                                "fontSize": 15,
                                "margin-top": "-18px",
                            },
                        ),
                        html.P(
                            id="deaths_latest_update",
                            style={
                                "textAlign": "center",
                                "color": "#dd1e35",
                                "fontSize": 15,
                                "margin-top": "-10px",
                            },
                        ),
                        dcc.Interval(
                            id="interval-component",
                            interval=5 * 1000,  # in milliseconds
                            n_intervals=2,
                        ),
                    ],
                    className="card_container three columns",
                ),
            ],
            className="row flex-display1",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.P(
                            "Select Zones:",
                            className="fix_label",
                            style={
                                "color": "white",
                                "font-weight": "bold",
                                "letter-spacing": "1px",
                            },
                        ),
                        dcc.Dropdown(
                            id="zones_barangay",
                            multi=False,
                            clearable=False,
                            value="Zone 1",
                            placeholder="Select Zones",
                            options=[{"label": zone, "value": zone} for zone in zones],
                            className="dcc_compon",
                        ),
                        dcc.Dropdown(
                            id="zone_gender",
                            multi=False,
                            clearable=False,
                            value="Male",
                            placeholder="Select Gender",
                            options=[
                                {"label": gender, "value": gender}
                                for gender in male_female
                            ],
                            className="dcc_compon",
                        ),
                        html.P(
                            id="zone_date_title",
                            className="fix_label",
                            style={"color": "white", "text-align": "center"},
                        ),
                        dcc.Graph(
                            id="infection_zone",
                            config={"displayModeBar": False},
                            className="dcc_compon",
                            style={"margin-top": "20px"},
                        ),
                        html.P(
                            id="infection_zone_title",
                            className="fix_label",
                            style={
                                "color": "white",
                                "text-align": "center",
                                "margin-top": "-20px",
                            },
                        ),
                        dcc.Graph(
                            id="recoveries_zone",
                            config={"displayModeBar": False},
                            className="dcc_compon",
                            style={"margin-top": "20px"},
                        ),
                        html.P(
                            id="recoveries_zone_title",
                            className="fix_label",
                            style={
                                "color": "white",
                                "text-align": "center",
                                "margin-top": "-20px",
                            },
                        ),
                        dcc.Graph(
                            id="deaths_zone",
                            config={"displayModeBar": False},
                            className="dcc_compon",
                            style={"margin-top": "20px"},
                        ),
                        html.P(
                            id="death_zone_title",
                            className="fix_label",
                            style={
                                "color": "white",
                                "text-align": "center",
                                "margin-top": "-20px",
                            },
                        ),
                    ],
                    className="create_container three columns",
                    id="cross-filter-option1",
                ),
                html.Div(
                    [
                        dcc.Graph(
                            id="zone_pie_chart",
                            config={"displayModeBar": "hover"},
                            style={"font-weight": "bold", "letter-spacing": "1px"},
                        ),
                    ],
                    className="create_container four columns",
                ),
                html.Div(
                    [
                        dcc.Graph(
                            id="zone_line_chart",
                            style={"font-weight": "bold", "letter-spacing": "1px"},
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                dcc.Dropdown(
                                                    id="zone_cases",
                                                    multi=False,
                                                    clearable=False,
                                                    value="Infection",
                                                    placeholder="Select Cases",
                                                    options=[
                                                        {"label": cases, "value": cases}
                                                        for cases in covid_19_cases
                                                    ],
                                                    className="drop_down dcc_compon",
                                                ),
                                            ],
                                            className="dropdown",
                                        ),
                                        html.Div(
                                            [
                                                dcc.Input(
                                                    id="case_population",
                                                    type="text",
                                                    readOnly=True,
                                                    disabled=True,
                                                    placeholder="Total Cases",
                                                    className="input_population",
                                                    style={"border": "2px solid green"},
                                                ),
                                                dcc.Input(
                                                    id="zone_population",
                                                    type="text",
                                                    readOnly=True,
                                                    disabled=True,
                                                    placeholder="Population",
                                                    className="input_population",
                                                    style={"border": "2px solid green"},
                                                ),
                                            ],
                                            className="search_field",
                                        ),
                                    ],
                                    className="search_box",
                                )
                            ],
                            className="wrapper",
                        ),
                    ],
                    className="create_container five columns",
                ),
            ],
            className="row flex-display",
            style={"margin-bottom": "50px"},
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.P(
                            "Select Barangay:",
                            className="fix_label",
                            style={
                                "color": "white",
                                "font-weight": "bold",
                                "letter-spacing": "1px",
                            },
                        ),
                        dcc.Dropdown(
                            id="barangay",
                            multi=False,
                            clearable=False,
                            value="Max Suniel Street",
                            placeholder="Select Barangay",
                            className="dcc_compon",
                        ),
                        dcc.Dropdown(
                            id="gender",
                            multi=False,
                            clearable=False,
                            value="Male",
                            placeholder="Select Gender",
                            options=[
                                {"label": gender, "value": gender}
                                for gender in male_female
                            ],
                            className="dcc_compon",
                        ),
                        html.P(
                            id="date_title",
                            className="fix_label",
                            style={"color": "white", "text-align": "center"},
                        ),
                        dcc.Graph(
                            id="infection_barangay",
                            config={"displayModeBar": False},
                            className="dcc_compon",
                            style={"margin-top": "20px"},
                        ),
                        html.P(
                            id="infection_barangay_title",
                            className="fix_label",
                            style={
                                "color": "white",
                                "text-align": "center",
                                "margin-top": "-20px",
                            },
                        ),
                        dcc.Graph(
                            id="recoveries_barangay",
                            config={"displayModeBar": False},
                            className="dcc_compon",
                            style={"margin-top": "20px"},
                        ),
                        html.P(
                            id="recoveries_barangay_title",
                            className="fix_label",
                            style={
                                "color": "white",
                                "text-align": "center",
                                "margin-top": "-20px",
                            },
                        ),
                        dcc.Graph(
                            id="deaths_barangay",
                            config={"displayModeBar": False},
                            className="dcc_compon",
                            style={"margin-top": "20px"},
                        ),
                        html.P(
                            id="deaths_barangay_title",
                            className="fix_label",
                            style={
                                "color": "white",
                                "text-align": "center",
                                "margin-top": "-20px",
                            },
                        ),
                    ],
                    className="create_container three columns",
                    id="cross-filter-options",
                ),
                html.Div(
                    [
                        dcc.Graph(
                            id="pie_chart",
                            config={"displayModeBar": "hover"},
                            style={
                                "color": "white",
                                "font-weight": "bold",
                                "letter-spacing": "1px",
                            },
                        ),
                    ],
                    className="create_container four columns",
                ),
                html.Div(
                    [
                        dcc.Graph(
                            id="line_chart",
                            style={
                                "color": "white",
                                "font-weight": "bold",
                                "letter-spacing": "1px",
                            },
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                dcc.Dropdown(
                                                    id="cases",
                                                    multi=False,
                                                    clearable=False,
                                                    value="Infection",
                                                    placeholder="Select Cases",
                                                    options=[
                                                        {"label": case, "value": case}
                                                        for case in covid_19_cases
                                                    ],
                                                    className="drop_down dcc_compon",
                                                ),
                                            ],
                                            className="dropdown",
                                        ),
                                        html.Div(
                                            [
                                                dcc.Input(
                                                    id="barangay_case_population",
                                                    type="text",
                                                    readOnly=True,
                                                    disabled=True,
                                                    placeholder="Total Cases",
                                                    className="input_population",
                                                    style={"border": "2px solid green"},
                                                ),
                                            ],
                                            className="search_field",
                                        ),
                                    ],
                                    className="search_box",
                                )
                            ],
                            className="wrapper",
                        ),
                    ],
                    className="create_container five columns",
                ),
            ],
            className="row flex-display",
            style={"margin-bottom": "50px"},
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.P(
                            "Select Demographic:",
                            className="fix_label",
                            style={
                                "color": "white",
                                "font-weight": "bold",
                                "letter-spacing": "1px",
                            },
                        ),
                        dcc.Dropdown(
                            id="demo_age",
                            multi=False,
                            clearable=False,
                            value="1-10 Years Old",
                            placeholder="Select Age Range",
                            options=[{"label": age, "value": age} for age in age_range],
                            className="dcc_compon",
                        ),
                        dcc.Dropdown(
                            id="demo_gender",
                            multi=False,
                            clearable=False,
                            value="Male",
                            placeholder="Select Gender",
                            options=[
                                {"label": gender, "value": gender}
                                for gender in male_female
                            ],
                            className="dcc_compon",
                        ),
                        dcc.Graph(
                            id="confirmed",
                            config={"displayModeBar": False},
                            className="dcc_compon",
                            style={"margin-top": "20px"},
                        ),
                        dcc.Graph(
                            id="recoveries",
                            config={"displayModeBar": False},
                            className="dcc_compon",
                            style={"margin-top": "20px"},
                        ),
                        dcc.Graph(
                            id="deaths",
                            config={"displayModeBar": False},
                            className="dcc_compon",
                            style={"margin-top": "20px"},
                        ),
                    ],
                    className="create_container three columns",
                    id="cross-filter-option",
                ),  # 30.6666666667%
                html.Div(
                    [
                        dcc.Graph(
                            id="demo_pie_chart",
                            config={"displayModeBar": "hover"},
                            style={
                                "color": "white",
                                "font-weight": "bold",
                                "letter-spacing": "1px",
                            },
                        ),
                    ],
                    className="create_container four columns",
                ),
                html.Div(
                    [
                        dcc.Graph(
                            id="demo_line_chart",
                            style={
                                "color": "white",
                                "font-weight": "bold",
                                "letter-spacing": "1px",
                            },
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                dcc.Dropdown(
                                                    id="demo_cases",
                                                    multi=False,
                                                    clearable=False,
                                                    value="Infection",
                                                    placeholder="Select Cases",
                                                    options=[
                                                        {"label": case, "value": case}
                                                        for case in covid_19_cases
                                                    ],
                                                    style={"width":"80% !important"},
                                                    className="drop_down dcc_compon",
                                                ),
                                            ],
                                            className="dropdown",
                                        ),
                                        html.Div(
                                            [
                                                dcc.Input(
                                                    id="demo_case_population",
                                                    type="text",
                                                    readOnly=True,
                                                    disabled=True,
                                                    placeholder="Total Cases",
                                                    className="input_population",
                                                    style={"border": "2px solid green"},
                                                ),
                                            ],
                                            className="search_field",
                                        ),
                                    ],
                                    className="search_box",
                                )
                            ],
                            className="wrapper",
                        ),
                    ],
                    className="create_container five columns",
                ),
            ],
            className="row flex-display",
            style={"margin-bottom": "50px"},
        ),
        html.Div(
            [
                html.Div(
                    [
                        dcc.Graph(
                            id="line_chart_weekly_infection",
                            style={
                                "color": "white",
                                "font-weight": "bold",
                                "letter-spacing": "0.5px",
                            },
                        ),
                    ],
                    className="create_container seven columns",
                ),
                html.Div(
                    [
                        dcc.Graph(
                            id="line_chart_weekly_recoveries",
                            style={
                                "color": "white",
                                "font-weight": "bold",
                                "letter-spacing": "0.5px",
                            },
                        ),
                    ],
                    className="create_container seven columns",
                ),
            ],
            className="row flex-diplay",
            style={
                "align-items": "center",
                "justify-content": "center",
                "display": "flex",
            },
        ),
        html.Div(
            [
                html.Div(
                    [
                        dcc.Graph(
                            id="line_chart_weekly_vaccination",
                            style={
                                "color": "white",
                                "font-weight": "bold",
                                "letter-spacing": "0.5px",
                            },
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                dcc.Dropdown(
                                                    id="vaccination_dose",
                                                    multi=False,
                                                    clearable=False,
                                                    value="1st Dose",
                                                    placeholder="Select Doses",
                                                    options=[
                                                        {"label": dose, "value": dose}
                                                        for dose in vaccination_doses
                                                    ],
                                                    className="drop_down dcc_compon",
                                                ),
                                                dcc.Dropdown(
                                                    id="year_vaccination",
                                                    multi=False,
                                                    clearable=False,
                                                    value="2021",
                                                    placeholder="Select Year",
                                                    options=[
                                                        {"label": year, "value": year}
                                                        for year in vaccination_year
                                                    ],
                                                    className="drop_down dcc_compon",
                                                ),
                                                dcc.Dropdown(
                                                    id="month_vaccination",
                                                    multi=False,
                                                    clearable=False,
                                                    value="January",
                                                    placeholder="Select Month",
                                                    options=[
                                                        {"label": month, "value": month}
                                                        for month in vaccination_month
                                                    ],
                                                    className="drop_down dcc_compon",
                                                ),
                                            ],
                                            className="dropdown_vaccination",
                                        ),
                                        html.Div(
                                            [
                                                dcc.Input(
                                                    id="doses",
                                                    type="text",
                                                    readOnly=True,
                                                    disabled=True,
                                                    placeholder="Doses",
                                                    className="input_population",
                                                    style={"border": "2px solid green"},
                                                ),
                                                dcc.Input(
                                                    id="input_year",
                                                    type="text",
                                                    readOnly=True,
                                                    disabled=True,
                                                    placeholder="Year",
                                                    className="input_population",
                                                    style={
                                                        "border": "2px solid green",
                                                        "margin-top": "10px",
                                                    },
                                                ),
                                                dcc.Input(
                                                    id="input_month",
                                                    type="text",
                                                    readOnly=True,
                                                    disabled=True,
                                                    placeholder="Month",
                                                    className="input_population",
                                                    style={
                                                        "border": "2px solid green",
                                                        "margin-top": "10px",
                                                    },
                                                ),
                                            ],
                                            className="search_field",
                                        ),
                                    ],
                                    className="search_box_vaccination",
                                )
                            ],
                            className="wrapper",
                        ),
                    ],
                    className="create_container eleven columns",
                ),
            ],
            className="row flex-diplay",
            style={
                "align-items": "center",
                "justify-content": "center",
                "display": "flex",
            },
        ),
    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)


@app.callback(
    Output("total_cases_infection", "children"),
    [Input("interval-component", "n_intervals")],
)
def update_total_cases(n):
    infection_dataframe = db.selecting_infection()
    total_infection_cases = infection_dataframe["infection"].sum()
    convert_string = str(total_infection_cases)

    return convert_string


@app.callback(
    Output("total_cases_recoveries", "children"),
    [Input("interval-component", "n_intervals")],
)
def update_total_cases(n):
    recoveries_dataframe = db.selecting_recoveries()
    total_recoveries_cases = recoveries_dataframe["recoveries"].sum()
    convert_string = str(total_recoveries_cases)

    return convert_string


@app.callback(
    Output("total_cases_deaths", "children"),
    [Input("interval-component", "n_intervals")],
)
def update_total_cases(n):
    deaths_dataframe = db.selecting_deaths()
    total_deaths_cases = deaths_dataframe["deaths"].sum()
    convert_string = str(total_deaths_cases)

    return convert_string


@app.callback(
    Output("total_cases_infection_update", "children"),
    [Input("interval-component", "n_intervals")],
)
def update_total_cases(n):
    weekly_infection = db.selecting_infection()
    weekly_infection = weekly_infection.rename(
        columns={"dateinfection": "DateInfection", "infection": "Infection"}
    )
    weekly_infection["DateInfection"] = pd.to_datetime(
        weekly_infection["DateInfection"]
    )
    weekly_infection.set_index("DateInfection", inplace=True)

    raw_data_infection = weekly_infection["Infection"].resample("W").sum()
    raw_data_weekly_infection = raw_data_infection.reset_index()
    total_infection = raw_data_weekly_infection["Infection"].sum()

    py_int1 = total_infection.item()
    py_int2 = raw_data_weekly_infection["Infection"].iloc[-1].item()

    latest_percentage = str(
        round(((py_int1 - (py_int1 - py_int2)) / py_int1) * 100, 2,)
    )
    statement = "new:  " + str(py_int2) + " (" + latest_percentage + "%)"

    return statement


@app.callback(
    Output("total_cases_recoveries_update", "children"),
    [Input("interval-component", "n_intervals")],
)
def update_total_cases(n):
    weekly_recoveries = db.selecting_recoveries()
    weekly_recoveries = weekly_recoveries.rename(
        columns={"daterecoveries": "DateRecoveries", "recoveries": "Recoveries"}
    )
    weekly_recoveries["DateRecoveries"] = pd.to_datetime(
        weekly_recoveries["DateRecoveries"]
    )
    weekly_recoveries.set_index("DateRecoveries", inplace=True)

    raw_data_recoveries = weekly_recoveries["Recoveries"].resample("W").sum()
    raw_data_weekly_recoveries = raw_data_recoveries.reset_index()
    total_recoveries = raw_data_weekly_recoveries["Recoveries"].sum()

    py_int1 = total_recoveries.item()
    py_int2 = raw_data_weekly_recoveries["Recoveries"].iloc[-1].item()

    latest_percentage = str(
        round(((py_int1 - (py_int1 - py_int2)) / py_int1) * 100, 2,)
    )
    statement = "new:  " + str(py_int2) + " (" + latest_percentage + "%)"

    return statement


@app.callback(
    Output("total_cases_deaths_update", "children"),
    [Input("interval-component", "n_intervals")],
)
def update_total_cases(n):
    weekly_deaths = db.selecting_deaths()
    weekly_deaths = weekly_deaths.rename(
        columns={"datedeaths": "DateDeaths", "deaths": "Deaths"}
    )

    weekly_deaths["DateDeaths"] = pd.to_datetime(weekly_deaths["DateDeaths"])
    weekly_deaths.set_index("DateDeaths", inplace=True)
    raw_data_deaths = weekly_deaths["Deaths"].resample("W").sum()
    raw_data_weekly_deaths = raw_data_deaths.reset_index()
    total_deaths = raw_data_weekly_deaths["Deaths"].sum()

    py_int1 = total_deaths.item()
    py_int2 = raw_data_weekly_deaths["Deaths"].iloc[-1].item()

    latest_percentage = str(
        round(((py_int1 - (py_int1 - py_int2)) / py_int1) * 100, 2,)
    )
    statement = "new:  " + str(py_int2) + " (" + latest_percentage + "%)"

    return statement


@app.callback(
    Output("recoveries_latest_update", "children"),
    [Input("interval-component", "n_intervals")],
)
def update_total_cases(n):
    weekly_recoveries = db.selecting_recoveries()

    weekly_recoveries = weekly_recoveries.rename(
        columns={"daterecoveries": "DateRecoveries", "recoveries": "Recoveries"}
    )
    weekly_recoveries["DateRecoveries"] = pd.to_datetime(
        weekly_recoveries["DateRecoveries"]
    )
    weekly_recoveries.set_index("DateRecoveries", inplace=True)
    raw_data_recoveries = weekly_recoveries["Recoveries"].resample("W").sum()
    raw_data_weekly_recoveries = raw_data_recoveries.reset_index()
    raw_data_weekly_recoveries["just_date"] = raw_data_weekly_recoveries[
        "DateRecoveries"
    ].dt.date
    latest_recoveries = str(
        convertion_date(max(raw_data_weekly_recoveries["just_date"]))
    )

    return "Latest Update:" + latest_recoveries


@app.callback(
    Output("infection_latest_update", "children"),
    [Input("interval-component", "n_intervals")],
)
def update_total_cases(n):
    weekly_infection = db.selecting_infection()
    weekly_infection = weekly_infection.rename(
        columns={"dateinfection": "DateInfection", "infection": "Infection"}
    )
    weekly_infection["DateInfection"] = pd.to_datetime(
        weekly_infection["DateInfection"]
    )
    weekly_infection.set_index("DateInfection", inplace=True)
    raw_data_infection = weekly_infection["Infection"].resample("W").sum()
    raw_data_weekly_infection = raw_data_infection.reset_index()
    raw_data_weekly_infection["just_date"] = raw_data_weekly_infection["DateInfection"].dt.date
    latest_infection = str(convertion_date(max(raw_data_weekly_infection["just_date"])))
    return "Latest Update:" + latest_infection


@app.callback(
    Output("deaths_latest_update", "children"),
    [Input("interval-component", "n_intervals")],
)
def update_total_cases(n):
    weekly_deaths = db.selecting_deaths()

    weekly_deaths = weekly_deaths.rename(
        columns={"datedeaths": "DateDeaths", "deaths": "Deaths"}
    )
    weekly_deaths["DateDeaths"] = pd.to_datetime(weekly_deaths["DateDeaths"])
    weekly_deaths.set_index("DateDeaths", inplace=True)
    raw_data_deaths = weekly_deaths["Deaths"].resample("W").sum()
    raw_data_weekly_deaths = raw_data_deaths.reset_index()
    raw_data_weekly_deaths["just_date"] = raw_data_weekly_deaths["DateDeaths"].dt.date
    latest_deaths = str(convertion_date(max(raw_data_weekly_deaths["just_date"])))
    return "Latest Update:" + latest_deaths


def counting_age(person_range):
    age_range = next(iter(person_range))
    split_range = age_range.split("-")
    x_range = int(split_range[0])
    y_range = int(split_range[1])

    for i in person_age_range:
        if i >= x_range and i <= y_range:
            person_range[age_range] = person_range[age_range] + 1
        else:
            pass

    return person_range


def zone_counting_age(person_range):
    age_range = next(iter(person_range))
    split_range = age_range.split("-")
    x_range = int(split_range[0])
    y_range = int(split_range[1])

    for i in zone_age_range:
        if i >= x_range and i <= y_range:
            person_range[age_range] = person_range[age_range] + 1
        else:
            pass

    return person_range


def demo_counting_age(person_range):
    age_range = next(iter(person_range))
    split_range = age_range.split("-")
    x_range = int(split_range[0])
    y_range = int(split_range[1])

    for i in demo_age_range:
        if i >= x_range and i <= y_range:
            person_range[age_range] = person_range[age_range] + 1
        else:
            pass

    return person_range


def percentage(person, group):

    percentage_list = []
    whole = len(person)

    if whole > 0:

        for x in group:
            num_age = list(x.values())[0]
            percent = round(100 * float(num_age) / float(whole))
            percentage = str(percent) + "%"
            percentage_list.append(percentage)
    else:

        percentage_list = ["0%", "0%", "0%", "0%", "0%", "0%", "0%", "0%", "0%", "0%"]

    return percentage_list


def coordinate_y(counting_age):

    count_age = list(counting_age.values())[0]

    return count_age


@app.callback(Output("barangay", "options"), [Input("zones_barangay", "value")])
def update_zones(zones_barangay):

    spec_zone = zone_infection_barangay[
        zone_infection_barangay["Zones"] == zones_barangay
    ]

    return [
        {"label": subzone, "value": subzone}
        for subzone in spec_zone["Address"].unique()
    ]


@app.callback(Output("barangay", "value"), [Input("zones_barangay", "value")])
def update_zones(zones_barangay):

    spec_zone = zone_infection_barangay[
        zone_infection_barangay["Zones"] == zones_barangay
    ]

    first_address = spec_zone["Address"].iloc[0]

    return first_address


def subtract_date(x):
    current_date = x.replace("-", "/")
    date_format_str = "%Y/%m/%d"
    # create datetime object from timestamp string
    given_time = datetime.strptime(current_date, date_format_str)

    final_time = given_time - timedelta(days=1)
    final_time_str = final_time.strftime("%Y/%m/%d")

    return final_time_str


@app.callback(
    Output("zone_date_title", "children"), [Input("zones_barangay", "value"),]
)
def update_date(zones_barangay):

    zone_infection_barangay = db.selecting_barangay_infection()
    zone_recoveries_barangay = db.selecting_barangay_recoveries()
    zone_deaths_barangay = db.selecting_barangay_deaths()

    zone_infection_barangay = zone_infection_barangay.rename(
        columns={
            "dateinfection": "Infection",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )
    zone_recoveries_barangay = zone_recoveries_barangay.rename(
        columns={
            "daterecoveries": "Recoveries",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )
    zone_deaths_barangay = zone_deaths_barangay.rename(
        columns={
            "datedeaths": "Deaths",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )

    zone_infection_barangay["Infection"] = zone_infection_barangay["Infection"].astype(
        str
    )
    zone_recoveries_barangay["Recoveries"] = zone_recoveries_barangay[
        "Recoveries"
    ].astype(str)
    zone_deaths_barangay["Deaths"] = zone_deaths_barangay["Deaths"].astype(str)

    try:
        spec_zone_infection = zone_infection_barangay[
            zone_infection_barangay["Zones"] == zones_barangay
        ]

        spec_barangay_recoveries = zone_recoveries_barangay[
            zone_recoveries_barangay["Zones"] == zones_barangay
        ]

        spec_barangay_deaths = zone_deaths_barangay[
            zone_deaths_barangay["Zones"] == zones_barangay
        ]

        max_date_infection = spec_zone_infection["Infection"].iloc[-1]
        max_date_recoveries = max(spec_barangay_recoveries["Recoveries"])
        max_date_deaths = max(spec_barangay_deaths["Deaths"])

    except ValueError:
        max_date_deaths = max_date_recoveries

    df_dates = pd.DataFrame(columns=["Date"])
    df_dates = df_dates.append({"Date": max_date_infection}, ignore_index=True)
    df_dates = df_dates.append({"Date": max_date_recoveries}, ignore_index=True)
    df_dates = df_dates.append({"Date": max_date_deaths}, ignore_index=True)

    new_case_update_date = convertion_date(max(df_dates["Date"]))

    statement = "Last 30 Days, Cases: " + str(new_case_update_date)
    return statement


@app.callback(
    Output("date_title", "children"),
    [Input("barangay", "value"), Input("zones_barangay", "value")],
)
def update_date(barangay, zones_barangay):
    zone_infection_barangay = db.selecting_barangay_infection()
    zone_recoveries_barangay = db.selecting_barangay_recoveries()
    zone_deaths_barangay = db.selecting_barangay_deaths()

    zone_infection_barangay = zone_infection_barangay.rename(
        columns={
            "dateinfection": "Infection",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )
    zone_recoveries_barangay = zone_recoveries_barangay.rename(
        columns={
            "daterecoveries": "Recoveries",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )
    zone_deaths_barangay = zone_deaths_barangay.rename(
        columns={
            "datedeaths": "Deaths",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )

    zone_infection_barangay["Infection"] = zone_infection_barangay["Infection"].astype(
        str
    )
    zone_recoveries_barangay["Recoveries"] = zone_recoveries_barangay[
        "Recoveries"
    ].astype(str)
    zone_deaths_barangay["Deaths"] = zone_deaths_barangay["Deaths"].astype(str)

    try:
        spec_zone_infection = zone_infection_barangay[
            zone_infection_barangay["Zones"] == zones_barangay
        ]
        spec_zone_recoveries = zone_recoveries_barangay[
            zone_recoveries_barangay["Zones"] == zones_barangay
        ]
        spec_zone_deaths = zone_deaths_barangay[
            zone_deaths_barangay["Zones"] == zones_barangay
        ]

        spec_barangay_infection = spec_zone_infection[
            spec_zone_infection["Address"] == barangay
        ]
        spec_barangay_recoveries = spec_zone_recoveries[
            spec_zone_recoveries["Address"] == barangay
        ]
        spec_barangay_deaths = spec_zone_deaths[spec_zone_deaths["Address"] == barangay]

        max_date_infection = spec_barangay_infection["Infection"].iloc[-1]
        max_date_recoveries = max(spec_barangay_recoveries["Recoveries"])
        max_date_deaths = max(spec_barangay_deaths["Deaths"])

    except ValueError:
        max_date_deaths = max_date_recoveries

    df_dates = pd.DataFrame(columns=["Date"])
    df_dates = df_dates.append({"Date": max_date_infection}, ignore_index=True)
    df_dates = df_dates.append({"Date": max_date_recoveries}, ignore_index=True)
    df_dates = df_dates.append({"Date": max_date_deaths}, ignore_index=True)

    new_case_update_date = convertion_date(max(df_dates["Date"]))

    statement = "Last 30 Days, Updated Cases: " + str(new_case_update_date)
    return statement


@app.callback(
    Output("infection_zone_title", "children"), [Input("zones_barangay", "value")]
)
def update_date(zones_barangay):
    zone_infection_barangay = db.selecting_barangay_infection()
    zone_infection_barangay = zone_infection_barangay.rename(
        columns={
            "dateinfection": "Infection",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )
    zone_infection_barangay["Infection"] = zone_infection_barangay["Infection"].astype(
        str
    )

    spec_zone_infection = zone_infection_barangay[
        zone_infection_barangay["Zones"] == zones_barangay
    ]

    max_date_infection = spec_zone_infection["Infection"].iloc[-1]
    df_dates = pd.DataFrame(columns=["Date"])

    df_dates = df_dates.append({"Date": max_date_infection}, ignore_index=True)

    new_case_update_date = convertion_date(max(df_dates["Date"]))

    statement = "Updated Infection Cases: " + str(new_case_update_date)

    return statement


@app.callback(
    Output("recoveries_zone_title", "children"), [Input("zones_barangay", "value")]
)
def update_date(zones_barangay):

    zone_recoveries_barangay = db.selecting_barangay_recoveries()
    zone_recoveries_barangay = zone_recoveries_barangay.rename(
        columns={
            "daterecoveries": "Recoveries",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )
    zone_recoveries_barangay["Recoveries"] = zone_recoveries_barangay[
        "Recoveries"
    ].astype(str)

    try:

        spec_zone_recoveries = zone_recoveries_barangay[
            zone_recoveries_barangay["Zones"] == zones_barangay
        ]

        max_date_recoveries = max(spec_zone_recoveries["Recoveries"])
        df_dates = pd.DataFrame(columns=["Date"])

        df_dates = df_dates.append({"Date": max_date_recoveries}, ignore_index=True)

        new_case_update_date = convertion_date(max(df_dates["Date"]))

        statement = "Updated Recoveries Cases: " + str(new_case_update_date)
    except ValueError:
        statement = "Updated Recoveries Cases: "
    return statement


@app.callback(
    Output("death_zone_title", "children"), [Input("zones_barangay", "value")]
)
def update_date(zones_barangay):

    zone_deaths_barangay = db.selecting_barangay_deaths()

    zone_deaths_barangay = zone_deaths_barangay.rename(
        columns={
            "datedeaths": "Deaths",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )
    zone_deaths_barangay["Deaths"] = zone_deaths_barangay["Deaths"].astype(str)
    try:

        spec_zone_deaths = zone_deaths_barangay[
            zone_deaths_barangay["Zones"] == zones_barangay
        ]

        max_date_deaths = max(spec_zone_deaths["Deaths"])
        df_dates = pd.DataFrame(columns=["Date"])

        df_dates = df_dates.append({"Date": max_date_deaths}, ignore_index=True)

        new_case_update_date = convertion_date(max(df_dates["Date"]))

        statement = "Updated Deaths Cases: " + str(new_case_update_date)
    except ValueError:
        statement = "Updated Deaths Cases: "
    return statement


@app.callback(
    Output("infection_barangay_title", "children"),
    [Input("zones_barangay", "value"), Input("barangay", "value")],
)
def update_date(zones_barangay, barangay):

    zone_infection_barangay = db.selecting_barangay_infection()
    zone_infection_barangay = zone_infection_barangay.rename(
        columns={
            "dateinfection": "Infection",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )
    zone_infection_barangay["Infection"] = zone_infection_barangay["Infection"].astype(
        str
    )
    try:

        spec_zone_infection = zone_infection_barangay[
            zone_infection_barangay["Zones"] == zones_barangay
        ]

        spec_barangay = spec_zone_infection[spec_zone_infection["Address"] == barangay]

        max_date_infection = max(spec_barangay["Infection"])
        df_dates = pd.DataFrame(columns=["Date"])

        df_dates = df_dates.append({"Date": max_date_infection}, ignore_index=True)

        new_case_update_date = convertion_date(max(df_dates["Date"]))

        statement = "Updated Infection Cases: " + str(new_case_update_date)
    except ValueError:
        statement = "Updated Infection Cases: "
    return statement


@app.callback(
    Output("recoveries_barangay_title", "children"),
    [Input("zones_barangay", "value"), Input("barangay", "value")],
)
def update_date(zones_barangay, barangay):

    zone_recoveries_barangay = db.selecting_barangay_recoveries()
    zone_recoveries_barangay = zone_recoveries_barangay.rename(
        columns={
            "daterecoveries": "Recoveries",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )
    zone_recoveries_barangay["Recoveries"] = zone_recoveries_barangay[
        "Recoveries"
    ].astype(str)

    try:

        spec_zone_recoveries = zone_recoveries_barangay[
            zone_recoveries_barangay["Zones"] == zones_barangay
        ]

        spec_barangay = spec_zone_recoveries[
            spec_zone_recoveries["Address"] == barangay
        ]

        max_date_recoveries = max(spec_barangay["Recoveries"])
        df_dates = pd.DataFrame(columns=["Date"])

        df_dates = df_dates.append({"Date": max_date_recoveries}, ignore_index=True)

        new_case_update_date = convertion_date(max(df_dates["Date"]))

        statement = "Updated Recoveries Cases: " + str(new_case_update_date)

    except ValueError:
        statement = "Updated Recoveries Cases: "

    return statement


@app.callback(
    Output("deaths_barangay_title", "children"),
    [Input("zones_barangay", "value"), Input("barangay", "value")],
)
def update_date(zones_barangay, barangay):
    zone_deaths_barangay = db.selecting_barangay_deaths()
    zone_deaths_barangay = zone_deaths_barangay.rename(
        columns={
            "datedeaths": "Deaths",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )
    zone_deaths_barangay["Deaths"] = zone_deaths_barangay["Deaths"].astype(str)
    try:

        spec_zone_deaths = zone_deaths_barangay[
            zone_deaths_barangay["Zones"] == zones_barangay
        ]

        spec_barangay = spec_zone_deaths[spec_zone_deaths["Address"] == barangay]

        max_date_deaths = max(spec_barangay["Deaths"])
        df_dates = pd.DataFrame(columns=["Date"])
        df_dates = df_dates.append({"Date": max_date_deaths}, ignore_index=True)

        new_case_update_date = convertion_date(max(df_dates["Date"]))

        statement = "Updated Deaths Cases: " + str(new_case_update_date)

    except ValueError:
        statement = "Updated Death Cases: "

    return statement


@app.callback(Output("infection_zone", "figure"), [Input("zones_barangay", "value")])
def update_confirmed(zones_barangay):
    # present_date_timestamp = pd.to_datetime(infection_barangay["Infection"].iloc[-1])

    zone_infection_barangay = db.selecting_barangay_infection()

    zone_infection_barangay = zone_infection_barangay.rename(
        columns={
            "dateinfection": "Infection",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )
    zone_infection_barangay["Infection"] = zone_infection_barangay["Infection"].astype(
        str
    )

    spec_zone = zone_infection_barangay[
        zone_infection_barangay["Zones"] == zones_barangay
    ]

    subtract_current_date = 0
    subtract_outdated_date = 0

    current_date_list = []
    outdated_date_list = []

    present_date = spec_zone["Infection"].iloc[-1]
    current_date_list.append(present_date)

    current = pd.DataFrame()
    outdated = pd.DataFrame()

    while subtract_current_date < 30:

        current_day = current_date_list[subtract_current_date]
        current_last_seven_days = subtract_date(current_day)
        current_date_list.append(current_last_seven_days)
        subtract_current_date = subtract_current_date + 1

    outdated_date = subtract_date(current_date_list[len(current_date_list) - 1])
    outdated_date_list.append(outdated_date)

    while subtract_outdated_date < 30:

        outdated_day = outdated_date_list[subtract_outdated_date]
        outdated_last_seven_days = subtract_date(outdated_day)
        outdated_date_list.append(outdated_last_seven_days)
        subtract_outdated_date = subtract_outdated_date + 1

    for x in current_date_list:

        x = x.replace("/", "-")
        current_infection = spec_zone[spec_zone["Infection"] == x]
        current = current.append(current_infection)

    for y in outdated_date_list:
        y = y.replace("/", "-")
        outdated_infection = spec_zone[spec_zone["Infection"] == y]
        outdated = outdated.append(outdated_infection)

    num_current_infection = len(current)
    num_outdated_infection = len(outdated)

    data = {"Current": [num_current_infection], "Outdated": [num_outdated_infection]}
    df = pd.DataFrame(data)
    df["Barangay"] = zones_barangay

    value_infection = df[df["Barangay"] == zones_barangay]["Current"][0]
    delta_infection = df[df["Barangay"] == zones_barangay]["Outdated"][0]

    return {
        "data": [
            go.Indicator(
                mode="number+delta",
                value=value_infection,
                delta={
                    "reference": delta_infection,
                    "position": "right",
                    "valueformat": ".0f",
                    "increasing": {"color": "#FF0000"},
                    "decreasing": {"color": "green"},
                    "relative": False,
                    "font": {"size": 15},
                },
                number={"valueformat": ",", "font": {"size": 20},},
                domain={"y": [0, 1], "x": [0, 1]},
            )
        ],
        "layout": go.Layout(
            title={
                "text": "New Confirmed",
                "y": 1,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            },
            font=dict(color="orange"),
            paper_bgcolor="#1f2c56",
            plot_bgcolor="#1f2c56",
            height=50,
        ),
    }


@app.callback(
    Output("infection_barangay", "figure"),
    [Input("barangay", "value"), Input("zones_barangay", "value")],
)
def update_confirmed(barangay, zones_barangay):
    # present_date_timestamp = pd.to_datetime(infection_barangay["Infection"].iloc[-1])
    zone_infection_barangay = db.selecting_barangay_infection()

    zone_infection_barangay = zone_infection_barangay.rename(
        columns={
            "dateinfection": "Infection",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )
    zone_infection_barangay["Infection"] = zone_infection_barangay["Infection"].astype(
        str
    )

    spec_zone = zone_infection_barangay[
        zone_infection_barangay["Zones"] == zones_barangay
    ]
    spec_barangay = spec_zone[spec_zone["Address"] == barangay]
    subtract_current_date = 0
    subtract_outdated_date = 0

    current_date_list = []
    outdated_date_list = []

    present_date = spec_barangay["Infection"].iloc[-1]
    current_date_list.append(present_date)

    current = pd.DataFrame()
    outdated = pd.DataFrame()

    while subtract_current_date < 30:

        current_day = current_date_list[subtract_current_date]
        current_last_seven_days = subtract_date(current_day)
        current_date_list.append(current_last_seven_days)
        subtract_current_date = subtract_current_date + 1

    outdated_date = subtract_date(current_date_list[len(current_date_list) - 1])
    outdated_date_list.append(outdated_date)

    while subtract_outdated_date < 30:

        outdated_day = outdated_date_list[subtract_outdated_date]
        outdated_last_seven_days = subtract_date(outdated_day)
        outdated_date_list.append(outdated_last_seven_days)
        subtract_outdated_date = subtract_outdated_date + 1

    for x in current_date_list:

        x = x.replace("/", "-")
        current_infection = spec_barangay[spec_barangay["Infection"] == x]
        current = current.append(current_infection)

    for y in outdated_date_list:
        y = y.replace("/", "-")
        outdated_infection = spec_barangay[spec_barangay["Infection"] == y]
        outdated = outdated.append(outdated_infection)

    num_current_infection = len(current)
    num_outdated_infection = len(outdated)

    data = {"Current": [num_current_infection], "Outdated": [num_outdated_infection]}
    df = pd.DataFrame(data)
    df["Barangay"] = barangay

    value_infection = df[df["Barangay"] == barangay]["Current"][0]
    delta_infection = df[df["Barangay"] == barangay]["Outdated"][0]

    return {
        "data": [
            go.Indicator(
                mode="number+delta",
                value=value_infection,
                delta={
                    "reference": delta_infection,
                    "position": "right",
                    "valueformat": ".0f",
                    "increasing": {"color": "#FF0000"},
                    "decreasing": {"color": "green"},
                    "relative": False,
                    "font": {"size": 15},
                },
                number={"valueformat": ",", "font": {"size": 20},},
                domain={"y": [0, 1], "x": [0, 1]},
            )
        ],
        "layout": go.Layout(
            title={
                "text": "New Confirmed",
                "y": 1,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            },
            font=dict(color="orange"),
            paper_bgcolor="#1f2c56",
            plot_bgcolor="#1f2c56",
            height=50,
        ),
    }


@app.callback(Output("recoveries_zone", "figure"), [Input("zones_barangay", "value")])
def update_confirmed(zones_barangay):
    # present_date_timestamp = pd.to_datetime(infection_barangay["Infection"].iloc[-1])

    zone_recoveries_barangay = db.selecting_barangay_recoveries()
    zone_recoveries_barangay = zone_recoveries_barangay.rename(
        columns={
            "daterecoveries": "Recoveries",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )
    zone_recoveries_barangay["Recoveries"] = zone_recoveries_barangay[
        "Recoveries"
    ].astype(str)

    spec_zone = zone_recoveries_barangay[
        zone_recoveries_barangay["Zones"] == zones_barangay
    ]
    subtract_current_date = 0
    subtract_outdated_date = 0
    current_date_list = []
    outdated_date_list = []
    try:
        present_date = max(spec_zone["Recoveries"])
        current_date_list.append(present_date)

        current = pd.DataFrame()
        outdated = pd.DataFrame()

        while subtract_current_date < 30:

            current_day = current_date_list[subtract_current_date]
            current_last_seven_days = subtract_date(current_day)
            current_date_list.append(current_last_seven_days)
            subtract_current_date = subtract_current_date + 1

        outdated_date = subtract_date(current_date_list[len(current_date_list) - 1])
        outdated_date_list.append(outdated_date)

        while subtract_outdated_date < 30:

            outdated_day = outdated_date_list[subtract_outdated_date]
            outdated_last_seven_days = subtract_date(outdated_day)
            outdated_date_list.append(outdated_last_seven_days)
            subtract_outdated_date = subtract_outdated_date + 1

        for x in current_date_list:

            x = x.replace("/", "-")
            current_recoveries = spec_zone[spec_zone["Recoveries"] == x]
            current = current.append(current_recoveries)

        for y in outdated_date_list:
            y = y.replace("/", "-")
            outdated_recoveries = spec_zone[spec_zone["Recoveries"] == y]
            outdated = outdated.append(outdated_recoveries)

        num_current_recoveries = len(current)
        num_outdated_recoveries = len(outdated)
    except ValueError:
        num_current_recoveries = 0
        num_outdated_recoveries = 0

    data_recoveries = {
        "Current": [num_current_recoveries],
        "Outdated": [num_outdated_recoveries],
    }
    df_recoveries = pd.DataFrame(data_recoveries)
    df_recoveries["Barangay"] = zones_barangay

    value_infection = df_recoveries[df_recoveries["Barangay"] == zones_barangay][
        "Current"
    ][0]
    delta_infection = df_recoveries[df_recoveries["Barangay"] == zones_barangay][
        "Outdated"
    ][0]

    return {
        "data": [
            go.Indicator(
                mode="number+delta",
                value=value_infection,
                delta={
                    "reference": delta_infection,
                    "position": "right",
                    "valueformat": ".0f",
                    "increasing": {"color": "green"},
                    "decreasing": {"color": "#FF0000"},
                    "relative": False,
                    "font": {"size": 15},
                },
                number={"valueformat": ",", "font": {"size": 20},},
                domain={"y": [0, 1], "x": [0, 1]},
            )
        ],
        "layout": go.Layout(
            title={
                "text": "New Recoveries",
                "y": 1,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            },
            font=dict(color="green"),
            paper_bgcolor="#1f2c56",
            plot_bgcolor="#1f2c56",
            height=50,
        ),
    }


@app.callback(
    Output("recoveries_barangay", "figure"),
    [Input("barangay", "value"), Input("zones_barangay", "value")],
)
def update_confirmed(barangay, zones_barangay):
    # present_date_timestamp = pd.to_datetime(infection_barangay["Infection"].iloc[-1])
    zone_recoveries_barangay = db.selecting_barangay_recoveries()
    zone_recoveries_barangay = zone_recoveries_barangay.rename(
        columns={
            "daterecoveries": "Recoveries",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )
    zone_recoveries_barangay["Recoveries"] = zone_recoveries_barangay[
        "Recoveries"
    ].astype(str)

    spec_zone = zone_recoveries_barangay[
        zone_recoveries_barangay["Zones"] == zones_barangay
    ]

    spec_barangay = spec_zone[spec_zone["Address"] == barangay]
    subtract_current_date = 0
    subtract_outdated_date = 0
    current_date_list = []
    outdated_date_list = []
    try:
        present_date = max(spec_barangay["Recoveries"])
        current_date_list.append(present_date)

        current = pd.DataFrame()
        outdated = pd.DataFrame()

        while subtract_current_date < 30:

            current_day = current_date_list[subtract_current_date]
            current_last_seven_days = subtract_date(current_day)
            current_date_list.append(current_last_seven_days)
            subtract_current_date = subtract_current_date + 1

        outdated_date = subtract_date(current_date_list[len(current_date_list) - 1])
        outdated_date_list.append(outdated_date)

        while subtract_outdated_date < 30:

            outdated_day = outdated_date_list[subtract_outdated_date]
            outdated_last_seven_days = subtract_date(outdated_day)
            outdated_date_list.append(outdated_last_seven_days)
            subtract_outdated_date = subtract_outdated_date + 1

        for x in current_date_list:

            x = x.replace("/", "-")
            current_recoveries = spec_barangay[spec_barangay["Recoveries"] == x]
            current = current.append(current_recoveries)

        for y in outdated_date_list:
            y = y.replace("/", "-")
            outdated_recoveries = spec_barangay[spec_barangay["Recoveries"] == y]
            outdated = outdated.append(outdated_recoveries)

        num_current_recoveries = len(current)
        num_outdated_recoveries = len(outdated)
    except ValueError:
        num_current_recoveries = 0
        num_outdated_recoveries = 0

    data_recoveries = {
        "Current": [num_current_recoveries],
        "Outdated": [num_outdated_recoveries],
    }
    df_recoveries = pd.DataFrame(data_recoveries)
    df_recoveries["Barangay"] = barangay

    value_infection = df_recoveries[df_recoveries["Barangay"] == barangay]["Current"][0]
    delta_infection = df_recoveries[df_recoveries["Barangay"] == barangay]["Outdated"][
        0
    ]

    return {
        "data": [
            go.Indicator(
                mode="number+delta",
                value=value_infection,
                delta={
                    "reference": delta_infection,
                    "position": "right",
                    "valueformat": ".0f",
                    "increasing": {"color": "green"},
                    "decreasing": {"color": "#FF0000"},
                    "relative": False,
                    "font": {"size": 15},
                },
                number={"valueformat": ",", "font": {"size": 20},},
                domain={"y": [0, 1], "x": [0, 1]},
            )
        ],
        "layout": go.Layout(
            title={
                "text": "New Recoveries",
                "y": 1,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            },
            font=dict(color="green"),
            paper_bgcolor="#1f2c56",
            plot_bgcolor="#1f2c56",
            height=50,
        ),
    }


@app.callback(Output("deaths_zone", "figure"), [Input("zones_barangay", "value")])
def update_confirmed(zones_barangay):
    # present_date_timestamp = pd.to_datetime(infection_barangay["Infection"].iloc[-1])
    zone_deaths_barangay = db.selecting_barangay_deaths()

    zone_deaths_barangay = zone_deaths_barangay.rename(
        columns={
            "datedeaths": "Deaths",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )
    zone_deaths_barangay["Deaths"] = zone_deaths_barangay["Deaths"].astype(str)
    spec_zone = zone_deaths_barangay[zone_deaths_barangay["Zones"] == zones_barangay]
    subtract_current_date = 0
    subtract_outdated_date = 0
    current_date_list = []
    outdated_date_list = []

    try:
        present_date = max(spec_zone["Deaths"])
        current_date_list.append(present_date)

        current = pd.DataFrame()
        outdated = pd.DataFrame()

        while subtract_current_date < 30:

            current_day = current_date_list[subtract_current_date]
            current_last_seven_days = subtract_date(current_day)
            current_date_list.append(current_last_seven_days)
            subtract_current_date = subtract_current_date + 1

        outdated_date = subtract_date(current_date_list[len(current_date_list) - 1])
        outdated_date_list.append(outdated_date)

        while subtract_outdated_date < 30:

            outdated_day = outdated_date_list[subtract_outdated_date]
            outdated_last_seven_days = subtract_date(outdated_day)
            outdated_date_list.append(outdated_last_seven_days)
            subtract_outdated_date = subtract_outdated_date + 1

        for x in current_date_list:

            x = x.replace("/", "-")
            current_deaths = spec_zone[spec_zone["Deaths"] == x]
            current = current.append(current_deaths)

        for y in outdated_date_list:
            y = y.replace("/", "-")
            outdated_deaths = spec_zone[spec_zone["Deaths"] == y]
            outdated = outdated.append(outdated_deaths)

        num_current_deaths = len(current)
        num_outdated_deaths = len(outdated)

    except ValueError:
        num_current_deaths = 0
        num_outdated_deaths = 0

    data_deaths = {"Current": [num_current_deaths], "Outdated": [num_outdated_deaths]}
    df_deaths = pd.DataFrame(data_deaths)
    df_deaths["Barangay"] = zones_barangay

    value_infection = df_deaths[df_deaths["Barangay"] == zones_barangay]["Current"][0]
    delta_infection = df_deaths[df_deaths["Barangay"] == zones_barangay]["Outdated"][0]

    return {
        "data": [
            go.Indicator(
                mode="number+delta",
                value=value_infection,
                delta={
                    "reference": delta_infection,
                    "position": "right",
                    "valueformat": ".0f",
                    "increasing": {"color": "#FF0000"},
                    "decreasing": {"color": "green"},
                    "relative": False,
                    "font": {"size": 15},
                },
                number={"valueformat": ",", "font": {"size": 20},},
                domain={"y": [0, 1], "x": [0, 1]},
            )
        ],
        "layout": go.Layout(
            title={
                "text": "New Deaths",
                "y": 1,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            },
            font=dict(color="#FF0000"),
            paper_bgcolor="#1f2c56",
            plot_bgcolor="#1f2c56",
            height=50,
        ),
    }


@app.callback(
    Output("deaths_barangay", "figure"),
    [Input("barangay", "value"), Input("zones_barangay", "value")],
)
def update_confirmed(barangay, zones_barangay):
    # present_date_timestamp = pd.to_datetime(infection_barangay["Infection"].iloc[-1])
    zone_deaths_barangay = db.selecting_barangay_deaths()
    zone_deaths_barangay = zone_deaths_barangay.rename(
        columns={
            "datedeaths": "Deaths",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )
    zone_deaths_barangay["Deaths"] = zone_deaths_barangay["Deaths"].astype(str)

    spec_zone = zone_deaths_barangay[zone_deaths_barangay["Zones"] == zones_barangay]
    spec_barangay = spec_zone[spec_zone["Address"] == barangay]
    subtract_current_date = 0
    subtract_outdated_date = 0
    current_date_list = []
    outdated_date_list = []

    try:
        present_date = max(spec_barangay["Deaths"])
        current_date_list.append(present_date)

        current = pd.DataFrame()
        outdated = pd.DataFrame()

        while subtract_current_date < 30:

            current_day = current_date_list[subtract_current_date]
            current_last_seven_days = subtract_date(current_day)
            current_date_list.append(current_last_seven_days)
            subtract_current_date = subtract_current_date + 1

        outdated_date = subtract_date(current_date_list[len(current_date_list) - 1])
        outdated_date_list.append(outdated_date)

        while subtract_outdated_date < 30:

            outdated_day = outdated_date_list[subtract_outdated_date]
            outdated_last_seven_days = subtract_date(outdated_day)
            outdated_date_list.append(outdated_last_seven_days)
            subtract_outdated_date = subtract_outdated_date + 1

        for x in current_date_list:

            x = x.replace("/", "-")
            current_deaths = spec_barangay[spec_barangay["Deaths"] == x]
            current = current.append(current_deaths)

        for y in outdated_date_list:
            y = y.replace("/", "-")
            outdated_deaths = spec_barangay[spec_barangay["Deaths"] == y]
            outdated = outdated.append(outdated_deaths)

        num_current_deaths = len(current)
        num_outdated_deaths = len(outdated)
    except ValueError:
        num_current_deaths = 0
        num_outdated_deaths = 0

    data_deaths = {"Current": [num_current_deaths], "Outdated": [num_outdated_deaths]}
    df_deaths = pd.DataFrame(data_deaths)
    df_deaths["Barangay"] = barangay

    value_infection = df_deaths[df_deaths["Barangay"] == barangay]["Current"][0]
    delta_infection = df_deaths[df_deaths["Barangay"] == barangay]["Outdated"][0]

    return {
        "data": [
            go.Indicator(
                mode="number+delta",
                value=value_infection,
                delta={
                    "reference": delta_infection,
                    "position": "right",
                    "valueformat": ".0f",
                    "increasing": {"color": "#FF0000"},
                    "decreasing": {"color": "green"},
                    "relative": False,
                    "font": {"size": 15},
                },
                number={"valueformat": ",", "font": {"size": 20},},
                domain={"y": [0, 1], "x": [0, 1]},
            )
        ],
        "layout": go.Layout(
            title={
                "text": "New Deaths",
                "y": 1,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            },
            font=dict(color="#FF0000"),
            paper_bgcolor="#1f2c56",
            plot_bgcolor="#1f2c56",
            height=50,
        ),
    }


def specific_range(argument, spec_address):
    switcher = {
        "1-10": spec_address.loc[
            (spec_address["Age"] >= 1) & (spec_address["Age"] <= 10)
        ],
        "11-20": spec_address.loc[
            (spec_address["Age"] >= 11) & (spec_address["Age"] <= 20)
        ],
        "21-30": spec_address.loc[
            (spec_address["Age"] >= 21) & (spec_address["Age"] <= 30)
        ],
        "31-40": spec_address.loc[
            (spec_address["Age"] >= 31) & (spec_address["Age"] <= 40)
        ],
        "41-50": spec_address.loc[
            (spec_address["Age"] >= 41) & (spec_address["Age"] <= 50)
        ],
        "51-60": spec_address.loc[
            (spec_address["Age"] >= 51) & (spec_address["Age"] <= 60)
        ],
        "61-70": spec_address.loc[
            (spec_address["Age"] >= 61) & (spec_address["Age"] <= 70)
        ],
        "71-80": spec_address.loc[
            (spec_address["Age"] >= 71) & (spec_address["Age"] <= 80)
        ],
        "81-90": spec_address.loc[
            (spec_address["Age"] >= 81) & (spec_address["Age"] <= 90)
        ],
        "91-100": spec_address.loc[
            (spec_address["Age"] >= 91) & (spec_address["Age"] <= 100)
        ],
    }

    return switcher.get(argument, "nothing")


def gender_find(argument, spec_age):
    switcher = {
        "Male": spec_age.loc[(spec_age["Sex"] == "Male")],
        "Female": spec_age.loc[(spec_age["Sex"] == "Female")],
        "All":spec_age[0:]
    }

    return switcher.get(argument, "nothing")


@app.callback(
    Output("confirmed", "figure"),
    [
        Input("barangay", "value"),
        Input("demo_age", "value"),
        Input("demo_gender", "value"),
        Input("zones_barangay", "value"),
    ],
)
def update_cases(barangay, demo_age, demo_gender, zones_barangay):
    zone_infection_barangay = db.selecting_barangay_infection()
    zone_infection_barangay = zone_infection_barangay.rename(
        columns={
            "dateinfection": "Infection",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )
    zone_infection_barangay["Infection"] = zone_infection_barangay["Infection"].astype(
        str
    )

    split_age = demo_age.split(" ")
    spec_zone = zone_infection_barangay[
        zone_infection_barangay["Zones"] == zones_barangay
    ]

    spec_barangay = spec_zone[spec_zone["Address"] == barangay]
    spec_age = specific_range(split_age[0], spec_barangay)
    spec_gender = gender_find(demo_gender, spec_age)

    number_of_confirmed = len(spec_gender)

    return {
        "data": [
            go.Indicator(
                mode="number",
                value=number_of_confirmed,
                number={"valueformat": ",", "font": {"size": 20},},
                domain={"y": [0, 1], "x": [0, 1]},
            )
        ],
        "layout": go.Layout(
            title={
                "text": "Confirmed Cases",
                "y": 1,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            },
            font=dict(color="orange"),
            paper_bgcolor="#1f2c56",
            plot_bgcolor="#1f2c56",
            height=50,
        ),
    }


@app.callback(
    Output("recoveries", "figure"),
    [
        Input("barangay", "value"),
        Input("demo_age", "value"),
        Input("demo_gender", "value"),
        Input("zones_barangay", "value"),
    ],
)
def update_cases(barangay, demo_age, demo_gender, zones_barangay):

    zone_recoveries_barangay = db.selecting_barangay_recoveries()
    zone_recoveries_barangay = zone_recoveries_barangay.rename(
        columns={
            "daterecoveries": "Recoveries",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )
    zone_recoveries_barangay["Recoveries"] = zone_recoveries_barangay[
        "Recoveries"
    ].astype(str)

    split_age = demo_age.split(" ")

    spec_zone = zone_recoveries_barangay[
        zone_recoveries_barangay["Zones"] == zones_barangay
    ]
    spec_barangay = spec_zone[spec_zone["Address"] == barangay]

    spec_age = specific_range(split_age[0], spec_barangay)
    spec_gender = gender_find(demo_gender, spec_age)

    number_of_confirmed = len(spec_gender)

    return {
        "data": [
            go.Indicator(
                mode="number",
                value=number_of_confirmed,
                number={"valueformat": ",", "font": {"size": 20},},
                domain={"y": [0, 1], "x": [0, 1]},
            )
        ],
        "layout": go.Layout(
            title={
                "text": "Recoveries Cases",
                "y": 1,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            },
            font=dict(color="green"),
            paper_bgcolor="#1f2c56",
            plot_bgcolor="#1f2c56",
            height=50,
        ),
    }


@app.callback(
    Output("deaths", "figure"),
    [
        Input("barangay", "value"),
        Input("demo_age", "value"),
        Input("demo_gender", "value"),
        Input("zones_barangay", "value"),
    ],
)
def update_cases(barangay, demo_age, demo_gender, zones_barangay):

    zone_deaths_barangay = db.selecting_barangay_deaths()
    zone_deaths_barangay = zone_deaths_barangay.rename(
        columns={
            "datedeaths": "Deaths",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )
    zone_deaths_barangay["Deaths"] = zone_deaths_barangay["Deaths"].astype(str)

    split_age = demo_age.split(" ")

    spec_zone = zone_deaths_barangay[zone_deaths_barangay["Zones"] == zones_barangay]
    spec_barangay = spec_zone[spec_zone["Address"] == barangay]

    spec_age = specific_range(split_age[0], spec_barangay)
    spec_gender = gender_find(demo_gender, spec_age)
    number_of_confirmed = len(spec_gender)
    return {
        "data": [
            go.Indicator(
                mode="number",
                value=number_of_confirmed,
                number={"valueformat": ",", "font": {"size": 20},},
                domain={"y": [0, 1], "x": [0, 1]},
            )
        ],
        "layout": go.Layout(
            title={
                "text": "Death Cases",
                "y": 1,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            },
            font=dict(color="#FF0000"),
            paper_bgcolor="#1f2c56",
            plot_bgcolor="#1f2c56",
            height=50,
        ),
    }


def satinize_age_range(person_range):

    age_range = next(iter(person_range))
    # count_age = person_range[age_range]

    return age_range


def satinize_count_age(person_range):

    age_range = next(iter(person_range))
    count_age = person_range[age_range]

    return count_age


# Create pie chart (total casualties)
@app.callback(
    Output("demo_pie_chart", "figure"),
    [
        Input("zones_barangay", "value"),
        Input("barangay", "value"),
        Input("demo_cases", "value"),
        Input("demo_gender", "value"),
    ],
)
def update_graph(zones_barangay, barangay, demo_cases, demo_gender):
    if demo_cases == "Infection":

        zone_infection_barangay = db.selecting_barangay_infection()
        zone_infection_barangay = zone_infection_barangay.rename(
            columns={
                "dateinfection": "Infection",
                "age": "Age",
                "gender": "Sex",
                "zones": "Zones",
                "address": "Address",
            }
        )
        zone_infection_barangay["Infection"] = zone_infection_barangay[
            "Infection"
        ].astype(str)

        spec_zone = zone_infection_barangay[
            zone_infection_barangay["Zones"] == zones_barangay
        ]
    elif demo_cases == "Recoveries":
        zone_recoveries_barangay = db.selecting_barangay_recoveries()
        zone_recoveries_barangay = zone_recoveries_barangay.rename(
            columns={
                "daterecoveries": "Recoveries",
                "age": "Age",
                "gender": "Sex",
                "zones": "Zones",
                "address": "Address",
            }
        )
        zone_recoveries_barangay["Recoveries"] = zone_recoveries_barangay[
            "Recoveries"
        ].astype(str)
        spec_zone = zone_recoveries_barangay[
            zone_recoveries_barangay["Zones"] == zones_barangay
        ]
    elif demo_cases == "Deaths":
        zone_deaths_barangay = db.selecting_barangay_deaths()
        zone_deaths_barangay = zone_deaths_barangay.rename(
            columns={
                "datedeaths": "Deaths",
                "age": "Age",
                "gender": "Sex",
                "zones": "Zones",
                "address": "Address",
            }
        )
        zone_deaths_barangay["Deaths"] = zone_deaths_barangay["Deaths"].astype(str)
        spec_zone = zone_deaths_barangay[
            zone_deaths_barangay["Zones"] == zones_barangay
        ]

    spec_barangay = spec_zone[spec_zone["Address"] == barangay]

    global demo_age_range
    x_count = [
        {"1-10": 0},
        {"11-20": 0},
        {"21-30": 0},
        {"31-40": 0},
        {"41-50": 0},
        {"51-60": 0},
        {"61-70": 0},
        {"71-80": 0},
        {"81-90": 0},
        {"91-100": 0},
    ]

    person_gender = gender_find(demo_gender, spec_barangay)
    demo_age_range = person_gender["Age"]
    result = list(map(demo_counting_age, x_count))

    deep_copy = result
    index_pop = 0

    for x in result:

        person_age = next(iter(x))

        if x[person_age] > 0:
            index_pop = index_pop + 1
            continue
        elif x[person_age] == 0:
            deep_copy.pop(index_pop)
            index_pop = index_pop + 1

    start_index_pop = deep_copy[0]
    end_index_pop = deep_copy[len(deep_copy) - 1]

    start_value_pop = next(iter(start_index_pop))
    end_value_pop = next(iter(end_index_pop))

    if start_index_pop[start_value_pop] == 0:
        deep_copy.pop(0)

    if end_index_pop[end_value_pop] == 0:
        deep_copy.pop()

    colors = [
        "orange",
        "#69bdd2",
        "green",
        "#edb879",
        "#1979a9",
        "#e07b39",
        "#80391e",
        "#cce7e8",
        "#cce7e8",
        "#b97455",
    ]

    size_color = colors[: len(deep_copy)]
    return {
        "data": [
            go.Pie(
                labels=list(map(satinize_age_range, deep_copy)),
                values=list(map(satinize_count_age, deep_copy)),
                marker=dict(colors=colors),
                hoverinfo="label+value+percent",
                textinfo="label+value",
                textfont=dict(size=13),
                hole=0.7,
                rotation=45,
            )
        ],
        "layout": go.Layout(
            # width=800,
            # height=520,
            plot_bgcolor="#1f2c56",
            paper_bgcolor="#1f2c56",
            hovermode="closest",
            title={
                "text": "<b>"
                + "Total "
                + demo_gender
                + " "
                + demo_cases
                + " Cases : "
                + (barangay)
                + "</b>",
                "y": 0.93,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            },
            titlefont={"color": "white", "size": 15},
            legend={
                "orientation": "h",
                "bgcolor": "#1f2c56",
                "xanchor": "center",
                "x": 0.5,
                "y": -0.07,
            },
            font=dict(family="sans-serif", size=12, color="white"),
        ),
    }


# Create pie chart (total casualties)
@app.callback(Output("zone_pie_chart", "figure"), [Input("zones_barangay", "value"), Input("zone_gender", "value")])
def update_graph(zones_barangay, zone_gender):

    zone_infection_barangay = db.selecting_barangay_infection()
    zone_recoveries_barangay = db.selecting_barangay_recoveries()
    zone_deaths_barangay = db.selecting_barangay_deaths()

    zone_infection_barangay = zone_infection_barangay.rename(
        columns={
            "dateinfection": "Infection",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )
    zone_recoveries_barangay = zone_recoveries_barangay.rename(
        columns={
            "daterecoveries": "Recoveries",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )
    zone_deaths_barangay = zone_deaths_barangay.rename(
        columns={
            "datedeaths": "Deaths",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )

    zone_infection_barangay["Infection"] = zone_infection_barangay["Infection"].astype(
        str
    )
    zone_recoveries_barangay["Recoveries"] = zone_recoveries_barangay[
        "Recoveries"
    ].astype(str)
    zone_deaths_barangay["Deaths"] = zone_deaths_barangay["Deaths"].astype(str)

    spec_barangay_infection = zone_infection_barangay[
        zone_infection_barangay["Zones"] == zones_barangay
    ]
    spec_barangay_recoveries = zone_recoveries_barangay[
        zone_recoveries_barangay["Zones"] == zones_barangay
    ]
    spec_barangay_deaths = zone_deaths_barangay[
        zone_deaths_barangay["Zones"] == zones_barangay
    ]

    total_spec_barangay_infection = gender_find(zone_gender, spec_barangay_infection)
    total_spec_barangay_recoveries = gender_find(zone_gender, spec_barangay_recoveries)
    total_spec_barangay_deaths = gender_find(zone_gender, spec_barangay_deaths)

    total_barangay_infection = len(total_spec_barangay_infection)
    total_barangay_recoveries = len(total_spec_barangay_recoveries)
    total_barangay_deaths = len(total_spec_barangay_deaths)

    colors = ["orange", "#dd1e35", "green"]

    return {
        "data": [
            go.Pie(
                labels=["Confirmed", "Death", "Recovered"],
                values=[
                    total_barangay_infection,
                    total_barangay_deaths,
                    total_barangay_recoveries,
                ],
                marker=dict(colors=colors),
                hoverinfo="label+value+percent",
                textinfo="label+value",
                textfont=dict(size=13),
                hole=0.7,
                rotation=45,
                insidetextorientation="radial",
            )
        ],
        "layout": go.Layout(
            # width=800,
            # height=520,
            plot_bgcolor="#1f2c56",
            paper_bgcolor="#1f2c56",
            hovermode="closest",
            title={
                "text": "<b>" + "Total Cases : " + (zones_barangay) + "</b>",
                "y": 0.93,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            },
            titlefont={"color": "white", "size": 15},
            legend={
                "orientation": "h",
                "bgcolor": "#1f2c56",
                "xanchor": "center",
                "x": 0.5,
                "y": -0.07,
            },
            font=dict(family="sans-serif", size=12, color="white"),
            transition=dict(duration=500, easing="cubic-in-out"),
        ),
    }


# Create pie chart (total casualties)
@app.callback(
    Output("pie_chart", "figure"),
    [Input("barangay", "value"), Input("zones_barangay", "value"), Input("gender", "value")],
)
def update_graph(barangay, zones_barangay, gender):

    zone_infection_barangay = db.selecting_barangay_infection()
    zone_recoveries_barangay = db.selecting_barangay_recoveries()
    zone_deaths_barangay = db.selecting_barangay_deaths()

    zone_infection_barangay = zone_infection_barangay.rename(
        columns={
            "dateinfection": "Infection",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )
    zone_recoveries_barangay = zone_recoveries_barangay.rename(
        columns={
            "daterecoveries": "Recoveries",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )
    zone_deaths_barangay = zone_deaths_barangay.rename(
        columns={
            "datedeaths": "Deaths",
            "age": "Age",
            "gender": "Sex",
            "zones": "Zones",
            "address": "Address",
        }
    )

    zone_infection_barangay["Infection"] = zone_infection_barangay["Infection"].astype(
        str
    )
    zone_recoveries_barangay["Recoveries"] = zone_recoveries_barangay[
        "Recoveries"
    ].astype(str)
    zone_deaths_barangay["Deaths"] = zone_deaths_barangay["Deaths"].astype(str)

    spec_zone_infection = zone_infection_barangay[
        zone_infection_barangay["Zones"] == zones_barangay
    ]
    spec_zone_recoveries = zone_recoveries_barangay[
        zone_recoveries_barangay["Zones"] == zones_barangay
    ]
    spec_zone_deaths = zone_deaths_barangay[
        zone_deaths_barangay["Zones"] == zones_barangay
    ]

    spec_barangay_infection = spec_zone_infection[
        spec_zone_infection["Address"] == barangay
    ]
    spec_barangay_recoveries = spec_zone_recoveries[
        spec_zone_recoveries["Address"] == barangay
    ]
    spec_barangay_deaths = spec_zone_deaths[spec_zone_deaths["Address"] == barangay]

    total_spec_barangay_infection = gender_find(gender, spec_barangay_infection)
    total_spec_barangay_recoveries = gender_find(gender, spec_barangay_recoveries)
    total_spec_barangay_deaths = gender_find(gender, spec_barangay_deaths)

    total_barangay_infection = len(total_spec_barangay_infection)
    total_barangay_recoveries = len(total_spec_barangay_recoveries)
    total_barangay_deaths = len(total_spec_barangay_deaths)

    colors = ["orange", "#dd1e35", "green"]

    return {
        "data": [
            go.Pie(
                labels=["Confirmed", "Death", "Recovered"],
                values=[
                    total_barangay_infection,
                    total_barangay_deaths,
                    total_barangay_recoveries,
                ],
                marker=dict(colors=colors),
                hoverinfo="label+value+percent",
                textinfo="label+value",
                textfont=dict(size=13),
                hole=0.7,
                rotation=45,
                insidetextorientation="radial",
            )
        ],
        "layout": go.Layout(
            # width=800,
            # height=520,
            plot_bgcolor="#1f2c56",
            paper_bgcolor="#1f2c56",
            hovermode="closest",
            title={
                "text": "<b>" + "Total Cases : " + (barangay) + "</b>",
                "y": 0.93,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            },
            titlefont={"color": "white", "size": 15},
            legend={
                "orientation": "h",
                "bgcolor": "#1f2c56",
                "xanchor": "center",
                "x": 0.5,
                "y": -0.07,
            },
            font=dict(family="sans-serif", size=12, color="white"),
        ),
    }


def range_age(person_age):
    satinize_age = person_age.split(" ")[0]
    age = satinize_age.split("-")

    x_range = int(age[0])
    y_range = int(age[1])
    x_count = []

    xy_range = range(x_range, y_range + 1)

    for i in xy_range:
        dict_item = str(i)
        age_dict = {dict_item: 0}

        x_count.append(age_dict)

    return x_count


def person_count_age(person_range):
    age_range = next(iter(person_range))
    num_age = int(age_range)

    for i in person_demo_age_range:

        if num_age == i:
            str_age = str(num_age)
            person_range[str_age] = person_range[str_age] + 1
        else:
            pass

    return person_range


def x_coordinate_age(person_age):
    age_range = next(iter(person_age))

    return age_range


def counts_age(group):

    total_population = 0

    for x in group:
        num_age = list(x.values())[0]
        total_population = total_population + num_age

    return total_population


def age_percentage(whole, group):

    percentage_list = []
    if whole > 0:

        for x in group:
            num_age = list(x.values())[0]
            percent = round(100 * float(num_age) / float(whole))
            percentage = str(percent) + "%"
            percentage_list.append(percentage)
    else:

        percentage_list = ["0%", "0%", "0%", "0%", "0%", "0%", "0%", "0%", "0%", "0%"]

    return percentage_list


def datetime_list(covid_cases, weekly_data):

    latest_date = weekly_data["Date"].iloc[-1]
    ending_date_parse = str(latest_date).split(" ")[0]

    start_date = weekly_data["Date"].iloc[0]
    start_date_parse = str(start_date).split(" ")[0]

    if covid_cases == "Infection":

        date_list = (
            pd.date_range(start=start_date_parse, end=ending_date_parse, freq="W-SUN")
            .to_pydatetime()
            .tolist()
        )
    elif covid_cases == "Recoveries":

        date_list = (
            pd.date_range(start=start_date_parse, end=ending_date_parse, freq="W-SUN")
            .to_pydatetime()
            .tolist()
        )

    date_new_list = []

    for date in date_list:

        date_ptime = dt.strptime(str(date).split(" ")[0], "%Y-%m-%d")
        date_new_list.append(date_ptime)

    return date_new_list


@app.callback(
    Output("demo_line_chart", "figure"),
    [
        Input("zones_barangay", "value"),
        Input("barangay", "value"),
        Input("demo_cases", "value"),
        Input("demo_age", "value"),
        Input("demo_gender", "value"),
    ],
)
def update_graph(zones_barangay, barangay, demo_cases, demo_age, demo_gender):

    if demo_cases == "Infection":

        zone_infection_barangay = db.selecting_barangay_infection()
        zone_infection_barangay = zone_infection_barangay.rename(
            columns={
                "dateinfection": "Infection",
                "age": "Age",
                "gender": "Sex",
                "zones": "Zones",
                "address": "Address",
            }
        )
        zone_infection_barangay["Infection"] = zone_infection_barangay[
            "Infection"
        ].astype(str)

        spec_zone_infection = zone_infection_barangay[
            zone_infection_barangay["Zones"] == zones_barangay
        ]

        spec_barangay = spec_zone_infection[spec_zone_infection["Address"] == barangay]
    elif demo_cases == "Recoveries":
        zone_recoveries_barangay = db.selecting_barangay_recoveries()
        zone_recoveries_barangay = zone_recoveries_barangay.rename(
            columns={
                "daterecoveries": "Recoveries",
                "age": "Age",
                "gender": "Sex",
                "zones": "Zones",
                "address": "Address",
            }
        )
        zone_recoveries_barangay["Recoveries"] = zone_recoveries_barangay[
            "Recoveries"
        ].astype(str)

        spec_zone_recoveries = zone_recoveries_barangay[
            zone_recoveries_barangay["Zones"] == zones_barangay
        ]

        spec_barangay = spec_zone_recoveries[
            spec_zone_recoveries["Address"] == barangay
        ]
    elif demo_cases == "Deaths":
        zone_deaths_barangay = db.selecting_barangay_deaths()
        zone_deaths_barangay = zone_deaths_barangay.rename(
            columns={
                "datedeaths": "Deaths",
                "age": "Age",
                "gender": "Sex",
                "zones": "Zones",
                "address": "Address",
            }
        )
        zone_deaths_barangay["Deaths"] = zone_deaths_barangay["Deaths"].astype(str)
        spec_zone_deaths = zone_deaths_barangay[
            zone_deaths_barangay["Zones"] == zones_barangay
        ]

        spec_barangay = spec_zone_deaths[spec_zone_deaths["Address"] == barangay]

    global person_demo_age_range
    person_demo_age_range = []
    demo_person_age_range = range_age(demo_age)

    person_gender = gender_find(demo_gender, spec_barangay)
    person_demo_age_range = person_gender["Age"]

    result = list(map(person_count_age, demo_person_age_range))
    result2 = counts_age(result)

    age_group_percentage = age_percentage(result2, result)
    x_coordinate = list(map(x_coordinate_age, demo_person_age_range))
    y_coordinate = list(map(coordinate_y, result))

    x_series = pd.Series(x_coordinate, dtype="object")
    y_series = pd.Series(y_coordinate, dtype="object")

    """frame = {
        "Zone": zones_barangay,
        "Infection": y_series,
        "Group": x_series,
        "Percentage": age_group_percentage,
    }"""
    frame = {
        "Zone": barangay,
        "Infection": y_series,
        "Group": x_series,
        "Percentage": age_group_percentage,
    }
    group_results = pd.DataFrame(frame)

    return {
        "data": [
            go.Bar(
                x=x_series,
                y=y_series,
                name="confirmed Infection",
                marker=dict(color="orange"),
                hoverinfo="text",
                hovertext="<b>Age</b>: "
                + group_results[group_results["Zone"] == barangay]["Group"].astype(str)
                + "<br>"
                + "<b>Number of "
                + demo_cases
                + "</b>: "
                + group_results[group_results["Zone"] == barangay]["Infection"].astype(
                    str
                )
                + "<br>"
                + "<b>Age Percentage</b>: "
                + group_results[group_results["Zone"] == barangay]["Percentage"].astype(
                    str
                )
                + "<br>",
            )
        ],
        "layout": go.Layout(
            plot_bgcolor="#1f2c56",
            paper_bgcolor="#1f2c56",
            title={
                "text": "<b>"
                + demo_gender
                + " "
                + demo_cases
                + " "
                + "Cases In : "
                + (barangay)
                + "</b>",
                "y": 0.93,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            },
            titlefont={"color": "white", "size": 15},
            hovermode="x",
            margin=dict(r=0),
            xaxis=dict(
                title="<b>Age Range</b>",
                color="white",
                showline=True,
                showgrid=True,
                showticklabels=True,
                linecolor="white",
                linewidth=2,
                ticks="outside",
                tickfont=dict(family="Arial", size=12, color="white"),
            ),
            yaxis=dict(
                title="<b>Number Of " + demo_cases + " Cases</b>",
                color="white",
                showline=True,
                showgrid=True,
                showticklabels=True,
                linecolor="white",
                linewidth=2,
                ticks="outside",
                tickfont=dict(family="Arial", size=12, color="white"),
            ),
            legend={
                "orientation": "h",
                "bgcolor": "#1f2c56",
                "xanchor": "center",
                "x": 0.5,
                "y": -0.3,
            },
            font=dict(family="sans-serif", size=12, color="white"),
            transition=dict(duration=500, easing="cubic-in-out"),
        ),
    }


def calculate_population_percentage(person, group):

    percentage_list = []

    for x in group:
        num_age = list(x.values())[0]
        percent = round(100 * float(num_age) / float(person))
        percentage = str(percent) + "%"
        percentage_list.append(percentage)

    return percentage_list


# Create bar chart (show new cases)
@app.callback(
    Output("demo_case_population", "value"),
    [
        Input("zones_barangay", "value"),
        Input("barangay", "value"),
        Input("demo_cases", "value"),
        Input("demo_age", "value"),
        Input("demo_gender", "value"),
    ],
)
def update_population(zones_barangay, barangay, demo_cases, demo_age, demo_gender):

    if demo_cases == "Infection":
        spec_zone_infection = zone_infection_barangay[
            zone_infection_barangay["Zones"] == zones_barangay
        ]

        spec_barangay = spec_zone_infection[spec_zone_infection["Address"] == barangay]
    elif demo_cases == "Recoveries":
        spec_zone_recoveries = zone_recoveries_barangay[
            zone_recoveries_barangay["Zones"] == zones_barangay
        ]

        spec_barangay = spec_zone_recoveries[
            spec_zone_recoveries["Address"] == barangay
        ]
    elif demo_cases == "Deaths":
        spec_zone_deaths = zone_deaths_barangay[
            zone_deaths_barangay["Zones"] == zones_barangay
        ]

        spec_barangay = spec_zone_deaths[spec_zone_deaths["Address"] == barangay]

    demo_person_age_range = range_age(demo_age)
    person_gender = gender_find(demo_gender, spec_barangay)

    global person_demo_age_range
    person_demo_age_range = []
    person_demo_age_range = person_gender["Age"]

    result1 = list(map(person_count_age, demo_person_age_range))

    result2 = counts_age(result1)

    return str(result2) + " " + demo_gender + " " + demo_cases + " " + "Cases"


# Create bar chart (show new cases)
@app.callback(
    Output("barangay_case_population", "value"),
    [
        Input("zones_barangay", "value"),
        Input("barangay", "value"),
        Input("cases", "value"),
        Input("gender", "value"),
    ],
)
def update_population(zones_barangay, barangay, cases, gender):

    if cases == "Infection":
        spec_zone_infection = zone_infection_barangay[
            zone_infection_barangay["Zones"] == zones_barangay
        ]

        spec_barangay = spec_zone_infection[spec_zone_infection["Address"] == barangay]
    elif cases == "Recoveries":
        spec_zone_recoveries = zone_recoveries_barangay[
            zone_recoveries_barangay["Zones"] == zones_barangay
        ]

        spec_barangay = spec_zone_recoveries[
            spec_zone_recoveries["Address"] == barangay
        ]
    elif cases == "Deaths":
        spec_zone_deaths = zone_deaths_barangay[
            zone_deaths_barangay["Zones"] == zones_barangay
        ]

        spec_barangay = spec_zone_deaths[spec_zone_deaths["Address"] == barangay]

    person_gender = gender_find(gender, spec_barangay)
    total_gender_population = len(person_gender)

    return str(total_gender_population) + " " + gender + " " + cases + " " + "Cases"


# Create bar chart (show new cases)
@app.callback(
    Output("case_population", "value"),
    [
        Input("zones_barangay", "value"),
        Input("zone_cases", "value"),
        Input("zone_gender", "value"),
    ],
)
def update_population(zones_barangay, zone_cases, zone_gender):

    if zone_cases == "Infection":
        spec_barangay = zone_infection_barangay[
            zone_infection_barangay["Zones"] == zones_barangay
        ]

    elif zone_cases == "Recoveries":
        spec_barangay = zone_recoveries_barangay[
            zone_recoveries_barangay["Zones"] == zones_barangay
        ]
    elif zone_cases == "Deaths":
        spec_barangay = zone_deaths_barangay[
            zone_deaths_barangay["Zones"] == zones_barangay
        ]

    person_gender = gender_find(zone_gender, spec_barangay)
    gender_total_population = len(person_gender)

    return (
        str(gender_total_population)
        + " "
        + zone_gender
        + " "
        + zone_cases
        + " "
        + "Cases"
    )


@app.callback(
    Output("zone_population", "value"),
    [Input("zones_barangay", "value"), Input("zone_gender", "value"),],
)
def update_population(zones_barangay, zone_gender):

    zones_population = zone_data[zone_data["Zone"] == zones_barangay]

    if zone_gender == "All":
        male_population = zones_population["Male"].iloc[0]
        female_population = zones_population["Female"].iloc[0]
        gender_population = male_population + female_population
    else:
        gender_population = zones_population[zone_gender].iloc[0]

    return str(gender_population) + " " + zone_gender + " " + "Population"


# Create bar chart (show new cases)
@app.callback(
    Output("zone_line_chart", "figure"),
    [
        Input("zones_barangay", "value"),
        Input("zone_gender", "value"),
        Input("zone_cases", "value"),
    ],
)
def update_graph(zones_barangay, zone_gender, zone_cases):

    if zone_cases == "Infection":

        zone_infection_barangay = db.selecting_barangay_infection()
        zone_infection_barangay = zone_infection_barangay.rename(
            columns={
                "dateinfection": "Infection",
                "age": "Age",
                "gender": "Sex",
                "zones": "Zones",
                "address": "Address",
            }
        )
        zone_infection_barangay["Infection"] = zone_infection_barangay[
            "Infection"
        ].astype(str)
        spec_barangay = zone_infection_barangay[
            zone_infection_barangay["Zones"] == zones_barangay
        ]

    elif zone_cases == "Recoveries":
        zone_recoveries_barangay = db.selecting_barangay_recoveries()
        zone_recoveries_barangay = zone_recoveries_barangay.rename(
            columns={
                "daterecoveries": "Recoveries",
                "age": "Age",
                "gender": "Sex",
                "zones": "Zones",
                "address": "Address",
            }
        )
        zone_recoveries_barangay["Recoveries"] = zone_recoveries_barangay[
            "Recoveries"
        ].astype(str)
        spec_barangay = zone_recoveries_barangay[
            zone_recoveries_barangay["Zones"] == zones_barangay
        ]
    elif zone_cases == "Deaths":
        zone_deaths_barangay = db.selecting_barangay_deaths()
        zone_deaths_barangay = zone_deaths_barangay.rename(
            columns={
                "datedeaths": "Deaths",
                "age": "Age",
                "gender": "Sex",
                "zones": "Zones",
                "address": "Address",
            }
        )
        zone_deaths_barangay["Deaths"] = zone_deaths_barangay["Deaths"].astype(str)
        spec_barangay = zone_deaths_barangay[
            zone_deaths_barangay["Zones"] == zones_barangay
        ]

    global zone_age_range

    zone_population = zone_data[zone_data["Zone"] == zones_barangay]

    x_count = [
        {"1-10": 0},
        {"11-20": 0},
        {"21-30": 0},
        {"31-40": 0},
        {"41-50": 0},
        {"51-60": 0},
        {"61-70": 0},
        {"71-80": 0},
        {"81-90": 0},
        {"91-100": 0},
    ]

    person_gender = gender_find(zone_gender, spec_barangay)
    zone_age_range = person_gender["Age"]
    result = list(map(zone_counting_age, x_count))
    age_group_percentage = percentage(person_gender, result)
    
    if zone_gender == "All":
        male_population = zone_population["Male"].iloc[0]
        female_population = zone_population["Female"].iloc[0]
        total_population = male_population + female_population
        population_percetage = calculate_population_percentage(
            total_population, result
        )

    else:
        print("I am hereeeeeeeeeeeeeeeee")
        print(zone_population)
        population_percetage = calculate_population_percentage(
            zone_population[zone_gender].iloc[0], result
        )
        

    x_coordinate = [
        "1-10",
        "11-20",
        "21-30",
        "31-40",
        "41-50",
        "51-60",
        "61-70",
        "71-80",
        "81-90",
        "91-100",
    ]
    y_coordinate = list(map(coordinate_y, result))

    x_series = pd.Series(x_coordinate, dtype="object")
    y_series = pd.Series(y_coordinate, dtype="object")

    frame = {
        "Zone": zones_barangay,
        "Infection": y_series,
        "Group": x_series,
        "Percentage": age_group_percentage,
        "Population": population_percetage,
    }

    group_results = pd.DataFrame(frame)

    return {
        "data": [
            go.Bar(
                x=x_series,
                y=y_series,
                name="confirmed Infection",
                marker=dict(color="orange"),
                hoverinfo="text",
                hovertext="<b>Age Group</b>: "
                + group_results[group_results["Zone"] == zones_barangay][
                    "Group"
                ].astype(str)
                + "<br>"
                + "<b>Number of "
                + zone_cases
                + "</b>: "
                + group_results[group_results["Zone"] == zones_barangay][
                    "Infection"
                ].astype(str)
                + "<br>"
                + "<b>"
                + zone_cases
                + "</b>"
                + " "
                + "<b>Percentage</b>: "
                + group_results[group_results["Zone"] == zones_barangay][
                    "Percentage"
                ].astype(str)
                + "<br>"
                + "<b>"
                + "Population Percentage"
                + "</b>: "
                + group_results[group_results["Zone"] == zones_barangay][
                    "Population"
                ].astype(str),
            )
        ],
        "layout": go.Layout(
            plot_bgcolor="#1f2c56",
            paper_bgcolor="#1f2c56",
            title={
                "text": "<b>"
                + zone_gender
                + " "
                + zone_cases
                + " "
                + "Cases In : "
                + (zones_barangay)
                + "</b>",
                "y": 0.93,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            },
            titlefont={"color": "white", "size": 15},
            hovermode="x",
            margin=dict(r=0),
            xaxis=dict(
                title="<b>Age Range</b>",
                color="white",
                showline=True,
                showgrid=True,
                showticklabels=True,
                linecolor="white",
                linewidth=2,
                ticks="outside",
                tickfont=dict(family="Arial", size=12, color="white"),
            ),
            yaxis=dict(
                title="<b>Number Of " + zone_cases + " Cases</b>",
                color="white",
                showline=True,
                showgrid=True,
                showticklabels=True,
                linecolor="white",
                linewidth=2,
                ticks="outside",
                tickfont=dict(family="Arial", size=12, color="white"),
            ),
            legend={
                "orientation": "h",
                "bgcolor": "#1f2c56",
                "xanchor": "center",
                "x": 0.5,
                "y": -0.3,
            },
            font=dict(family="sans-serif", size=12, color="white"),
            transition=dict(duration=500, easing="cubic-in-out"),
        ),
    }


# Create bar chart (show new cases)
@app.callback(
    Output("line_chart", "figure"),
    [
        Input("barangay", "value"),
        Input("gender", "value"),
        Input("cases", "value"),
        Input("zones_barangay", "value"),
    ],
)
def update_graph(
    barangay, gender, cases, zones_barangay,
):

    if cases == "Infection":

        zone_infection_barangay = db.selecting_barangay_infection()
        zone_infection_barangay = zone_infection_barangay.rename(
            columns={
                "dateinfection": "Infection",
                "age": "Age",
                "gender": "Sex",
                "zones": "Zones",
                "address": "Address",
            }
        )
        zone_infection_barangay["Infection"] = zone_infection_barangay[
            "Infection"
        ].astype(str)

        spec_zone_infection = zone_infection_barangay[
            zone_infection_barangay["Zones"] == zones_barangay
        ]

        spec_barangay = spec_zone_infection[spec_zone_infection["Address"] == barangay]
    elif cases == "Recoveries":
        zone_recoveries_barangay = db.selecting_barangay_recoveries()
        zone_recoveries_barangay = zone_recoveries_barangay.rename(
            columns={
                "daterecoveries": "Recoveries",
                "age": "Age",
                "gender": "Sex",
                "zones": "Zones",
                "address": "Address",
            }
        )
        zone_recoveries_barangay["Recoveries"] = zone_recoveries_barangay[
            "Recoveries"
        ].astype(str)

        spec_zone_recoveries = zone_recoveries_barangay[
            zone_recoveries_barangay["Zones"] == zones_barangay
        ]

        spec_barangay = spec_zone_recoveries[
            spec_zone_recoveries["Address"] == barangay
        ]
    elif cases == "Deaths":
        zone_deaths_barangay = db.selecting_barangay_deaths()
        zone_deaths_barangay = zone_deaths_barangay.rename(
            columns={
                "datedeaths": "Deaths",
                "age": "Age",
                "gender": "Sex",
                "zones": "Zones",
                "address": "Address",
            }
        )
        zone_deaths_barangay["Deaths"] = zone_deaths_barangay["Deaths"].astype(str)
        spec_zone_deaths = zone_deaths_barangay[
            zone_deaths_barangay["Zones"] == zones_barangay
        ]

        spec_barangay = spec_zone_deaths[spec_zone_deaths["Address"] == barangay]

    global person_age_range
    x_count = [
        {"1-10": 0},
        {"11-20": 0},
        {"21-30": 0},
        {"31-40": 0},
        {"41-50": 0},
        {"51-60": 0},
        {"61-70": 0},
        {"71-80": 0},
        {"81-90": 0},
        {"91-100": 0},
    ]

    person_gender = gender_find(gender, spec_barangay)
    person_age_range = person_gender["Age"]
    result = list(map(counting_age, x_count))

    age_group_percentage = percentage(person_gender, result)
    x_coordinate = [
        "1-10",
        "11-20",
        "21-30",
        "31-40",
        "41-50",
        "51-60",
        "61-70",
        "71-80",
        "81-90",
        "91-100",
    ]
    y_coordinate = list(map(coordinate_y, result))

    x_series = pd.Series(x_coordinate, dtype="object")
    y_series = pd.Series(y_coordinate, dtype="object")

    frame = {
        "Barangay": barangay,
        "Infection": y_series,
        "Group": x_series,
        "Percentage": age_group_percentage,
    }

    group_results = pd.DataFrame(frame)

    return {
        "data": [
            go.Bar(
                x=x_series,
                y=y_series,
                name="confirmed Infection",
                marker=dict(color="orange"),
                hoverinfo="text",
                hovertext="<b>Age Group</b>: "
                + group_results[group_results["Barangay"] == barangay]["Group"].astype(
                    str
                )
                + "<br>"
                + "<b>Number of "
                + cases
                + "</b>: "
                + group_results[group_results["Barangay"] == barangay][
                    "Infection"
                ].astype(str)
                + "<br>"
                + "<b>Percentage</b>: "
                + group_results[group_results["Barangay"] == barangay][
                    "Percentage"
                ].astype(str),
            )
        ],
        "layout": go.Layout(
            plot_bgcolor="#1f2c56",
            paper_bgcolor="#1f2c56",
            title={
                "text": "<b>"
                + gender
                + " "
                + cases
                + " "
                + "Cases In : "
                + (barangay)
                + "</b>",
                "y": 0.93,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            },
            titlefont={"color": "white", "size": 15},
            hovermode="x",
            margin=dict(r=0),
            xaxis=dict(
                title="<b>Age Range</b>",
                color="white",
                showline=True,
                showgrid=True,
                showticklabels=True,
                linecolor="white",
                linewidth=2,
                ticks="outside",
                tickfont=dict(family="Arial", size=12, color="white"),
            ),
            yaxis=dict(
                title="<b>Number Of " + cases + " Cases</b>",
                color="white",
                showline=True,
                showgrid=True,
                showticklabels=True,
                linecolor="white",
                linewidth=2,
                ticks="outside",
                tickfont=dict(family="Arial", size=12, color="white"),
            ),
            legend={
                "orientation": "h",
                "bgcolor": "#1f2c56",
                "xanchor": "center",
                "x": 0.5,
                "y": -0.3,
            },
            font=dict(family="sans-serif", size=12, color="white"),
            transition=dict(duration=500, easing="cubic-in-out"),
        ),
    }


@app.callback(
    Output("line_chart_weekly_infection", "figure"),
    [Input("interval-component", "n_intervals")],
)
def update_graph_weekly(n):

    zones_barangay = "Zone 1"
    weekly_infection = db.selecting_infection()
    weekly_infection["dateinfection"] = pd.to_datetime(weekly_infection["dateinfection"])
    weekly_infection.set_index("dateinfection", inplace=True)
    raw_data_infection = weekly_infection["infection"].resample("W").sum()
    raw_data_weekly_infection = raw_data_infection.reset_index()

    raw_data_weekly_infection = raw_data_weekly_infection.rename(
        columns={"dateinfection": "Date", "infection":"Infection"}
    )

    covid_data_1 = raw_data_weekly_infection
    date_new_list = datetime_list("Infection", covid_data_1)
    temporary_dictionary = {"Date": date_new_list}
    dates_df = pd.DataFrame(temporary_dictionary)

    new_df = covid_data_1.merge(dates_df, how="right", on="Date")
    new_df["Date"] = new_df["Date"].apply(
        lambda x: pd.to_datetime(str(x).split(" ")[0])
    )

    
    training_percentage = 0.50
    validation_percentage = 0.25
    length_dataframe = len(new_df)

    training_data_percentage = round(int(length_dataframe * training_percentage))
    validation_data_percentage = round(int(length_dataframe * validation_percentage))
    validation_size = training_data_percentage + validation_data_percentage
    training_df = new_df[0:training_data_percentage]
    validation_df = new_df[training_data_percentage:validation_size]
    testing_df = new_df[validation_size:]
    length_testing = len(testing_df)

    training_array = np.array(training_df["Infection"])
    validation_array = np.array(validation_df["Infection"])
    testing_array = np.array(testing_df["Infection"])
    training_array = training_array.reshape(training_data_percentage, 1)
    validation_array = validation_array.reshape(validation_data_percentage, 1)
    testing_array = testing_array.reshape(length_testing, 1)

    history = [element for element in training_array]
    predictions = list()
    bias = 2.0036779999999936

    for index in range(len(testing_array)):
        arima_model_ = SARIMAX(
            history,
            order=(1, 0, 0),
            seasonal_order=(0, 0, 0, 0),
            enforce_stationarity=False,
            enforce_invertibility=False,
        )
        fitted_arima_ = arima_model_.fit(trend="nc", disp=0)
        predicted_value = fitted_arima_.forecast()[0]
        predictions.append(predicted_value + bias)
        history.append(testing_array[index])

    latest_date = testing_df["Date"].iloc[-1]
    ending_date_parse = str(latest_date).split(" ")[0]

    testing_start_date = testing_df["Date"].iloc[0]
    start_date_parse = str(testing_start_date).split(" ")[0]
    testing_date_list = (
        pd.date_range(start=start_date_parse, end=ending_date_parse, freq="W-SUN")
        .to_pydatetime()
        .tolist()
    )

    testing_list = testing_array
    temporary_dictionary = {"Date": testing_date_list}
    testing_set = pd.DataFrame(temporary_dictionary)
    testing_set["Infection"] = testing_list
    testing_set.set_index("Date", inplace=True)

    testing_set = testing_set.reset_index()
    training_df = pd.concat([training_df, testing_set])

    training_infection = (
        training_df.groupby(["Date"])[["Infection"]].sum().reset_index()
    )
    training_infection.set_index("Date", inplace=True)

    model = SARIMAX(
        training_infection["Infection"].astype(float),
        order=(1, 0, 0),
        seasonal_order=(0, 0, 0, 0),
    )
    model_fit = model.fit()

    pred_date = [
        training_infection.index[-1] + DateOffset(weeks=x) for x in range(1, 2)
    ]
    pred_date = pd.DataFrame(index=pred_date[0:], columns=training_infection.columns)
    pred_date = pred_date.reset_index()
    pred_date = pred_date.rename(columns={"index": "Date"})

    training_infection = training_infection.reset_index()
    training_infection = pd.concat([training_infection, pred_date])

    start_index = len(training_infection["Infection"]) - 1
    end_index = len(training_infection["Infection"]) - 1
    prediction = model_fit.predict(start=start_index, end=end_index)
    prediction = prediction.reset_index()
    prediction = prediction.rename(columns={0: "Infection"})

    infection_num = int(prediction["Infection"].iloc[-1:][0])
    training_infection["Infection"].iloc[-1:] = infection_num
    training_infection.set_index("Date", inplace=True)

    prediction_infection = training_infection.iloc[-1:]
    prediction_infection = prediction_infection.reset_index()

    covid_data_1 = pd.concat([covid_data_1, prediction_infection])

    covid_data_1["Rolling Average"] = covid_data_1["Infection"].rolling(window=4).mean()

    weekly_date = covid_data_1["Date"].tail(8)
    number_infected = covid_data_1["Infection"].tail(8)
    rolling_average = covid_data_1["Rolling Average"].tail(8)

    frame = {
        "Barangay": zones_barangay,
        "Date": weekly_date,
        "Infection": number_infected,
        "Rolling Average": rolling_average,
    }

    results = pd.DataFrame(frame)
    colors = [
        "orange",
        "orange",
        "orange",
        "orange",
        "orange",
        "orange",
        "orange",
        "gray",
    ]

    #colorbar=dict(bgcolor="#ff0000")
    return {
        "data": [
            go.Bar(
                x=weekly_date,
                y=number_infected,
                name="Prediction Value",
                marker=dict(color=colors, colorbar=dict(bgcolor="#ff0000")),
                hoverinfo="text",
                hovertext="<b>Date</b>: "
                + results[results["Barangay"] == zones_barangay]["Date"].astype(str)
                + "<br>"
                + "<b>Weekly Confirmed</b>: "
                + results[results["Barangay"] == zones_barangay]["Infection"].astype(
                    str
                ),
            ),
            go.Scatter(
                x=results[results["Barangay"] == zones_barangay]["Date"],
                y=results[results["Barangay"] == zones_barangay]["Rolling Average"],
                mode="lines",
                name="Rolling average of the last four weeks - Weekly Infection Cases",
                line=dict(width=3, color="#FF00FF"),
                hoverinfo="text",
                hovertext="<b>Date</b>: "
                + results[results["Barangay"] == zones_barangay]["Date"].astype(str)
                + "<br>"
                + "<b>Rolling Ave. (last 4 weeks)</b>: "
                + results[results["Barangay"] == zones_barangay][
                    "Rolling Average"
                ].astype(str)
                + "<br>"
                # marker=dict(
                #     color='green'),
            ),
        ],
        "layout": go.Layout(
            plot_bgcolor="#1f2c56",
            paper_bgcolor="#1f2c56",
            title={
                "text": "Predictive Confirmed Cases In : " + "Barangay Carmen",
                "y": 0.93,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            },
            titlefont={"color": "white", "size": 20},
            hovermode="x",
            margin=dict(r=0),
            xaxis=dict(
                title="<b>Date</b>",
                color="white",
                showline=True,
                showgrid=True,
                showticklabels=True,
                linecolor="white",
                linewidth=2,
                ticks="outside",
                tickfont=dict(family="Arial", size=12, color="white"),
            ),
            yaxis=dict(
                title="<b>Weekly Confirmed Cases</b>",
                color="white",
                showline=True,
                showgrid=True,
                showticklabels=True,
                linecolor="white",
                linewidth=2,
                ticks="outside",
                tickfont=dict(family="Arial", size=12, color="white"),
            ),
            legend={
                "orientation": "v",
                "bgcolor": "#1f2c56",
                "xanchor": "center",
                "x": 0.5,
                "y": -0.5,
            },
            font=dict(family="sans-serif", size=12, color="white"),
        ),
    }


@app.callback(
    Output("line_chart_weekly_recoveries", "figure"),
    [Input("interval-component", "n_intervals")],
)
def update_graph_weekly(n):
    zones_barangay = "Zone 1"
    weekly_recoveries = db.selecting_recoveries()
    
    weekly_recoveries["daterecoveries"] = pd.to_datetime(weekly_recoveries["daterecoveries"])
    weekly_recoveries.set_index("daterecoveries", inplace=True)

    raw_data_recoveries = weekly_recoveries["recoveries"].resample("W").sum()
    raw_data_weekly_recoveries = raw_data_recoveries.reset_index()

    raw_data_weekly_recoveries = raw_data_weekly_recoveries.rename(
        columns={"daterecoveries": "Date", "recoveries":"Recoveries"}
    )


    covid_data_1 = raw_data_weekly_recoveries
    date_new_list = datetime_list("Recoveries", covid_data_1)
    temporary_dictionary = {"Date": date_new_list}
    dates_df = pd.DataFrame(temporary_dictionary)

    new_df = covid_data_1.merge(dates_df, how="right", on="Date")
    new_df["Date"] = new_df["Date"].apply(
        lambda x: pd.to_datetime(str(x).split(" ")[0])
    )

    training_percentage = 0.50
    validation_percentage = 0.25
    length_dataframe = len(new_df)

    training_data_percentage = round(int(length_dataframe * training_percentage))
    validation_data_percentage = round(int(length_dataframe * validation_percentage))
    validation_size = training_data_percentage + validation_data_percentage
    training_df = new_df[0:training_data_percentage]
    validation_df = new_df[training_data_percentage:validation_size]
    testing_df = new_df[validation_size:]
    length_testing = len(testing_df)

    training_array = np.array(training_df["Recoveries"])
    validation_array = np.array(validation_df["Recoveries"])
    testing_array = np.array(testing_df["Recoveries"])

    training_array = training_array.reshape(training_data_percentage, 1)
    validation_array = validation_array.reshape(validation_data_percentage, 1)
    testing_array = testing_array.reshape(length_testing, 1)

    history = [element for element in training_array]
    predictions = list()
    bias = 2.773577000000003

    for index in range(len(testing_array)):
        arima_model_ = SARIMAX(
            history,
            order=(1, 0, 0),
            seasonal_order=(0, 0, 0, 0),
            enforce_stationarity=False,
            enforce_invertibility=False,
        )
        fitted_arima_ = arima_model_.fit(trend="nc", disp=0)
        predicted_value = fitted_arima_.forecast()[0]
        predictions.append(predicted_value + bias)
        history.append(testing_array[index])

    latest_date = testing_df["Date"].iloc[-1]
    ending_date_parse = str(latest_date).split(" ")[0]

    testing_start_date = testing_df["Date"].iloc[0]
    start_date_parse = str(testing_start_date).split(" ")[0]

    testing_date_list = (
        pd.date_range(start=start_date_parse, end=ending_date_parse, freq="W-SUN")
        .to_pydatetime()
        .tolist()
    )

    testing_list = testing_array
    predictions_list = predictions
    temporary_dictionary = {"Date": testing_date_list}
    testing_set = pd.DataFrame(temporary_dictionary)
    testing_set["Recoveries"] = testing_list
    testing_set.set_index("Date", inplace=True)

    testing_set = testing_set.reset_index()
    training_df = pd.concat([training_df, testing_set])

    training_recoveries = (
        training_df.groupby(["Date"])[["Recoveries"]].sum().reset_index()
    )
    training_recoveries.set_index("Date", inplace=True)

    model = SARIMAX(
        training_recoveries["Recoveries"].astype(float),
        order=(1, 0, 0),
        seasonal_order=(0, 0, 0, 0),
    )
    model_fit = model.fit()

    pred_date = [
        training_recoveries.index[-1] + DateOffset(weeks=x) for x in range(1, 2)
    ]
    pred_date = pd.DataFrame(index=pred_date[0:], columns=training_recoveries.columns)
    pred_date = pred_date.reset_index()
    pred_date = pred_date.rename(columns={"index": "Date"})

    training_recoveries = training_recoveries.reset_index()
    training_recoveries = pd.concat([training_recoveries, pred_date])

    start_index = len(training_recoveries["Recoveries"]) - 1
    end_index = len(training_recoveries["Recoveries"]) - 1
    prediction = model_fit.predict(start=start_index, end=end_index)
    prediction = prediction.reset_index()
    prediction = prediction.rename(columns={0: "Recoveries"})

    recoveries_num = int(prediction["Recoveries"].iloc[-1:][0])
    training_recoveries["Recoveries"].iloc[-1:] = recoveries_num
    training_recoveries.set_index("Date", inplace=True)

    prediction_recoveries = training_recoveries.iloc[-1:]
    prediction_recoveries = prediction_recoveries.reset_index()

    covid_data_1 = pd.concat([covid_data_1, prediction_recoveries])
    covid_data_1["Rolling Average"] = (
        covid_data_1["Recoveries"].rolling(window=4).mean()
    )

    weekly_date = covid_data_1["Date"].tail(8)
    number_infected = covid_data_1["Recoveries"].tail(8)
    rolling_average = covid_data_1["Rolling Average"].tail(8)

    frame = {
        "Barangay": zones_barangay,
        "Date": weekly_date,
        "Recoveries": number_infected,
        "Rolling Average": rolling_average,
    }

    results = pd.DataFrame(frame)
    colors = [
        "yellow",
        "yellow",
        "yellow",
        "yellow",
        "yellow",
        "yellow",
        "yellow",
        "gray",
    ]

    #colorbar=dict(bgcolor="#ff0000")
    colors = [
        "yellow",
        "yellow",
        "yellow",
        "yellow",
        "yellow",
        "yellow",
        "yellow",
        "gray",
    ]

    return {
        "data": [
            go.Bar(
                x=weekly_date,
                y=number_infected,
                name="Predictions",
                marker=dict(color=colors, colorbar=dict(bgcolor="#ff0000")),
                hoverinfo="text",
                hovertext="<b>Date</b>: "
                + results[results["Barangay"] == zones_barangay]["Date"].astype(str)
                + "<br>"
                + "<b>Weekly Recoveries</b>: "
                + results[results["Barangay"] == zones_barangay]["Recoveries"].astype(
                    str
                ),
            ),
            go.Scatter(
                x=results[results["Barangay"] == zones_barangay]["Date"],
                y=results[results["Barangay"] == zones_barangay]["Rolling Average"],
                mode="lines",
                name="Rolling average of the last four weeks - Weekly Recoveries Cases",
                line=dict(width=3, color="#FF00FF"),
                hoverinfo="text",
                hovertext="<b>Date</b>: "
                + results[results["Barangay"] == zones_barangay]["Date"].astype(str)
                + "<br>"
                + "<b>Rolling Ave. (last 4 weeks)</b>: "
                + results[results["Barangay"] == zones_barangay][
                    "Rolling Average"
                ].astype(str)
                + "<br>"
                # marker=dict(
                #     color='green'),
            ),
        ],
        "layout": go.Layout(
            plot_bgcolor="#1f2c56",
            paper_bgcolor="#1f2c56",
            title={
                "text": "Predictive Recoveries Cases In : " + "Barangay Carmen",
                "y": 0.93,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            },
            titlefont={"color": "white", "size": 20},
            hovermode="x",
            margin=dict(r=0),
            xaxis=dict(
                title="<b>Date</b>",
                color="white",
                showline=True,
                showgrid=True,
                showticklabels=True,
                linecolor="white",
                linewidth=2,
                ticks="outside",
                tickfont=dict(family="Arial", size=12, color="white"),
            ),
            yaxis=dict(
                title="<b>Weekly Recoveries Cases</b>",
                color="white",
                showline=True,
                showgrid=True,
                showticklabels=True,
                linecolor="white",
                linewidth=2,
                ticks="outside",
                tickfont=dict(family="Arial", size=12, color="white"),
            ),
            legend={
                "orientation": "v",
                "bgcolor": "#1f2c56",
                "xanchor": "center",
                "x": 0.5,
                "y": -0.5,
            },
            font=dict(family="sans-serif", size=12, color="white"),
        ),
    }

@app.callback(
    Output("input_year", "value"), [Input("year_vaccination", "value")],
)
def update_doses(year_vaccination):

    statement = str(year_vaccination)

    return statement


@app.callback(
    Output("input_month", "value"), [Input("month_vaccination", "value")],
)
def update_doses(month_vaccination):

    statement = str(month_vaccination)

    return statement


@app.callback(
    Output("doses", "value"),
    [
        Input("vaccination_dose", "value"),
        Input("year_vaccination", "value"),
        Input("month_vaccination", "value"),
        Input("interval-component", "n_intervals"),
    ],
)
def update_doses(vaccination_dose, year_vaccination, month_vaccination, n):
    statement = ""
    num_vaccination = ""
    vaccination = db.selecting_vaccination()
    vaccination = vaccination.rename(
        columns={
            "datevaccination": "Date",
            "firstdose": "FirstDose",
            "seconddose": "SecondDose",
            "thirddose": "ThirdDose",
        }
    )
    vaccination["Date"] = pd.to_datetime(vaccination["Date"])
    vaccination.set_index("Date", inplace=True)

    weekly_vaccination = (
        vaccination[["FirstDose", "SecondDose", "ThirdDose"]].resample("W").sum()
    )
    weekly_vaccination = weekly_vaccination.reset_index()
    weekly_vaccination["Year"] = weekly_vaccination["Date"].apply(
        lambda x: str(x).split("-")[0]
    )
    weekly_vaccination["Date"] = pd.to_datetime(weekly_vaccination["Date"])
    weekly_vaccination["months"] = weekly_vaccination["Date"].dt.month_name()

    if vaccination_dose == "1st Dose":

        dose = weekly_vaccination[["Date", "FirstDose", "Year", "months"]]
        dose["FirstDose"] = dose["FirstDose"].astype(int)
        dose = dose.rename(columns={"FirstDose": "Doses"})

        weekly_vaccination_year = dose[dose["Year"] == year_vaccination]

        if month_vaccination == "All":
            num_vaccination = weekly_vaccination_year["Doses"].sum()
        else:
            weekly_vaccination_month = weekly_vaccination_year[
                weekly_vaccination_year["months"] == month_vaccination
            ]

            num_vaccination = weekly_vaccination_month["Doses"].sum()

    elif vaccination_dose == "2nd Dose":

        dose = weekly_vaccination[["Date", "SecondDose", "Year", "months"]]
        dose["SecondDose"] = dose["SecondDose"].astype(int)
        dose = dose.rename(columns={"SecondDose": "Doses"})

        weekly_vaccination_year = dose[dose["Year"] == year_vaccination]

        if month_vaccination == "All":
            num_vaccination = weekly_vaccination_year["Doses"].sum()
        else:
            weekly_vaccination_month = weekly_vaccination_year[
                weekly_vaccination_year["months"] == month_vaccination
            ]

            num_vaccination = weekly_vaccination_month["Doses"].sum()

    elif vaccination_dose == "3rd Dose":

        dose = weekly_vaccination[["Date", "SecondDose", "Year", "months"]]
        dose["SecondDose"] = dose["SecondDose"].astype(int)
        dose = dose.rename(columns={"SecondDose": "Doses"})

        weekly_vaccination_year = dose[dose["Year"] == year_vaccination]

        if month_vaccination == "All":
            num_vaccination = weekly_vaccination_year["Doses"].sum()
        else:
            weekly_vaccination_month = weekly_vaccination_year[
                weekly_vaccination_year["months"] == month_vaccination
            ]

            num_vaccination = weekly_vaccination_month["Doses"].sum()

    statement = str(num_vaccination) + " " + vaccination_dose

    return statement


@app.callback(
    Output("line_chart_weekly_vaccination", "figure"),
    [
        Input("vaccination_dose", "value"),
        Input("year_vaccination", "value"),
        Input("month_vaccination", "value"),
        Input("interval-component", "n_intervals"),
    ],
)
def update_graph_weekly(vaccination_dose, year_vaccination, month_vaccination, n):

    vaccination = db.selecting_vaccination()
    vaccination = vaccination.rename(
        columns={
            "datevaccination": "Date",
            "firstdose": "FirstDose",
            "seconddose": "SecondDose",
            "thirddose": "ThirdDose",
        }
    )
    vaccination["Date"] = pd.to_datetime(vaccination["Date"])
    vaccination.set_index("Date", inplace=True)

    weekly_vaccination = (
        vaccination[["FirstDose", "SecondDose", "ThirdDose"]].resample("W").sum()
    )
    weekly_vaccination = weekly_vaccination.reset_index()
    weekly_vaccination["Year"] = weekly_vaccination["Date"].apply(
        lambda x: str(x).split("-")[0]
    )
    weekly_vaccination["Date"] = pd.to_datetime(weekly_vaccination["Date"])
    weekly_vaccination["months"] = weekly_vaccination["Date"].dt.month_name()

    """
    vaccination_year = weekly_vaccination["Year"].unique()

    vaccination_month = weekly_vaccination["months"].unique()
    vaccination_month = vaccination_month = sorted(
        vaccination_month, key=lambda m: datetime.strptime(m, "%B")
    )
    vaccination_month.append("All")"""

    if vaccination_dose == "1st Dose":

        dose = weekly_vaccination[["Date", "FirstDose", "Year", "months"]]
        dose["FirstDose"] = dose["FirstDose"].astype(int)
        dose = dose.rename(columns={"FirstDose": "Doses"})

        weekly_vaccination_year = dose[dose["Year"] == year_vaccination]

        if month_vaccination == "All":
            weekly_vaccination_month = weekly_vaccination_year
        else:
            weekly_vaccination_month = weekly_vaccination_year[
                weekly_vaccination_year["months"] == month_vaccination
            ]
    elif vaccination_dose == "2nd Dose":

        dose = weekly_vaccination[["Date", "SecondDose", "Year", "months"]]
        dose["SecondDose"] = dose["SecondDose"].astype(int)
        dose = dose.rename(columns={"SecondDose": "Doses"})

        weekly_vaccination_year = dose[dose["Year"] == year_vaccination]
        if month_vaccination == "All":
            weekly_vaccination_month = weekly_vaccination_year
        else:
            weekly_vaccination_month = weekly_vaccination_year[
                weekly_vaccination_year["months"] == month_vaccination
            ]
    elif vaccination_dose == "3rd Dose":

        dose = weekly_vaccination[["Date", "SecondDose", "Year", "months"]]
        dose["SecondDose"] = dose["SecondDose"].astype(int)
        dose = dose.rename(columns={"SecondDose": "Doses"})

        weekly_vaccination_year = dose[dose["Year"] == year_vaccination]
        if month_vaccination == "All":
            weekly_vaccination_month = weekly_vaccination_year
        else:
            weekly_vaccination_month = weekly_vaccination_year[
                weekly_vaccination_year["months"] == month_vaccination
            ]

    weekly_vaccination_month["Rolling Average"] = (
        weekly_vaccination_month["Doses"].rolling(window=4).mean()
    )

    if month_vaccination == "All":

        weekly_date = weekly_vaccination_month["Date"].tail(100)
        number_vaccination = weekly_vaccination_month["Doses"].tail(100)
        rolling_average = weekly_vaccination_month["Rolling Average"].tail(100)
    else:

        weekly_date = weekly_vaccination_month["Date"].tail(8)
        number_vaccination = weekly_vaccination_month["Doses"].tail(8)
        rolling_average = weekly_vaccination_month["Rolling Average"].tail(8)

    frame = {
        "Dose": vaccination_dose,
        "Date": weekly_date,
        "Vaccination": number_vaccination,
        "Rolling Average": rolling_average,
    }

    results = pd.DataFrame(frame)

    return {
        "data": [
            go.Bar(
                x=weekly_date,
                y=number_vaccination,
                name="Weekly Vaccination",
                marker=dict(color="orange"),
                hoverinfo="text",
                hovertext="<b>Date</b>: "
                + results[results["Dose"] == vaccination_dose]["Date"].astype(str)
                + "<br>"
                + "<b>Weekly Vaccination</b>: "
                + results[results["Dose"] == vaccination_dose]["Vaccination"].astype(
                    str
                ),
            ),
        ],
        "layout": go.Layout(
            plot_bgcolor="#1f2c56",
            paper_bgcolor="#1f2c56",
            title={
                "text": "Vaccination In : " + "Barangay Carmen",
                "y": 0.93,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            },
            titlefont={"color": "white", "size": 20},
            hovermode="x",
            margin=dict(r=0),
            xaxis=dict(
                title="<b>Date</b>",
                color="white",
                showline=True,
                showgrid=True,
                showticklabels=True,
                linecolor="white",
                linewidth=2,
                ticks="outside",
                tickfont=dict(family="Arial", size=12, color="white"),
            ),
            yaxis=dict(
                title="<b>Weekly Vaccination</b>",
                color="white",
                showline=True,
                showgrid=True,
                showticklabels=True,
                linecolor="white",
                linewidth=2,
                ticks="outside",
                tickfont=dict(family="Arial", size=12, color="white"),
            ),
            legend={
                "orientation": "v",
                "bgcolor": "#1f2c56",
                "xanchor": "center",
                "x": 0.5,
                "y": -0.5,
            },
            font=dict(family="sans-serif", size=12, color="white"),
            transition=dict(duration=500, easing="cubic-in-out"),
        ),
    }


if __name__ == "__main__":
    app.run_server(port=8050,debug=True)

