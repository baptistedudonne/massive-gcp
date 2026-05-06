from locust import HttpUser, task, between
import os
import random

# On récupère le nombre d'utilisateurs depuis l'environnement pour savoir parmi 
# combien de users on peut tirer au sort
NUM_USERS = int(os.environ.get('DATA_USERS', '1000'))
PREFIX = os.environ.get('DATA_PREFIX', 'user')

class TimelineUser(HttpUser):
    # Simule un utilisateur qui lit sa timeline (attend entre 1 et 3 sec entre 2 requêtes)
    wait_time = between(1, 3)

    @task
    def load_timeline(self):
        # On simule un utilisateur aléatoire qui charge sa propre timeline
        user_id = f"{PREFIX}{random.randint(1, NUM_USERS)}"
        
        # Le nom (name="/api/timeline") permet à Locust d'agréger les requêtes 
        # plutôt que de faire une ligne par utilisateur dans le rapport
        self.client.get(f"/api/timeline?user={user_id}", name="/api/timeline")
