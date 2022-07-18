import pandas as pd
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
stop_words = set(stopwords.words('english'))
import re
from copy import copy
import os
import string
from A_DOI_finder import *
from datetime import *
import collections
from A_published_date import *

v = sys.version
token = 'IXMbiJNANWTlkMSb4ea7Y5qJIGCFqki6IJPZjc1m' # API Key

def keys_exists(element, *keys):
    '''
    Check if *keys (nested) exists in `element` (dict).
    '''
    if not isinstance(element, dict):
        raise AttributeError('keys_exists() expects dict as first argument.')
    if len(keys) == 0:
        raise AttributeError('keys_exists() expects at least two arguments, one given.')

    _element = element
    for key in keys:
        try:
            _element = _element[key]
        except KeyError:
            return False
    return True

# =====================================================================================================================
def load_dataframes():
    entities_path = "./DATA/Worksheet/Entities_DataBank.xls"

    df_Satellites= pd.read_excel(entities_path, sheet_name='Satellites')
    SAT_dict = {}
    compteur_ligne = 0
    for compteur_ligne in range(len(df_Satellites)):
        SAT_dict[str(df_Satellites.iloc[compteur_ligne,0])] = []
        for compteur_colonne in range(len(df_Satellites.iloc[compteur_ligne])) :
            if str(df_Satellites.iloc[compteur_ligne,compteur_colonne]) != 'nan':
                SAT_dict[str(df_Satellites.iloc[compteur_ligne, 0])].append(str(df_Satellites.iloc[compteur_ligne,compteur_colonne]))

    df_Instruments = pd.read_excel(entities_path, sheet_name='Instruments')
    INST_dict = {}
    compteur_ligne = 0
    for compteur_ligne in range(len(df_Instruments)):
        INST_dict[str(df_Instruments.iloc[compteur_ligne, 0])] = []
        for compteur_colonne in range(1, len(df_Instruments.iloc[compteur_ligne])):
            if str(df_Instruments.iloc[compteur_ligne, compteur_colonne]) != 'nan':
                if re.search("^\{", df_Instruments.iloc[compteur_ligne, compteur_colonne]):
                    INST_dict[str(df_Instruments.iloc[compteur_ligne, 0])].append(eval(df_Instruments.iloc[compteur_ligne, compteur_colonne]))
                else:
                    INST_dict[str(df_Instruments.iloc[compteur_ligne, 0])].append(str(df_Instruments.iloc[compteur_ligne, compteur_colonne]))

    df_Regions_general = pd.read_excel(entities_path, sheet_name='Regions_General')
    REG_general_list = []
    for compteur_ligne in range(len(df_Regions_general)):
        REG_general_list.append(str(df_Regions_general.iloc[compteur_ligne, 0]))

    df_Regions= pd.read_excel(entities_path, sheet_name='Regions_Tree')
    REG_dict = {}
    for compteur_ligne in range(len(df_Regions)):
        REG_dict[str(df_Regions.iloc[compteur_ligne,0])] = {}
        for compteur_colonne in range(1,len(df_Regions.iloc[compteur_ligne])) :
            if str(df_Regions.iloc[compteur_ligne,compteur_colonne]) != 'nan':
                REG_dict[str(df_Regions.iloc[compteur_ligne,0])].update(eval(str(df_Regions.iloc[compteur_ligne,compteur_colonne])))

    df_AMDA_SPASE = pd.read_excel(entities_path, sheet_name='Satellites\'s Regions')
    AMDA_dict = {}
    for compteur_ligne in range(len(df_AMDA_SPASE)):
        for compteur_colonne in range(1, len(df_AMDA_SPASE.iloc[compteur_ligne])):
            AMDA_dict[str(df_AMDA_SPASE.iloc[compteur_ligne, 0])] = eval(df_AMDA_SPASE.iloc[compteur_ligne, compteur_colonne])

    df_distance_metrics= pd.read_csv("../Classeurs/distance_metrics.csv")
    num_colonne = len(df_distance_metrics)

    df_operating_spans = pd.read_excel(entities_path, sheet_name='span')
    SPAN_dict = {}
    for compteur_ligne in range(len(df_operating_spans)):
        SPAN_dict[str(df_operating_spans.iloc[compteur_ligne, 0])] = []
        for compteur_colonne in range(1, len(df_operating_spans.iloc[compteur_ligne])):
            SPAN_dict[str(df_operating_spans.iloc[compteur_ligne, 0])].append(str(df_operating_spans.iloc[compteur_ligne, compteur_colonne]))

    # Pour toutes operating spans, si pas de date début ou fin remplace par défaut par T-Spoutnik le début, ou aujourd'hui pour la fin.
    for elements, val in SPAN_dict.items():
        if val[0] == 'nan':
            val[0] = '1957-10-04'  # T-Spoutnik
        if val[1] == 'nan':
            val[1] = str(datetime.date(datetime.now()))

    return SAT_dict,INST_dict,REG_general_list,REG_dict,AMDA_dict,df_distance_metrics,SPAN_dict,num_colonne

def operating_span_checker(sat,durations,SAT_dict,SPAN_dict,published_date):
    # Vérifie qu'un intervalle liée à un sattelite est bien comrpis dans l'operating span du dit sattelite.
    try:
        # récupère le nom principale (le premier) d'un sattelite.
        sat_name = sat['text']
        for syns in SAT_dict.values():
            if sat_name in syns:
                sat_name = syns[0]

        # découpage YYYY,MM,DD dans les spans
        SPAN_start_year,SPAN_start_month,SPAN_start_day = int(re.search("(([0-9]{4})-([0-9]{2})-([0-9]{2}))",SPAN_dict[sat_name][0]).group(2)),\
                                                          int(re.search("(([0-9]{4})-([0-9]{2})-([0-9]{2}))",SPAN_dict[sat_name][0]).group(3)),\
                                                          int(re.search("(([0-9]{4})-([0-9]{2})-([0-9]{2}))",SPAN_dict[sat_name][0]).group(4))
        if published_date != None:
            SPAN_stop_year,SPAN_stop_month,SPAN_stop_day = int(re.search("(([0-9]{4})-([0-9]{2})-([0-9]{2}))",published_date).group(2)),\
                                                       int(re.search("(([0-9]{4})-([0-9]{2})-([0-9]{2}))",published_date).group(3)),\
                                                       int(re.search("(([0-9]{4})-([0-9]{2})-([0-9]{2}))",published_date).group(4))
        else:
            SPAN_stop_year,SPAN_stop_month,SPAN_stop_day = int(re.search("(([0-9]{4})-([0-9]{2})-([0-9]{2}))",SPAN_dict[sat_name][1]).group(2)),\
                                                           int(re.search("(([0-9]{4})-([0-9]{2})-([0-9]{2}))",SPAN_dict[sat_name][1]).group(3)),\
                                                           int(re.search("(([0-9]{4})-([0-9]{2})-([0-9]{2}))",SPAN_dict[sat_name][1]).group(4))

        # découpage YYYY,MM,DD dans les durations
        begin_year,begin_month,begin_day = int(re.search("(([0-9]{4})-([0-9]{2})-([0-9]{2}))",durations['value']['begin']).group(2)),\
                                           int(re.search("(([0-9]{4})-([0-9]{2})-([0-9]{2}))",durations['value']['begin']).group(3)),\
                                           int(re.search("(([0-9]{4})-([0-9]{2})-([0-9]{2}))",durations['value']['begin']).group(4))
        end_year,end_month,end_day = int(re.search("(([0-9]{4})-([0-9]{2})-([0-9]{2}))",durations['value']['end']).group(2)),\
                                     int(re.search("(([0-9]{4})-([0-9]{2})-([0-9]{2}))",durations['value']['end']).group(3)),\
                                     int(re.search("(([0-9]{4})-([0-9]{2})-([0-9]{2}))",durations['value']['end']).group(4))

        # vérification: duration incluse dans operating span
        if (datetime(begin_year, begin_month, begin_day) >= datetime(SPAN_start_year, SPAN_start_month, SPAN_start_day)) and (datetime(end_year, end_month, end_day) <= datetime(SPAN_stop_year, SPAN_stop_month, SPAN_stop_day)):
            return True
        else:
            return False
    except:
        return 1
# =================================================

def entities_finder(current_OCR_folder):

    def find_path(dict_obj, key, i=None):
        for k, v in dict_obj.items():
            # add key to path
            path.append(k)
            if isinstance(v, dict):
                # continue searching
                find_path(v, key, i)
            if isinstance(v, list):
                # search through list of dictionaries
                for i, item in enumerate(v):
                    # add the index of list that item dict is part of, to path
                    path.append(i)
                    if isinstance(item, dict):
                        # continue searching in item dict
                        find_path(item, key, i)
                    # if reached here, the last added index was incorrect, so removed
                    path.pop()
            if k == key:
                # add path to our result
                result.append(copy(path))
            # remove the key added in the first line
            if path != []:
                path.pop()

    SAT_dict, INST_dict, REG_general_list, REG_dict, AMDA_dict, df_distance_metrics, SPAN_dict, num_colonne = load_dataframes()

    files_path = os.path.join(current_OCR_folder, "out_filtered_text.txt")  # chargement du fichier texte (contenue de l'article)

    file = open(files_path, "r")
    content_upper = file.read()
    file.close()

    file_name = current_OCR_folder + "/" + os.path.basename(current_OCR_folder) + ".tei.xml"
    DOI = find_DOI(file_name) # récupération du DOI de l'article en cour de traitement.

    files_path_json = os.path.join(current_OCR_folder, "res_sutime_2.json")  # chargement des résultats SUTime transformés
    JSON_file = open(files_path_json, "r")
    JSON_content = JSON_file.read()
    JSON_dict = eval(JSON_content)
    JSON_file.close()

    # SAT recognition
    sat_dict_list = []
    for SATs, Synonymes in SAT_dict.items():
        for syns in Synonymes:
            test = re.finditer("( |\n)" + syns + "(\.|,| )", content_upper)
            sat_dict_list += [{'end': matches.end(), 'start': matches.start(), 'text': re.sub("(\n|\.|,)", "", matches.group()).strip(), 'type':'sat'} for matches in test]

    # INST recognition
    inst_dict_list = []
    for INSTs, Instrument in INST_dict.items():
        for inst in Instrument:
            if isinstance(inst, str):
                test = re.finditer("" + inst + "(\.|,| |;)", content_upper)
                inst_dict_list += [{'end': matches.end(), 'start': matches.start(), 'text': matches.group().strip().translate(str.maketrans('', '', string.punctuation))} for matches in test]
            elif isinstance(inst, dict):
                for key, value in inst.items():
                    test = re.finditer("" + key + "(\.|,| |;)", content_upper)
                    inst_dict_list += [{'end': matches.end(), 'start': matches.start(), 'text': matches.group().strip().translate(str.maketrans('', '', string.punctuation))} for matches in test]
                    if isinstance(value, str):
                        test_2 = re.finditer("" + value + "(\.|,| |;)", content_upper)
                        for matches in test_2:
                            inst_dict_list += [{'end': matches.end(), 'start': matches.start(), 'text': key}]
                    elif isinstance(value, list):
                        for syns in value:
                            test_2 = re.finditer("" + syns + "(\.|,| |;)", content_upper)
                            for matches in test_2:
                                inst_dict_list += [{'end': matches.end(), 'start': matches.start(), 'text': key}]

    # remove matches include in spans of others matches
    temp = []
    for sat_1 in sat_dict_list:
        for inst_2 in inst_dict_list:
            if sat_1 != {}:
                if (inst_2['start'] - 1 <= sat_1['start']) and (inst_2['end'] + 1 >= sat_1['end']):  # is include
                    sat_1.clear()
                    # break
        temp.append(sat_1)
    sat_dict_list = [i for i in temp if i != {}]

    inst_list = list(set([inst['text'] for inst in inst_dict_list]))

    final_links = []
    for sats in sat_dict_list:
        final_links.append([sats, {'end': (len(content_upper) / 2) + 1, 'start': (len(content_upper) / 2), 'text': inst_list}])

    # Vérifie pour chaque sattelites trouvés les instruments qui leur appartiennent respectivement.
    for elements in final_links:
        temp = []
        try:
            for inst in elements[1]['text']:
                INST_temp = []
                for elems in INST_dict[elements[0]['text']]:
                    if isinstance(elems, str):
                        INST_temp.append(elems)
                    elif isinstance(elems, dict):
                        for key in elems.keys():
                            INST_temp.append(key)
                if inst in INST_temp:
                    temp.append(inst)
        except:
            elements[1]['text'] = []
        elements[1]['text'] = temp

    # Changeles nom de tous les sattelites trouvés par leur nom principal (nom AMDA quand existant OU premier nom dans SAT_dict)
    for elements in final_links:
        for key, val in SAT_dict.items():
            if elements[0]['text'] in val:
                in_amda = False
                for elems in val:
                    if elems in AMDA_dict.keys():  # nom amda
                        elements[0]['text'] = elems
                        in_amda = True
                if in_amda == False:
                    for key, val in SAT_dict.items(): # premier nom dans SAT_dict
                        if elements[0]['text'] in val:
                            elements[0]['text'] = val[0]

    # comptage occurance des satellites et intégrations
    list_occur = dict(collections.Counter([dicts[0]['text'] for dicts in final_links]))
    for elems in final_links:
        elems[0]['SO'] = list_occur[elems[0]['text']]

    temp = [elem[0] for elem in final_links]
    temp += JSON_dict
    temp = sorted(temp, key=lambda d: d['start'])

    # Association de la duration la plus proche d'un sattelite. Si elle n'est pas comprise dans l'operating span du sattelite, recherche la Nième duration le plus proche.
    published_date = published_date_finder(token, v, DOI)
    dicts_index = 0
    for dicts in temp:
        dist_list = []

        compteur_rang_aller = 0
        compteur_rang_retour = 0

        if dicts['type'] == 'sat':
            sens_aller = dicts_index
            sens_retour = dicts_index

            # sens -->
            while sens_aller < len(temp):
                if (temp[sens_aller]['type'] != 'sat'):
                    compteur_rang_aller += 1
                    if operating_span_checker(dicts, temp[sens_aller], SAT_dict, SPAN_dict, published_date) == True:
                        dicts['R'] = compteur_rang_aller
                        dist_list.append(temp[sens_aller])
                        sens_aller = len(temp)
                sens_aller += 1

            # sens <--
            while sens_retour >= 0:
                if (temp[sens_retour]['type'] != 'sat'):
                    compteur_rang_retour += 1
                    if operating_span_checker(dicts, temp[sens_retour], SAT_dict, SPAN_dict, published_date) == True:
                        dicts['R'] = compteur_rang_retour
                        dist_list.append(temp[sens_retour])
                        sens_retour = -1
                sens_retour -= 1

            # vérification du plus proche entre aller et retour:
            if len(dist_list) == 2:
                if (abs(dicts['start'] - dist_list[0]['start'])) < (abs(dicts['start'] - dist_list[1]['start'])):
                    min_dist = abs(dicts['start'] - dist_list[0]['start'])
                    compteur = 0
                    for elems in final_links:
                        if elems[0] == dicts:
                            final_links[compteur].append(dist_list[0])
                            final_links[compteur][0]['D'] = min_dist
                        compteur += 1
                else:
                    min_dist = abs(dicts['start'] - dist_list[1]['start'])
                    compteur = 0
                    for elems in final_links:
                        if elems[0] == dicts:
                            final_links[compteur].append(dist_list[1])
                            final_links[compteur][0]['D'] = min_dist
                        compteur += 1
            elif len(dist_list) == 1:
                min_dist = abs(dicts['start'] - dist_list[0]['start'])
                compteur = 0
                for elems in final_links:
                    if elems[0] == dicts:
                        final_links[compteur].append(dist_list[0])
                        final_links[compteur][0]['D'] = min_dist
                    compteur += 1
        else:
            continue
        dicts_index += 1

    TSO = {'occur_sat': len(sat_dict_list), 'nb_durations': len(JSON_dict)}
    for elements in final_links:
        if ('D' not in elements[0]) and ('R' in elements[0]):
            elements[0]['D'] = 1
        elif ('D' in elements[0]) and ('R' not in elements[0]):
            elements[0]['R'] = 1
        elif ('D' not in elements[0]) and ('R' not in elements[0]):
            elements[0]['D'] = 1
            elements[0]['R'] = 1

        elements[0]['conf'] = (elements[0]['D'] * elements[0]['R']) / (elements[0]['SO'] / TSO['occur_sat']) # à normalizé par max de conf

    maxi = max([elements[0]['conf'] for elements in final_links])
    for elements in final_links:
        elements[0]['conf'] = elements[0]['conf'] / maxi # normalisation par l'indice de confiance maximum

    # REG recognition
    planete_list = ["earth", "jupiter", "mars", "mercury", "neptune", "saturn", "sun", "uranus", "venus", "pluto", "heliosphere", "asteroid", "comet", "interstellar"]
    regs_dict_list = []

    for regs in REG_general_list:
        test = re.finditer("( |\n)" + "(" + regs + "|" + regs.lower() + ")" + "(\.|,| )", content_upper)
        regs_dict_list += [{'end': matches.end(), 'start': matches.start(), 'text': matches.group().strip().translate(str.maketrans('', '', string.punctuation))} for matches in test]

    # Association du nom de région de niveau bas (exemple magnetosphere) au nom de niveau haut (nom de planète) le plus proche.
    dicts_index = 0
    founded_regions_list = []
    temp = []
    for dicts in regs_dict_list:
        if dicts['text'].lower() in planete_list:
            temp = []
            sens_aller = dicts_index + 1
            sens_retour = dicts_index - 1
            # sens -->
            while sens_aller < len(regs_dict_list):
                if regs_dict_list[sens_aller]['text'] not in planete_list:
                    temp.append(regs_dict_list[sens_aller])
                    temp.append(dicts)
                    founded_regions_list.append(temp)
                    temp = []
                sens_aller += 1
            # sens <--
            while sens_retour >= 0:
                if regs_dict_list[sens_retour]['text'] not in planete_list:
                    temp.append(dicts)
                    temp.append(regs_dict_list[sens_retour])
                    founded_regions_list.append(temp)
                    temp = []
                sens_retour -= 1
        dicts_index += 1

    # TEST
    compteur = 0
    for elements in founded_regions_list:
        if elements[0]['text'].lower() in planete_list and elements[1]['text'].lower() in planete_list:
            if elements[0]['text'].lower() != elements[1]['text'].lower(): # supprésion des couples planète/planète quand celle-ci sont différentes.
                founded_regions_list[compteur].clear()
        elif (elements[0]['text'].lower() not in planete_list) and (elements[1]['text'].lower() not in planete_list): # supprésion des couples bas niveau/bas niveau.
            founded_regions_list[compteur].clear()
        compteur += 1
    founded_regions_list = [elements for elements in founded_regions_list if elements != []]

    # Ré-organisation de la liste de dictionnaire:
    #   les planètes en indexe 0
    #   les bas niveau en indexe 1
    compteur = 0
    for list_of_dicts in founded_regions_list:
        if (list_of_dicts[0]['text'].lower() not in planete_list) and (list_of_dicts[1]['text'].lower() in planete_list):
            temp_0 = founded_regions_list[compteur][0]
            temp_1 = founded_regions_list[compteur][1]
            founded_regions_list[compteur][0] = temp_1
            founded_regions_list[compteur][1] = temp_0
        compteur += 1

    # Vérification et supprésion de les couples planètes/bas niveau impossible (exemple Mercury/Atmosphère)
    path = []
    compteur = 0
    for elements in founded_regions_list:
        result = []
        result.append(elements[0]['text'])
        find_path(REG_dict[str(elements[0]['text'][0].upper() + elements[0]['text'][1:])], elements[1]['text'][0].upper() + elements[1]['text'][1:])  # params = nom planete, nom bas niveau
        final_path = ""
        for i in result:
            if isinstance(i, str):
                final_path += i + "."
            elif isinstance(i, list):
                for j in i:
                    if isinstance(j, str):
                        final_path += j + "."
        final_path = re.sub("\.$", "", final_path)
        result = []

        if elements[0]['text'].lower() != elements[1]['text'].lower():
            if final_path == elements[0]['text']:
                elements[1] = elements[0]
        compteur += 1

    # supréssion des couples en doublons
    compteur = 0
    for i in founded_regions_list:
        compteur_2 = compteur
        for j in founded_regions_list[compteur + 1:]:
            if j == i:
                founded_regions_list[compteur_2].clear()
            compteur_2 += 1
        compteur += 1
    founded_regions_list = [elements for elements in founded_regions_list if elements != []]

    # cas sattelite cité dans l'article mais aucune région le concernant:
    #   association par défaut avec le premier élément de sa liste de région.
    if len(founded_regions_list) == 0:
        for elements in final_links:
            sat = elements[0]['text']
            if sat in AMDA_dict:
                regs = AMDA_dict[sat]
                for regions in regs:
                    subs = regions.split(".")
                    founded_regions_list.append([{'end': 2, 'start': 4, 'text': subs[0]}, {'end': 6, 'start': 8, 'text': subs[-1]}])
        compteur = 0
        for i in founded_regions_list:
            compteur_2 = compteur
            for j in founded_regions_list[compteur + 1:]:
                if j == i:
                    founded_regions_list[compteur_2].clear()
                compteur_2 += 1
            compteur += 1
        founded_regions_list = [elements for elements in founded_regions_list if elements != []]

    # SAT and REG linker
    # result and path should be outside of the scope of find_path to persist values during recursive calls to the function
    path = []

    temp = []
    compteur_sat = 0
    for elems in final_links:
        temp_reg = []
        temp_reg += founded_regions_list
        finish = False
        while finish == False:
            first_passe = True
            compteur = 0
            compteur_min = 0

            for regs in temp_reg:
                if first_passe == True:
                    dist_min = abs(elems[0]['start'] - regs[1]['start'])
                    compteur_min = compteur
                    first_passe = False
                else:
                    if abs(elems[0]['start'] - regs[1]['start']) < dist_min:
                        dist_min = abs(elems[0]['start'] - regs[1]['start'])
                        compteur_min = compteur
                compteur += 1

            # construire le path SPASE
            # recherche dans l'arborescence
            result = []
            result.append(temp_reg[compteur_min][0]['text'])
            find_path(REG_dict[temp_reg[compteur_min][0]['text'][0].upper() + temp_reg[compteur_min][0]['text'][1:]],
                      temp_reg[compteur_min][1]['text'][0].upper() + temp_reg[compteur_min][1]['text'][1:])  # params = nom planete, nom bas niveau
            final_path = ""
            for i in result:
                if isinstance(i, str):
                    final_path += i + "."
                elif isinstance(i, list):
                    for j in i:
                        if isinstance(j, str):
                            final_path += j + "."
            final_path = re.sub("\.$", "", final_path)
            result = []

            # vérification de l'existance de cette plus proche régions dans REG_dict
            if elems[0]['text'] in AMDA_dict:
                nearest_region = None
                if final_path in AMDA_dict[elems[0]['text']]:
                    finish = True
                    nearest_region = temp_reg[compteur_min]
                    if len(final_links[compteur_sat]) == 3 and len(nearest_region) != 0:
                        final_links[compteur_sat] = [final_links[compteur_sat][0], final_links[compteur_sat][1], nearest_region[0], nearest_region[1], final_links[compteur_sat][2]['value']]
                    elif len(nearest_region) != 0:
                        final_links[compteur_sat] = [final_links[compteur_sat][0], final_links[compteur_sat][1], nearest_region[0], nearest_region[1]]
                    break
                else:
                    del temp_reg[compteur_min]
                    if len(temp_reg) == 0:
                        finish = True
                        break
            else:
                nearest_region = None
                finish = True
                break

        # rien n'a était trouvé
        if len(temp_reg) == 0 or nearest_region == None:
            if elems[0]['text'] in AMDA_dict:
                temp = AMDA_dict[elems[0]['text']][0].split(".")
                nearest_region = [{'end': 10, 'start': 0, 'text': temp[0]}, {'end': 30, 'start': 20, 'text': temp[-1]}]
                if len(final_links[compteur_sat]) == 3 and len(nearest_region) != 0:
                    final_links[compteur_sat] = [final_links[compteur_sat][0], final_links[compteur_sat][1], nearest_region[0], nearest_region[1], final_links[compteur_sat][2]['value']]
                elif len(nearest_region) != 0:
                    final_links[compteur_sat] = [final_links[compteur_sat][0], final_links[compteur_sat][1], nearest_region[0], nearest_region[1]]
            else:
                first_passe = True
                compteur = 0
                temp_reg = []
                temp_reg += founded_regions_list
                for regs in temp_reg:
                    if first_passe == True:
                        dist_min = abs(elems[0]['start'] - regs[1]['start'])
                        compteur_min = compteur
                        first_passe = False
                    else:
                        if abs(elems[0]['start'] - regs[1]['start']) < dist_min:
                            dist_min = abs(elems[0]['start'] - regs[1]['start'])
                            compteur_min = compteur
                    compteur += 1
                nearest_region = temp_reg[compteur_min]
                if len(final_links[compteur_sat]) == 3 and len(nearest_region) != 0:
                    final_links[compteur_sat] = [final_links[compteur_sat][0], final_links[compteur_sat][1], nearest_region[0], nearest_region[1], final_links[compteur_sat][2]['value']]
                elif len(nearest_region) != 0:
                    final_links[compteur_sat] = [final_links[compteur_sat][0], final_links[compteur_sat][1], nearest_region[0], nearest_region[1]]

        compteur_sat += 1

    # Ré-écriture selon la mise en forme ci-dessous
    final_amda_dict = {"start_time": "", "stop_time": "", "DOI": "", "sat": "", "inst": "", "reg": "", "D": "", "R": "", "SO": ""}
    final_amda_list = []

    for elems in final_links:
        final_amda_dict["sat"] = elems[0]["text"]
        final_amda_dict["inst"] = ','.join(elems[1]["text"])
        final_amda_dict["D"] = elems[0]['D']
        final_amda_dict["R"] = elems[0]['R']
        final_amda_dict["SO"] = elems[0]['SO']
        final_amda_dict["conf"] = elems[0]['conf']
        if len(elems) >= 5:
            final_amda_dict["start_time"] = elems[4]["begin"]
            final_amda_dict["stop_time"] = elems[4]["end"]
        # recherche dans l'arborescence
        result = []

        result.append(elems[2]['text'])

        find_path(REG_dict[elems[2]['text'][0].upper() + elems[2]['text'][1:]],elems[3]['text'][0].upper() + elems[3]['text'][1:])  # params = nom planete, nom bas niveau

        final_path = ""
        for i in result:
            if isinstance(i, str):
                final_path += i + "."
            elif isinstance(i, list):
                for j in i:
                    if isinstance(j, str):
                        final_path += j + "."
        final_path = re.sub("\.$", "", final_path)
        result = []
        final_amda_dict["reg"] = final_path
        final_amda_list.append(final_amda_dict)
        final_amda_dict = {"start_time": "", "stop_time": "", "DOI": "", "sat": "", "inst": "", "reg": "", "D": "", "R": "", "SO": ""}

    # insertion DOI dans le champ prévu à cet effet.
    for elements in final_amda_list:
        elements['DOI'] = DOI

    final_amda_list = sorted(final_amda_list, key=lambda d: d['start_time'])

    distinct_sats = list(set([dicts['sat'] for dicts in final_amda_list]))

    for elems in final_amda_list:
        if elems['start_time'] == '' and elems['stop_time'] == '':
            elems.clear()

    final_amda_list = [i for i in final_amda_list if i != {}]

    temp = []
    temp_final = []
    for sats in distinct_sats:
        for dicts in final_amda_list:
            if dicts['sat'] == sats:
                temp.append(dicts)
        temp_final.append(temp)
        temp = []

    # write in file
    final_file = open(current_OCR_folder + "/" + "reg_recognition_res.txt", "w")
    for elems in final_amda_list:
        final_file.write(str(elems))
        final_file.write("\n")
    final_file.close()

    # TEST
    start_time = 'start_time'
    stop_time = 'stop_time'
    DOI_2 = 'DOI'
    sat = 'sat'
    inst = 'inst'
    reg = 'reg'
    print(f'{start_time:30}', f'{stop_time:30}', f'{DOI_2:30}', f'{sat:30}', f'{inst:50}'f'{reg:30}')
    for elements in final_amda_list:
        temp = [value for key, value in elements.items()]
        print(f'{temp[0]:30}',f'{temp[1]:30}',f'{temp[2]:30}',f'{temp[3]:30}',f'{temp[4]:50}'f'{temp[5]:30}')
        print("------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")
    print("\n")

    with open(current_OCR_folder + "/" + DOI.translate(str.maketrans('', '', string.punctuation))+"_bibheliotech_V"+"1.txt", "w") as f:
        # f.write("# Test catalog;" + "\n")
        f.write("# Name: "+DOI.translate(str.maketrans('', '', string.punctuation))+"_bibheliotech_V"+"1"+";" + "\n")
        f.write("# Creation Date: " + datetime.now().isoformat() + ";" + "\n")
        f.write("# Description: Catalogue of events resulting from the HelioNER code (Dablanc & Génot, " + "\"github link à insérer\"" + ") on the paper " + "https://doi.org/" + str(DOI) + "\"" + ". The two first columns are the start/stop times of the event. the third column is the DOI of the paper, the fourth column is the mission that observed the event with the list of instruments (1 or more) listed in the fifth column. The sixth column is the most probable region of space where the observation took place (SPASE ObservedRegions term);\n")
        f.write("# Parameter 1: id:column1; name:DOI; size:1; type:char;" + "\n")
        f.write("# Parameter 2: id:column2; name:SATS; size:1; type:char;" + "\n")
        f.write("# Parameter 3: id:column3; name:INSTS; size:1; type:char;" + "\n")
        f.write("# Parameter 4: id:column4; name:REGS; size:1; type:char;" + "\n")
        f.write("# Parameter 5: id:column5; name:D; size:1; type:int;" + "\n")
        f.write("# Parameter 6: id:column6; name:R; size:1; type:int;" + "\n")
        f.write("# Parameter 7: id:column7; name:SO; size:1; type:int;" + "\n")
        f.write("# Parameter 8: id:column8; name:occur_sat; size:1; type:int;" + "\n")
        f.write("# Parameter 9: id:column9; name:nb_durations; size:1; type:int;" + "\n")
        f.write("# Parameter 10: id:column10; name:conf; size:1; type:float;" + "\n")
        compteur = 0
        for elements in final_amda_list:
            f.write(elements['start_time'] + " "
                    + elements['stop_time'] + " "
                    + "https://doi.org/" + str(elements['DOI']) + " "
                    + "\"" + elements['sat'] + "\"" + " "
                    + "\"" + elements['inst'].strip() + "\"" + " "
                    + "\"" + elements['reg'] + "\"" + " "
                    +  str(elements['D'])  + " "
                    +  str(elements['R'])  + " "
                    +  str(elements['SO'])  + " "
                    +  str(TSO['occur_sat'])  + " "
                    +  str(TSO['nb_durations'])  + " "
                    +  str(elements['conf'])  + " "
                    +"\n")
            compteur += 1