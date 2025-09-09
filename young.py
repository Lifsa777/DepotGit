import pandas as pd
# Charger le DataFrame des utilisateurs nettoyé
users = pd.read_csv('users_clean.csv', sep=';')

def is_young(user_id, threshold=30):
    user_row = users[users['User-ID'] == user_id]
    if user_row.empty:
        return False  # ou lever une exception si l'utilisateur n'existe pas
    age = user_row.iloc[0]['Age']
    return age < threshold

# Exemple d'utilisation
user_id_example = 100  # Remplacer par l'ID réel
if is_young(user_id_example):
    print(f"L'utilisateur {user_id_example} est jeune.")
else:
    print(f"L'utilisateur {user_id_example} n'est pas considéré comme jeune.")