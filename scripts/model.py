import os
import numpy as np
import pandas as pd
from datetime import timedelta
import joblib
import tensorflow as tf
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras import layers, models, regularizers
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau


def load_and_aggregate(data_path: str) -> pd.DataFrame:
    """
    Įkelia eismo įvykių duomenis, agreguoja pagal savivaldybę ir dieną,
    koduoja savivaldybes ir išsaugo LabelEncoder.

    Returns:
        DataFrame su ['savivaldybe','date','accident_count','mun_code']
    """
    script_dir = os.path.abspath(os.path.dirname(__file__))
    models_dir = os.path.normpath(os.path.join(script_dir, '..', 'models'))
    os.makedirs(models_dir, exist_ok=True)

    events = pd.read_csv(data_path, parse_dates=['dataLaikas'])
    events['date'] = events['dataLaikas'].dt.floor('d')

    agg_df = (
        events.groupby(['savivaldybe','date'])
              .size()
              .reset_index(name='accident_count')
    )

    le = LabelEncoder()
    agg_df['mun_code'] = le.fit_transform(agg_df['savivaldybe'])
    joblib.dump(le, os.path.join(models_dir, 'label_encoder.joblib'))

    return agg_df


def prepare_sequence(df: pd.DataFrame, seq_len: int = 30) -> np.ndarray:
    """
    Paruošia seką LSTM modeliui:
    - Jei DataFrame turi 'accident_count', grąžina X_seq,y_seq,mun_seq (mokymui)
    - Priešingu atveju, traktuoja df kaip vienos savivaldybės neataggreguotus įrašus ir grąžina (1,seq_len,1)
    """
    # Mokymosi atvejis: naudoti grupuotą DataFrame
    if 'accident_count' in df.columns and 'mun_code' in df.columns:
        X, y, mun_ids = [], [], []
        for mun_id, grp in df.groupby('mun_code'):
            grp = grp.sort_values('date')
            counts = grp['accident_count'].values
            for i in range(len(counts) - seq_len):
                X.append(counts[i:i+seq_len])
                y.append(counts[i+seq_len])
                mun_ids.append(mun_id)
        X_seq = np.array(X).reshape(-1, seq_len, 1)
        y_seq = np.array(y)
        mun_seq = np.array(mun_ids)
        return X_seq, y_seq, mun_seq

    # Inference atvejis: raw arba filtruoti įrašai be accident_count
    if 'dataLaikas' in df.columns:
        df_inf = df.copy()
        df_inf['date'] = pd.to_datetime(df_inf['dataLaikas']).dt.floor('d')
        # Dalykinė laikotarpis
        last_date = df_inf['date'].max()
        start_date = last_date - timedelta(days=seq_len-1)
        counts = (
            df_inf.groupby('date').size()
        )
        full_idx = pd.date_range(start=start_date, end=last_date, freq='D')
        daily = counts.reindex(full_idx, fill_value=0).values
        return daily.reshape(1, seq_len, 1)

    raise ValueError("Negalima paruošti sekos: netinkamas DataFrame formatas.")


def build_lstm_model(num_muns: int, seq_len: int = 30,
                     emb_dim: int = 8, lstm_units: int = 64,
                     l2_reg: float = 1e-6, dropout_rate: float = 0.2) -> tf.keras.Model:
    """
    Sukuria ir kompiliuoja LSTM su dviem įėjimais: seka ir mun_code.
    """
    seq_input = layers.Input(shape=(seq_len,1), name='seq_input')
    mun_input = layers.Input(shape=(), dtype='int32', name='mun_input')
    emb = layers.Embedding(input_dim=num_muns, output_dim=emb_dim)(mun_input)
    emb_flat = layers.Flatten()(emb)
    x = layers.LSTM(lstm_units, kernel_regularizer=regularizers.l2(l2_reg))(seq_input)
    x = layers.Concatenate()([x, emb_flat])
    x = layers.Dense(lstm_units, activation='relu', kernel_regularizer=regularizers.l2(l2_reg))(x)
    x = layers.Dropout(dropout_rate)(x)
    out = layers.Dense(1)(x)
    model = models.Model([seq_input, mun_input], out)
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-4),
                  loss='mse', metrics=[tf.keras.metrics.RootMeanSquaredError()])
    return model


def main():
    script_dir = os.path.abspath(os.path.dirname(__file__))
    data_path = os.path.normpath(os.path.join(script_dir, '..','data','processed','cleaned_events.csv'))
    models_dir = os.path.normpath(os.path.join(script_dir, '..','models'))
    os.makedirs(models_dir, exist_ok=True)

    # 1. Load & aggregate
    agg = load_and_aggregate(data_path)

    # 2. Prepare training sequences
    SEQ_LEN = 30
    X_seq, y_seq, mun_seq = prepare_sequence(agg, seq_len=SEQ_LEN)

    # 3. Train-test split by date
    cutoff = agg['date'].max() - pd.DateOffset(years=2)
    dates = np.concatenate([
        grp['date'].values[SEQ_LEN:]
        for _, grp in agg.groupby('mun_code')
    ])
    mask = dates < np.datetime64(cutoff)
    X_train, X_test = X_seq[mask], X_seq[~mask]
    y_train, y_test = y_seq[mask], y_seq[~mask]
    mun_train, mun_test = mun_seq[mask], mun_seq[~mask]

    # 4. Build model
    model = build_lstm_model(agg['mun_code'].nunique(), seq_len=SEQ_LEN)

    # 5. Callbacks
    callbacks = [
        EarlyStopping('val_root_mean_squared_error', patience=7, restore_best_weights=True),
        ReduceLROnPlateau('val_root_mean_squared_error', factor=0.5, patience=5),
        ModelCheckpoint(os.path.join(models_dir,'lstm_accident_model.keras'), save_best_only=True, monitor='val_root_mean_squared_error')
    ]

    # 6. Train
    model.fit([X_train, mun_train], y_train, validation_split=0.2,
              epochs=20, batch_size=32, callbacks=callbacks, verbose=2)

    # 7. Evaluate
    loss, rmse = model.evaluate([X_test, mun_test], y_test, verbose=0)
    print(f"Test RMSE: {rmse:.3f}")

    # 8. Save final model
    model.save(os.path.join(models_dir,'lstm_accident_model_final.keras'), include_optimizer=False)

if __name__=='__main__':
    main()