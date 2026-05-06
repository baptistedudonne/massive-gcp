#!/usr/bin/env python3
"""Script de peuplement (seed) pour Tiny Instagram.

Usage basique:
  python seed.py --users 5 --posts 40 --follows-min 1 --follows-max 3

Paramètres:
  --users        Nombre d'utilisateurs à créer (user1 .. userN)
  --posts        Nombre total de posts à répartir
  --follows-min  Nombre minimum de follows par utilisateur
  --follows-max  Nombre maximum de follows par utilisateur
  --prefix       Préfixe des noms d'utilisateurs (default: user)
  --dry-run      N'écrit rien, affiche seulement le plan

Le script est idempotent sur les utilisateurs (il ne recrée pas si existants) et ajoute simplement des posts supplémentaires.

ATTENTION: Ce script écrit directement dans Datastore du projet courant (gcloud config get-value project).
"""
from __future__ import annotations
import argparse
import random
from datetime import datetime, timedelta
from google.cloud import datastore


def parse_args():
    p = argparse.ArgumentParser(description="Seed Datastore for Tiny Instagram")
    p.add_argument('--users', type=int, default=5)
    p.add_argument('--posts', type=int, default=30)
    p.add_argument('--follows-min', type=int, default=1)
    p.add_argument('--follows-max', type=int, default=3)
    p.add_argument('--prefix', type=str, default='user')
    p.add_argument('--dry-run', action='store_true')
    return p.parse_args()


def ensure_users(client: datastore.Client, names: list[str], dry: bool):
    created = 0
    keys = [client.key('User', name) for name in names]
    
    existing_entities = []
    # get_multi accepte max 1000 clés par requête
    for i in range(0, len(keys), 1000):
        existing_entities.extend(client.get_multi(keys[i:i+1000]))
        
    existing_keys = {e.key for e in existing_entities}
    
    to_put = []
    for key in keys:
        if key not in existing_keys:
            entity = datastore.Entity(key)
            entity['follows'] = []
            to_put.append(entity)
            created += 1
            
    if not dry and to_put:
        # put_multi accepte max 500 entités par requête
        for i in range(0, len(to_put), 500):
            client.put_multi(to_put[i:i+500])
            
    return created


def assign_follows(client: datastore.Client, names: list[str], fmin: int, fmax: int, dry: bool):
    keys = [client.key('User', name) for name in names]
    entities = []
    for i in range(0, len(keys), 1000):
        entities.extend(client.get_multi(keys[i:i+1000]))
        
    to_put = []
    for entity in entities:
        name = entity.key.name
        others = [u for u in names if u != name]
        if not others:
            continue
        target_count = random.randint(min(fmin, len(others)), min(fmax, len(others)))
        selection = random.sample(others, target_count)
        
        existing = set(entity.get('follows', []))
        new_set = sorted(existing.union(selection))
        entity['follows'] = new_set
        to_put.append(entity)
        
    if not dry and to_put:
        for i in range(0, len(to_put), 500):
            client.put_multi(to_put[i:i+500])


def create_posts(client: datastore.Client, names: list[str], total_posts: int, dry: bool):
    if not names or total_posts <= 0:
        return 0
    created = 0
    base_time = datetime.utcnow()
    to_put = []
    
    for i in range(total_posts):
        author = random.choice(names)
        key = client.key('Post')
        post = datastore.Entity(key)
        post['author'] = author
        post['content'] = f"Seed post {i+1} by {author}"
        post['created'] = base_time - timedelta(seconds=i)
        to_put.append(post)
        created += 1
        
        if len(to_put) >= 500:
            if not dry:
                client.put_multi(to_put)
            to_put = []
            
    if to_put and not dry:
        client.put_multi(to_put)
        
    return created


def main():
    args = parse_args()
    client = datastore.Client()

    user_names = [f"{args.prefix}{i}" for i in range(1, args.users + 1)]

    print(f"[Seed] Utilisateurs ciblés: {user_names}")
    if args.dry_run:
        print("[Dry-Run] Aucune écriture ne sera effectuée.")

    # 1. Users
    new_users = ensure_users(client, user_names, args.dry_run)
    print(f"[Seed] Nouveaux utilisateurs créés: {new_users}")

    # 2. Follows
    assign_follows(client, user_names, args.follows_min, args.follows_max, args.dry_run)
    print("[Seed] Relations de suivi ajustées.")

    # 3. Posts
    created_posts = create_posts(client, user_names, args.posts, args.dry_run)
    print(f"[Seed] Posts créés: {created_posts}")

    print("[Seed] Terminé.")


if __name__ == '__main__':
    main()
