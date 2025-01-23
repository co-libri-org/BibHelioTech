import sys


def analyze_errors(text):
    # On divise le texte en sections d'erreurs
    sections = text.split('exception raised while executing (web.bht_proxy.pipe_paper)')
    sections = sections[1:]  # On ignore la première partie avant la première erreur

    # Dictionnaire pour stocker les types d'erreurs et leurs occurrences
    error_types = {}

    for section in sections:
        # On cherche la ligne d'erreur principale
        lines = section.strip().split('\n')
        error_line = None

        # On cherche la ligne qui contient l'erreur spécifique
        for line in lines:
            if 'Error:' in line or 'Exception:' in line:
                error_line = line.strip()
                break

        if error_line:
            # On nettoie la ligne d'erreur pour avoir une clé cohérente
            # On garde la partie après "Error:" ou "Exception:"
            if 'Error:' in error_line:
                error_type = error_line.split('Error:')[-1].strip()
            elif 'Exception:' in error_line:
                error_type = error_line.split('Exception:')[-1].strip()
            else:
                error_type = error_line

            # On incrémente le compteur pour ce type d'erreur
            error_types[error_type] = error_types.get(error_type, 0) + 1

    return error_types


def generate_report(error_types):
    print("Rapport d'analyse des erreurs:")
    print("-" * 50)
    print(f"\nNombre total de types d'erreurs différents: {len(error_types)}")
    print("\nDétail des erreurs:")
    print("-" * 50)

    # Trier par nombre d'occurrences (du plus fréquent au moins fréquent)
    sorted_errors = sorted(error_types.items(), key=lambda x: x[1], reverse=True)

    for error_type, count in sorted_errors:
        print(f"\nType d'erreur: {error_type}")
        print(f"Nombre d'occurrences: {count}")
        print(f"Pourcentage: {(count / sum(error_types.values()) * 100):.2f}%")
        print("-" * 30)


def main():
    if len(sys.argv) < 2:
        print("Missing exceptions.txt file as argument")
        sys.exit()
    file_path = sys.argv[1]
    # Lire le fichier d'entrée
    with open(file_path, 'r') as file:
        content = file.read()

    # Analyser les erreurs
    error_types = analyze_errors(content)

    # Générer et afficher le rapport
    generate_report(error_types)


if __name__ == "__main__":
    main()