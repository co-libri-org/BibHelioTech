import sys


def extract_lines(file_path):
    # On lit toutes les lignes du fichier
    with open(file_path, 'r') as file:
        lines = file.readlines()

    results = []
    for i, line in enumerate(lines):
        # 1- On cherche la première chaîne
        if 'exception raised while executing (web.bht_proxy.pipe_paper)' in line:
            # À partir de cette position, on cherche la deuxième chaîne
            for j in range(i, len(lines)):
                if 'BHT PIPELINE STEP 0: ' in lines[j]:
                    # On récupère les 4 lignes précédentes
                    start_index = max(0, j - 4)  # Pour éviter un index négatif
                    extracted_lines = lines[start_index:j]
                    results.append(extracted_lines)
                    break  # On passe à la prochaine occurrence de la première chaîne

    return results


# Utilisation
def main():
    if len(sys.argv) < 2:
        print("Missing worker.log file as argument")
        sys.exit()
    file_path = sys.argv[1]
    extracted_sections = extract_lines(file_path)

    # Affichage des résultats
    for i, section in enumerate(extracted_sections, 1):
        print(f"\nSection {i}:")
        print("".join(section))


if __name__ == "__main__":
    main()