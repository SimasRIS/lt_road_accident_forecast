import pandas as pd
import matplotlib.pyplot as plt


df = pd.read_csv("C:/Users/Vartotojas/PycharmProjects/bendras/data/processed/cleaned_events_df.csv")


df_filtered = df[(df['metai'] >= 2017) & (df['metai'] <= 2023)]


monthly_counts = df_filtered.groupby(['menuo', 'metai']).size().unstack()


monthly_counts.plot(kind='bar', figsize=(14, 6), colormap='tab10')
plt.title('Įskaitinių eismo įvykių pasiskirstymas pagal mėnesius (2017–2023)')
plt.xlabel('Mėnuo')
plt.ylabel('Įvykių skaičius')
plt.xticks(ticks=range(12), labels=[str(m) for m in range(1, 13)], rotation=0)
plt.legend(title='Metai', loc='center left', bbox_to_anchor=(1.0, 0.5))
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()
