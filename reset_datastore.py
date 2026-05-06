import os
from google.cloud import datastore

# On s'assure d'utiliser le bon projet
os.environ["GOOGLE_CLOUD_PROJECT"] = "tp1-cloud2"

def clear_datastore():
    print("Initialisation de la suppression...")
    client = datastore.Client(project="tp1-cloud2")
    
    # Suppression des Posts
    print("Récupération des Posts...")
    query = client.query(kind='Post')
    query.keys_only()
    posts = list(query.fetch())
    
    if posts:
        print(f"Suppression de {len(posts)} Posts...")
        for i in range(0, len(posts), 500):
            batch = posts[i:i+500]
            client.delete_multi([p.key for p in batch])
        print("Posts supprimés.")
    else:
        print("Aucun Post à supprimer.")
        
    # Suppression des Users
    print("Récupération des Users...")
    query = client.query(kind='User')
    query.keys_only()
    users = list(query.fetch())
    
    if users:
        print(f"Suppression de {len(users)} Users...")
        for i in range(0, len(users), 500):
            batch = users[i:i+500]
            client.delete_multi([u.key for u in batch])
        print("Users supprimés.")
    else:
        print("Aucun User à supprimer.")
        
    print("Datastore réinitialisé avec succès.")

if __name__ == '__main__':
    clear_datastore()
