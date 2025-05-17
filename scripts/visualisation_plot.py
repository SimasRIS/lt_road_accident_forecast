
import pandas as pd
import plotly.express as px

# Funkcija, kuri sukuria animuotą grafiką
def create_accident_animation():
    # Įkeliame išvalytus duomenis
    events_df = pd.read_csv('../data/processed/cleaned_events.csv')

    # Grupuojame duomenis pagal metus ir suskaičiuojame avarijų skaičių
    yearly_accidents = events_df.groupby('metai').size().reset_index(name='accident_number')

    # Sukuriame cumulative duomenis animacijai
    frames = []
    for i in range(1, len(yearly_accidents) + 1):
        frame = yearly_accidents.iloc[:i].copy()
        frame['frame_year'] = yearly_accidents.iloc[i - 1]['metai']
        frames.append(frame)

    df_anim = pd.concat(frames)

    # Animacija su linijiniu diagramu
    fig = px.line(
        df_anim,
        x='metai',
        y='accident_number',
        animation_frame='frame_year',
        markers=True,
        title='🎬 Tiksliai animuotas avarijų skaičiaus augimas per metus',
        labels={'accident_number': 'Avarijų skaičius', 'metai': 'Metai'}
    )

    fig.update_layout(yaxis_range=[0, yearly_accidents['accident_number'].max() + 500])
    fig.show()

# Pagrindinis blokas, kuris iškviečia funkciją
if __name__ == '__main__':
    create_accident_animation()
