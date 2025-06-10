from sqlalchemy_schemadisplay import create_schema_graph
from web import db, create_app  # On récupère l'instance SQLAlchemy de ton projet

app = create_app()

with app.app_context():

    # Assurez-vous que l'engine est bien récupéré
    engine = db.engine  # Récupération explicite de l'engine

    # Générer le graphe
    graph = create_schema_graph(
        metadata=db.metadata,  # Utilise les métadonnées SQLAlchemy
        engine=engine,         # Fournit l'engine manquant
        show_datatypes=True,    # Afficher les types SQL (Integer, String, etc.)
        show_indexes=True,      # Afficher les index
        rankdir="LR",           # Orientation du graphe (de gauche à droite)
        concentrate=False       # Éviter de fusionner les relations
    )

    # Sauvegarde du schéma en image
    graph.write_pdf("schema.pdf")

print("Schéma généré : schema.pdf")
