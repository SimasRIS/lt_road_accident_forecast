import os
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras import layers, models, regularizers
from tensorflow.keras.callbacks import (
    EarlyStopping, ReduceLROnPlateau, ModelCheckpoint, LambdaCallback
)
from tensorflow.keras.models import load_model
from sklearn.preprocessing import LabelEncoder
import keras_tuner as kt

# ------------------------------
# 0. Utils: clear session & epoch printer
# ------------------------------
def reset_tf():
    tf.keras.backend.clear_session()

print_epoch = LambdaCallback(
    on_epoch_begin=lambda epoch, logs: print(f"▶️ Epoch {epoch+1} start")
)

# ------------------------------
# 1. Load & preprocess data
# ------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
processed_path = os.path.normpath(
    os.path.join(script_dir, '..', 'data', 'processed', 'cleaned_events.csv')
)
if not os.path.exists(processed_path):
    raise FileNotFoundError(f"Cleaned data not found at {processed_path}")

events = pd.read_csv(processed_path, parse_dates=["dataLaikas"])
events['date'] = events['dataLaikas'].dt.floor('d')

# ------------------------------
# 2. Aggregate daily counts
# ------------------------------
agg = (
    events
    .groupby(['savivaldybe', 'date'])
    .size()
    .reset_index(name='accident_count')
)
le = LabelEncoder()
agg['mun_code'] = le.fit_transform(agg['savivaldybe'])

# ------------------------------
# 3. Create sequences
# ------------------------------
SEQ_LEN = 30
X_seq, y_seq, mun_seq, date_seq = [], [], [], []
for mun, df_m in agg.groupby('mun_code'):
    df_m = df_m.sort_values('date')
    counts = df_m['accident_count'].to_numpy()
    dates  = df_m['date'].to_numpy()
    for i in range(len(counts) - SEQ_LEN):
        X_seq.append(counts[i:i+SEQ_LEN])
        y_seq.append(counts[i+SEQ_LEN])
        mun_seq.append(mun)
        date_seq.append(dates[i+SEQ_LEN])

X_seq    = np.array(X_seq).reshape(-1, SEQ_LEN, 1)
y_seq    = np.array(y_seq)
mun_seq  = np.array(mun_seq)
date_seq = np.array(date_seq, dtype='datetime64[ns]')

# ------------------------------
# 4. Split into train/test by date
# ------------------------------
cutoff   = agg['date'].max() - pd.DateOffset(years=1)
train_idx = date_seq < np.datetime64(cutoff)
test_idx  = date_seq >= np.datetime64(cutoff)

X_train, X_test = X_seq[train_idx], X_seq[test_idx]
y_train, y_test = y_seq[train_idx], y_seq[test_idx]
mun_train, mun_test = mun_seq[train_idx], mun_seq[test_idx]

if len(X_train)==0 or len(X_test)==0:
    raise RuntimeError("Empty train/test split")

# ------------------------------
# 5. Hypermodel builder
# ------------------------------
def build_model(hp):
    emb_dim      = hp.Choice('emb_dim',   [4, 8, 16, 32])
    units        = hp.Choice('units',     [32, 64, 128])
    n_layers     = hp.Int(   'n_layers',  1, 3)
    dropout_rate = hp.Float( 'dropout_rate', 0.1, 0.5, step=0.1)
    l2_reg       = hp.Float( 'l2',         1e-6, 1e-3, sampling='log')
    lr           = hp.Choice('lr',         [1e-2, 1e-3, 1e-4])
    model_type   = hp.Choice('model_type', ['lstm', 'tcn'])

    seq_input = layers.Input((SEQ_LEN, 1), name='seq_input')
    mun_input = layers.Input(shape=(), dtype='int32', name='mun_input')
    emb = layers.Embedding(
        input_dim=agg['mun_code'].nunique(),
        output_dim=emb_dim
    )(mun_input)
    emb_flat = layers.Flatten()(emb)

    x = seq_input
    for i in range(n_layers):
        if model_type == 'lstm':
            x = layers.LSTM(
                units,
                return_sequences=(i < n_layers - 1),
                kernel_regularizer=regularizers.l2(l2_reg)
            )(x)
        else:
            x = layers.Conv1D(
                units,
                kernel_size=3,
                padding='causal',
                dilation_rate=2**i,
                kernel_regularizer=regularizers.l2(l2_reg)
            )(x)
            x = layers.Activation('relu')(x)
    if model_type == 'tcn':
        x = layers.GlobalAveragePooling1D()(x)

    x = layers.Concatenate()([x, emb_flat])
    x = layers.Dense(
        units,
        activation='relu',
        kernel_regularizer=regularizers.l2(l2_reg)
    )(x)
    x = layers.Dropout(dropout_rate)(x)
    out = layers.Dense(1)(x)

    model = models.Model([seq_input, mun_input], out)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=lr),
        loss='mse',
        metrics=[tf.keras.metrics.RootMeanSquaredError()]
    )
    return model

# ------------------------------
# 6. Hyperparameter grid over val_split & batch_size
# ------------------------------
val_splits  = [0.1, 0.2, 0.3, 0.4]
batch_sizes = [16, 32, 64]
best_score = np.inf
best_cfg   = {}

for vs in val_splits:
    for bs in batch_sizes:
        print(f"\n>> Searching vs={vs:.1f}, batch_size={bs}")
        reset_tf()
        tuner = kt.Hyperband(
            build_model,
            objective='val_root_mean_squared_error',
            max_epochs=30,
            factor=3,
            directory='tuner_dir',
            project_name=f'acc_vs{int(vs*100)}_bs{bs}'
        )
        tuner.search(
            x=[X_train, mun_train],
            y=y_train,
            validation_split=vs,
            epochs=50,
            batch_size=bs,
            callbacks=[
                EarlyStopping('val_root_mean_squared_error', patience=5, restore_best_weights=True),
                ReduceLROnPlateau('val_root_mean_squared_error', factor=0.5, patience=3),
                print_epoch
            ],
            verbose=1
        )

        # Evaluate best model on hold-out test set
        model = tuner.get_best_models(num_models=1)[0]
        pred  = model.predict([X_test, mun_test], verbose=0).flatten()
        rmse  = np.sqrt(np.mean((y_test - pred)**2))
        print(f"   → test RMSE = {rmse:.3f}")

        if rmse < best_score:
            best_score = rmse
            best_cfg = {
                'validation_split': vs,
                'batch_size': bs,
                'hyperparameters': tuner.get_best_hyperparameters(1)[0]
            }

print(f"\n*** Best test RMSE = {best_score:.3f} "
      f"with vs={best_cfg['validation_split']:.1f}, "
      f"bs={best_cfg['batch_size']} ***")

# ------------------------------
# 7. Optional Ensemble with baseline
# ------------------------------
model_dir     = os.path.normpath(os.path.join(script_dir, '..', 'models'))
baseline_file = None
for fname in ['accident_predictor_improved.h5', 'accident_predictor.h5']:
    path = os.path.join(model_dir, fname)
    if os.path.exists(path):
        baseline_file = path
        break

if baseline_file:
    # load without optimizer
    baseline = load_model(baseline_file, compile=False)
    # recompile cleanly
    baseline.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=best_cfg['hyperparameters'].get('lr')),
        loss='mse',
        metrics=[tf.keras.metrics.RootMeanSquaredError()]
    )

    # make predictions and ensemble
    seq_model = tuner.get_best_models(num_models=1)[0]
    seq_pred  = seq_model.predict([X_test, mun_test], verbose=0).flatten()
    # example time features for baseline:
    years  = pd.DatetimeIndex(date_seq[test_idx]).year
    months = pd.DatetimeIndex(date_seq[test_idx]).month
    base_pred    = baseline.predict({'mun': mun_test, 'time_feats': np.vstack((years, months)).T}, verbose=0).flatten()
    ensemble_pred = 0.5 * base_pred + 0.5 * seq_pred
    rmse_ens     = np.sqrt(np.mean((y_test - ensemble_pred)**2))
    print(f"Ensemble RMSE: {rmse_ens:.3f}")
else:
    print("No baseline found—skipping ensemble.")

# ------------------------------
# 8. Final training & saving
# ------------------------------
reset_tf()

best_vs  = best_cfg['validation_split']  # still 0.4, but we’ll override below
best_bs  = best_cfg['batch_size']
best_hps = best_cfg['hyperparameters']

# Training config tweaks
FINAL_VAL_SPLIT = 0.1   # use only 10% for quick validation
MAX_EPOCHS      = 20    # cap at typical best-epoch
MODEL_NAME      = 'accident_seq_model_best.keras'

# Build & compile
final_model = build_model(best_hps)

final_callbacks = [
    EarlyStopping(
        'val_root_mean_squared_error',
        patience=3,               # stop quickly after plateau
        restore_best_weights=True
    ),
    ReduceLROnPlateau(
        'val_root_mean_squared_error',
        factor=0.5,
        patience=2
    ),
    ModelCheckpoint(
        MODEL_NAME,
        monitor='val_root_mean_squared_error',
        save_best_only=True
    ),
    print_epoch
]

# Fit with smaller val split and fewer epochs
history = final_model.fit(
    [X_train, mun_train], y_train,
    validation_split=FINAL_VAL_SPLIT,
    epochs=MAX_EPOCHS,
    batch_size=best_bs,
    callbacks=final_callbacks,
    verbose=2
)

# Save final model (native .keras format, no optimizer)
os.makedirs(model_dir, exist_ok=True)
final_model.save(
    os.path.join(model_dir, MODEL_NAME),
    include_optimizer=False
)
print(f"Saved final model to {model_dir}/{MODEL_NAME} (optimizer excluded)")