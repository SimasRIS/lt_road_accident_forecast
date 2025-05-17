import os
import numpy as np
import pandas as pd
import plotly.offline as pyo
import joblib
import logging
import tensorflow as tf
from tensorflow.keras import layers, models, regularizers
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from flask import Flask, render_template, request
from scripts.map_visualisation import create_map_div
from scripts.visualisation import (
    accidents_by_month,
    forecast_accidents_sma,
    plotly_death_forecast,
    analyze_deaths_by_gender_age_type,
    analyze_deaths_by_weekday
)
from scripts.model import prepare_sequence
from scripts.openai import describe_project, describe_chart
from dotenv import load_dotenv


BASEDIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASEDIR, 'data', 'processed')
MODELS_DIR = os.path.join(BASEDIR, 'models')
MODEL_PATH = os.path.join(MODELS_DIR, 'lstm_accident_model_final.keras')
EVENTS_CSV = os.path.join(DATA_DIR, 'cleaned_events.csv')
load_dotenv()
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.getenv('FLASK_SECRET_KEY')

if not os.getenv("OPENAI_API_KEY"):
    app.logger.error("OPENAI_API_KEY not found! AI features will fail.")
else:
    app.logger.info("OpenAI API key loaded successfully.")
# load model
model = tf.keras.models.load_model(MODEL_PATH)
# load LabelEncoder
le = joblib.load(os.path.join(MODELS_DIR, 'label_encoder.joblib'))

# load events data
events_df = pd.read_csv(EVENTS_CSV, parse_dates=['dataLaikas'])
events_df['date'] = events_df['dataLaikas'].dt.floor('d')

@app.route('/')
def home():
    return render_template('base.html', title='LTU Eismo Įvykiai')

@app.route('/visualisations', methods=['GET', 'POST'])
def visualisations():
    options = [
        ('by_month', 'Events by month', accidents_by_month),
        ('sma', 'Yearly SMA forecast', forecast_accidents_sma),
        ('death', 'Death trend', plotly_death_forecast),
        ('gender', 'Death distribution by gender', analyze_deaths_by_gender_age_type),
        ('weekday', 'Death by weekday', analyze_deaths_by_weekday),
    ]

    selected = (request.form.getlist('graphs')
                if request.method == 'POST'
                else [key for key, _, _ in options])

    graphs = []
    first = True
    for key, label, func in options:
        if key not in selected:
            continue

        fig = func(events_df)

        # Render the Plotly figure
        div = pyo.plot(fig,
                       include_plotlyjs='cdn' if first else False,
                       output_type='div')

        # **Directly** call the AI describer
        desc = describe_chart(fig, title=label)

        graphs.append({
            'div': div,
            'desc': desc,
            'label': label
        })
        first = False

    return render_template(
        'visualisations.html',
        options=options,
        selected=selected,
        graphs=graphs,
        title='Vizualizacijos'
    )

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    savivaldybes = sorted(events_df['savivaldybe'].unique())
    selected_municipality = ''
    selected_date = ''
    prediction = None

    if request.method == 'POST' and model is not None:
        selected_municipality = request.form['savivaldybe']
        selected_date       = request.form['date']

        # 1) Filter to that municipality
        df_sel = events_df[events_df['savivaldybe'] == selected_municipality].copy()

        # 2) Prepare the (1,30,1) sequence for the model
        seq = prepare_sequence(df_sel, seq_len=30)

        # 3) Lookup its code and build the second input
        mun_code = le.transform([selected_municipality])[0]
        mun_arr  = np.array([mun_code], dtype=np.int32)

        # 4) Predict with both inputs
        pred = model.predict([seq, mun_arr], verbose=0)
        prediction = int(pred.flatten()[0])


    return render_template(
        'predict.html',
        title='Prognozė',
        savivaldybes=savivaldybes,
        selected_municipality=selected_municipality,
        selected_date=selected_date,
        prediction=prediction
    )
@app.route('/map', methods=['GET', 'POST'])
def show_map():
    # 1) Load the same events CSV and parse dates
    df0 = pd.read_csv(EVENTS_CSV, parse_dates=['dataLaikas'])
    # 2) Build your filter dropdowns from the real columns
    categories = sorted(df0['rusis'].unique())
    years      = sorted(df0['metai'].unique())

    # 3) Read user selections (if any)
    if request.method == 'POST':
        cat = request.form.get('category') or None
        yr  = request.form.get('year')
        yr  = int(yr) if yr else None
    else:
        cat, yr = None, None

    # 4) Generate the map div
    map_div = create_map_div(EVENTS_CSV, category=cat, year=yr)

    # 5) Render, passing both lists into the template
    return render_template(
        'map.html',
        title='Žemėlapis',
        map_div=map_div,
        categories=categories,
        years=years,
        selected_category=cat,
        selected_year=yr
    )
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)