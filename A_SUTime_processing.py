import json
from sutime import SUTime
import re
from datetime import date
from datetime import datetime

def SUTime_treatement(current_OCR_folder,sutime):
    file = open(current_OCR_folder + "/" + 'out_filtered_text.txt', 'r')
    reading = file.read()

    test_case = reading

    test_list = sutime.parse(test_case) #Analyse du texte en entier par SUTime

    compteur = 0
    for dicts in test_list:
        try:
            # removal of useless values
            if re.search('PRESENT_REF', str(dicts['value'])):  # remove times of type "..._REF"
                dicts.clear()
            elif re.search('FUTURE_REF', str(dicts['value'])):  # remove times of type "..._REF"
                dicts.clear()
            elif re.search('PAST_REF', str(dicts['value'])):  # remove times of type "..._REF"
                dicts.clear()
            elif re.search('P.*',str(dicts['value'])):  # remove times of types like PXS.XS,PTXS,PTXM,PTXH,PXD,PXW,PXY
                dicts.clear()
            elif re.search('^([^0-9]*)$',str(dicts['text'])):  # remove times that do not contains digit (like 'today', 'dusk', 'the night', etc...)
                dicts.clear()
            elif re.search('-WE$', str(dicts['value'])):  # remove times of type XXXX-WX-WE (weeks/week-end)
                dicts.clear()
            elif re.search('-W', str(dicts['value'])):  # remove times of type XXXX-WX-WE (weeks/week-end)
                dicts.clear()
            elif re.search('.*Q.*', str(dicts['value'])):  # remove times of type QX (Quarters)
                dicts.clear()
            elif re.search('MO$', str(dicts['value'])):  # remove times of type MO (morning)
                dicts.clear()
            elif re.search('AF$', str(dicts['value'])):  # remove times of type AF (afternoon)
                dicts.clear()
            elif re.search('EV$', str(dicts['value'])):  # remove times of type EV (evening)
                dicts.clear()
            elif re.search('NI$', str(dicts['value'])):  # remove times of type NI (night)
                dicts.clear()
            elif re.search('-FA$', str(dicts['value'])):  # remove times of type FA (autumn)
                dicts.clear()
            elif re.search('-SU$', str(dicts['value'])):  # remove times of type SU (summer)
                dicts.clear()
            elif re.search('-SP$', str(dicts['value'])):  # remove times of type SP (spring)
                dicts.clear()
            elif re.search('-WI$', str(dicts['value'])):  # remove times of type WI (winter)
                dicts.clear()
            elif re.search('^[0-9]{4}$', str(dicts['value'])):  # remove years alone (value : "2004")
                dicts.clear()
            elif re.search('^\+.*', str(dicts['value'])):  # remove +XXXX alone
                dicts.clear()
            elif re.search(str(str(date.today()).replace("-","\-")), dicts['value']):  # remove date if it's today
                dicts['value'] = re.sub(str(str(date.today()).replace("-","\-")),"", dicts['value'])
                dicts['timex-value'] = re.sub(str(str(date.today()).replace("-","\-")), "", dicts['timex-value'])
                if dicts['value'] == "":
                    dicts.clear()
        except:
            continue
        compteur += 1

    test_list = [i for i in test_list if i != {}] # remove empty dictionaries

    res_file = open(current_OCR_folder + "/" + "res_sutime.json", "w")
    res_file.write(json.dumps(test_list, sort_keys=True, indent=4)) # write the result in a file

    file.close()
    res_file.close()

def nearest_date(JSON_list,compteur_dicts):
    compteur_avant = compteur_dicts -1
    compteur_apres = compteur_dicts +1
    avant = 0
    apres = 0
    # parcour des éléments contenue avant JSON_list[compteur_dicts] dans JSON_list
    while compteur_avant >= 0:
        if JSON_list[compteur_avant]['type'] == "DATE":
            if re.search("((^[0-9]{4})-[0-9]{2}-[0-9]{2}$)",JSON_list[compteur_avant]['value']):
                avant = JSON_list[compteur_avant]
                break
        elif JSON_list[compteur_avant]['type'] == "DURATION":
            if re.search("((^[0-9]{4})-[0-9]{2}-[0-9]{2}$)",JSON_list[compteur_avant]['value']['begin']) and re.search("((^[0-9]{4})-[0-9]{2}-[0-9]{2}$)",JSON_list[compteur_avant]['value']['end']):
                avant = JSON_list[compteur_avant]
                break
        compteur_avant -= 1

    # parcour des éléments contenue après JSON_list[compteur_dicts] dans JSON_list
    while compteur_apres < len(JSON_list):
        if JSON_list[compteur_apres]['type'] == "DATE":
            if re.search("((^[0-9]{4})-[0-9]{2}-[0-9]{2}$)",JSON_list[compteur_apres]['value']):
                apres = JSON_list[compteur_apres]
                break
        elif JSON_list[compteur_apres]['type'] == "DURATION":
            if re.search("((^[0-9]{4})-[0-9]{2}-[0-9]{2}$)",JSON_list[compteur_apres]['value']['begin']) and re.search("((^[0-9]{4})-[0-9]{2}-[0-9]{2}$)",JSON_list[compteur_apres]['value']['end']):
                avant = JSON_list[compteur_apres]
                break
        compteur_apres += 1

    if avant == 0: #cas: pas de DATE ou DURATION avant
        nearest = JSON_list[compteur_apres]
    elif apres == 0: #cas: pas de DATE ou DURATION après
        nearest = JSON_list[compteur_avant]
    elif abs(JSON_list[compteur_avant]['end'] - JSON_list[compteur_dicts]['start']) < abs(JSON_list[compteur_dicts]['end'] - JSON_list[compteur_apres]['start']): # plus proche entre avant et après: c'est avant
        nearest = JSON_list[compteur_avant]
    else: # plus proche entre avant et après: c'est après
        nearest = JSON_list[compteur_apres]
    return nearest

def nearest_year(JSON_list,compteur_dicts):
    compteur_avant = compteur_dicts -1
    compteur_apres = compteur_dicts +1
    avant = 0
    apres = 0
    # parcour des éléments contenue avant JSON_list[compteur_dicts] dans JSON_list
    while compteur_avant >= 0:
        if JSON_list[compteur_avant]['type'] == "DATE":
            matcher = re.match("((^[0-9]{4})-[0-9]{2}-[0-9]{2})",JSON_list[compteur_avant]['value'])
            if matcher != None:
                avant = JSON_list[compteur_avant]
                break
        elif JSON_list[compteur_avant]['type'] == "DURATION":
            # print(JSON_list[JSON_list[compteur_avant]])
            matcher_begin = re.match("((^[0-9]{4})-[0-9]{2}-[0-9]{2})",JSON_list[compteur_avant]['value']['begin'])
            matcher_end = re.match("((^[0-9]{4})-[0-9]{2}-[0-9]{2})",JSON_list[compteur_avant]['value']['end'])
            if matcher_begin != None or matcher_end != None:
                avant = JSON_list[compteur_avant]
                break
        elif JSON_list[compteur_avant]['type'] == "TIME":
            matcher = re.match("((^[0-9]{4})-[0-9]{2}-[0-9]{2})",JSON_list[compteur_avant]['value'])
            if matcher != None:
                avant = JSON_list[compteur_avant]
                break
        compteur_avant -= 1

    # parcour des éléments contenue après JSON_list[compteur_dicts] dans JSON_list
    while compteur_apres < len(JSON_list):
        if JSON_list[compteur_apres]['type'] == "DATE":
            matcher = re.match("((^[0-9]{4})-[0-9]{2}-[0-9]{2})",JSON_list[compteur_apres]['value'])
            if matcher != None:
                apres = JSON_list[compteur_apres]
                break
        elif JSON_list[compteur_apres]['type'] == "DURATION":
            matcher_begin = re.match("((^[0-9]{4})-[0-9]{2}-[0-9]{2})",JSON_list[compteur_apres]['value']['begin'])
            matcher_end = re.match("((^[0-9]{4})-[0-9]{2}-[0-9]{2})",JSON_list[compteur_apres]['value']['end'])
            if matcher_begin != None or matcher_end != None:
                apres = JSON_list[compteur_apres]
                break
        elif JSON_list[compteur_apres]['type'] == "TIME":
            matcher = re.match("((^[0-9]{4})-[0-9]{2}-[0-9]{2})",JSON_list[compteur_apres]['value'])
            if matcher != None:
                avant = JSON_list[compteur_apres]
                break
        compteur_apres += 1

    if avant == 0: #cas: pas de DATE ou DURATION avant
        if JSON_list[compteur_apres]['type'] == "DATE":
            nearest = re.match("((^[0-9]{4})-[0-9]{2}-[0-9]{2})",JSON_list[compteur_apres]['value']).group(2)
        elif JSON_list[compteur_apres]['type'] == "TIME":
            nearest = re.match("((^[0-9]{4})-[0-9]{2}-[0-9]{2})",JSON_list[compteur_apres]['value']).group(2)
        elif JSON_list[compteur_apres]['type'] == "DURATION":
            nearest = re.match("((^[0-9]{4})-[0-9]{2}-[0-9]{2})",JSON_list[compteur_apres]['value']['begin']).group(2)
    elif apres == 0: #cas: pas de DATE ou DURATION après
        if JSON_list[compteur_avant]['type'] == "DATE":
            nearest = re.match("((^[0-9]{4})-[0-9]{2}-[0-9]{2})",JSON_list[compteur_avant]['value']).group(2)
        elif JSON_list[compteur_avant]['type'] == "TIME":
            nearest = re.match("((^[0-9]{4})-[0-9]{2}-[0-9]{2})",JSON_list[compteur_avant]['value']).group(2)
        elif JSON_list[compteur_avant]['type'] == "DURATION":
            nearest = re.match("((^[0-9]{4})-[0-9]{2}-[0-9]{2})",JSON_list[compteur_avant]['value']['end']).group(2)
    elif abs(JSON_list[compteur_avant]['end'] - JSON_list[compteur_dicts]['start']) < abs(JSON_list[compteur_dicts]['end'] - JSON_list[compteur_apres]['start']): # plus proche entre avant et après: c'est avant
        if JSON_list[compteur_avant]['type'] == "DATE":
            nearest = re.match("((^[0-9]{4})-[0-9]{2}-[0-9]{2})",JSON_list[compteur_avant]['value']).group(2)
        elif JSON_list[compteur_avant]['type'] == "TIME":
            nearest = re.match("((^[0-9]{4})-[0-9]{2}-[0-9]{2})",JSON_list[compteur_avant]['value']).group(2)
        elif JSON_list[compteur_avant]['type'] == "DURATION":
            matcher_begin = re.match("((^[0-9]{4})-[0-9]{2}-[0-9]{2})",JSON_list[compteur_avant]['value']['begin'])
            if matcher_begin != None:
                nearest = re.match("((^[0-9]{4})-[0-9]{2}-[0-9]{2})",JSON_list[compteur_avant]['value']['begin']).group(2)
            matcher_end = re.match("((^[0-9]{4})-[0-9]{2}-[0-9]{2})",JSON_list[compteur_avant]['value']['end'])
            if matcher_end != None:
                nearest = re.match("((^[0-9]{4})-[0-9]{2}-[0-9]{2})",JSON_list[compteur_avant]['value']['end']).group(2)
    else: # plus proche entre avant et après: c'est après
        if JSON_list[compteur_apres]['type'] == "DATE":
            nearest = re.match("((^[0-9]{4})-[0-9]{2}-[0-9]{2})",JSON_list[compteur_apres]['value']).group(2)
        elif JSON_list[compteur_apres]['type'] == "TIME":
            nearest = re.match("((^[0-9]{4})-[0-9]{2}-[0-9]{2})",JSON_list[compteur_apres]['value']).group(2)
        elif JSON_list[compteur_apres]['type'] == "DURATION":
            matcher_begin = re.match("((^[0-9]{4})-[0-9]{2}-[0-9]{2})",JSON_list[compteur_apres]['value']['begin'])
            if matcher_begin != None:
                nearest = re.match("((^[0-9]{4})-[0-9]{2}-[0-9]{2})",JSON_list[compteur_apres]['value']['begin']).group(2)
            matcher_end = re.match("((^[0-9]{4})-[0-9]{2}-[0-9]{2})",JSON_list[compteur_apres]['value']['end'])
            if matcher_end != None:
                nearest = re.match("((^[0-9]{4})-[0-9]{2}-[0-9]{2})",JSON_list[compteur_apres]['value']['end']).group(2)
    return nearest

def SUTime_transform(current_OCR_folder):
    file = open(current_OCR_folder + "/" + 'res_sutime.json', 'r')
    reading = file.read()
    JSON_list = eval(reading)
    file.close()

    today = datetime.today().strftime('%Y-%m-%d')  # stockage dans la date d'aujourd'hui au format YYYY-MM-DD
    current_year = re.match("(((^[0-9]{4})|(XXXX))-[0-9]{2}-[0-9]{2}$)", today).group(2)  # stockage de l'année actuelle

    for dicts in JSON_list:
        if dicts['type'] == "DATE":
            dicts['value'] = re.sub(rf"{current_year}.*", "XXXX", dicts['value'])
        elif dicts['type'] == "TIME":
            dicts['value'] = re.sub(rf"{current_year}", "XXXX", dicts['value'])
        elif dicts['type'] == "DURATION":
            if 'begin' not in dicts['value'] or 'end' not in dicts['value']:
                dicts.clear()
            else:
                dicts['value']['begin'] = re.sub(rf"{current_year}", "XXXX", dicts['value']['begin'])
                dicts['value']['end'] = re.sub(rf"{current_year}", "XXXX", dicts['value']['end'])

    JSON_list = [i for i in JSON_list if i != {}]  # filtrage des dictionnaires vides

    for dicts in JSON_list:
        try:
            # Suppréssion dans les DURATIONS des "+0000" ajouté dans les temps, induit par la lecture de "UTC" par SUTime
            if dicts['type'] == "DURATION":
                dicts['value']['begin'] = re.sub("\+0000", "", dicts['value']['begin'])
                dicts['value']['end'] = re.sub("\+0000", "", dicts['value']['end'])
            else:
                dicts['value'] = re.sub("\+0000", "", dicts['value'])
        except:
            continue

    for dicts in JSON_list:
        try:
            # TIMES
            if dicts['type'] == "TIME":
                # recherche de temp ressemblant au minimum à THH (avec toutes les déclinaisons possibles de YYYY-MM-DDTHH:MM:SS.msmsmsms)
                test = re.match(
                    '((?:[0-9]{4})?)((?:(\-|\–|\—))?)((?:[0-9]{2})?)((?:(\-|\–|\—))?)((?:[0-9]{2})?)(T)([0-9]{2})((?:(\:))?)((?:[0-9]{2})?)((?:\:)?)((?:[0-9]{2})?)((?:\.)?)((?:[0-9]{1,4})?)',
                    dicts['value'])
                if test != None:

                    begin = ''
                    end = ''

                    group_counter_max = len(test.groups())
                    while test.group(group_counter_max) == '' or test.group(group_counter_max) == None:  # teste arrêt aux HH ou aux MM ou ...
                        group_counter_max -= 1

                    group_counter_min = group_counter_max
                    while test.group(group_counter_min) != '':  # teste début aux YYYY ou aux MM ou ...
                        if group_counter_min == 0:
                            break
                        group_counter_min -= 1
                    group_counter_min += 1

                    if group_counter_max == 16:  # fin aux ms (milisecondes)
                        if group_counter_min == 1:  # début aux années
                            begin = ''.join(list(test.group(1, 2, 4, 5, 7, 8, 9, 10, 12, 13, 14, 15))) + str("%03d" % (int(test.group(group_counter_max)) - 1))
                            end = ''.join(list(test.group(1, 2, 4, 5, 7, 8, 9, 10, 12, 13, 14, 15))) + str("%03d" % (int(test.group(group_counter_max)) + 1))
                        elif group_counter_min == 4:  # début aux mois
                            begin = ''.join(list(test.group(4, 5, 7, 8, 9, 10, 12, 13, 14, 15))) + str("%03d" % (int(test.group(group_counter_max)) - 1))
                            end = ''.join(list(test.group(4, 5, 7, 8, 9, 10, 12, 13, 14, 15))) + str("%03d" % (int(test.group(group_counter_max)) + 1))
                        elif group_counter_min == 8:  # début à T (temps sans date)
                            begin = ''.join(list(test.group(8, 9, 10, 12, 13, 14, 15))) + str("%03d" % (int(test.group(group_counter_max)) - 1))
                            end = ''.join(list(test.group(8, 9, 10, 12, 13, 14, 15))) + str("%03d" % (int(test.group(group_counter_max)) + 1))
                    elif group_counter_max == 14:  # fin aux seconds
                        if group_counter_min == 1:  # début aux années
                            begin = ''.join(list(test.group(1, 2, 4, 5, 7, 8, 9, 10, 12, 13, 14))) + str(".%03d" % (495))
                            end = ''.join(list(test.group(1, 2, 4, 5, 7, 8, 9, 10, 12, 13, 14))) + str(".%03d" % (505))
                        elif group_counter_min == 4:  # début aux mois
                            begin = ''.join(list(test.group(4, 5, 7, 8, 9, 10, 12, 13, 14))) + str(".%03d" % (495))
                            end = ''.join(list(test.group(4, 5, 7, 8, 9, 10, 12, 13, 14))) + str(".%03d" % (505))
                        elif group_counter_min == 8:  # début à T (temps sans date)
                            begin = ''.join(list(test.group(8, 9, 10, 12, 13, 14))) + str(".%03d" % (495))
                            end = ''.join(list(test.group(8, 9, 10, 12, 13, 14))) + str(".%03d" % (505))
                    elif group_counter_max == 12:  # fin aux minutes
                        if group_counter_min == 1:  # début aux années
                            begin = ''.join(list(test.group(1, 2, 4, 5, 7, 8, 9, 10, 12))) + str(":" + "%02d" % (0))
                            end = ''.join(list(test.group(1, 2, 4, 5, 7, 8, 9, 10, 12))) + str(":" + "%02d" % (59))
                        elif group_counter_min == 4:  # début aux mois
                            begin = ''.join(list(test.group(4, 5, 7, 8, 9, 10, 12))) + str(":" + "%02d" % (0))
                            end = ''.join(list(test.group(4, 5, 7, 8, 9, 10, 12))) + str(":" + "%02d" % (59))
                        elif group_counter_min == 8:  # début à T (temps sans date)
                            begin = ''.join(list(test.group(8, 9, 10, 12))) + str(":" + "%02d" % (0))
                            end = ''.join(list(test.group(8, 9, 10, 12))) + str(":" + "%02d" % (59))
                    elif group_counter_max == 9:  # fin aux heurs
                        if group_counter_min == 1:  # début aux années
                            begin = ''.join(list(test.group(1, 2, 4, 5, 7, 8, 9, 10, 12))) + str(":" + "%02d" % (0)) + str(":" + "%02d" % (0))
                            end = ''.join(list(test.group(1, 2, 4, 5, 7, 8, 9, 10, 12))) + str(":" + "%02d" % (59)) + str(":" + "%02d" % (59))
                        elif group_counter_min == 4:  # début aux mois
                            begin = ''.join(list(test.group(4, 5, 7, 8, 9, 10, 12))) + str(":" + "%02d" % (0)) + str(":" + "%02d" % (0))
                            end = ''.join(list(test.group(4, 5, 7, 8, 9, 10, 12))) + str(":" + "%02d" % (59))
                        elif group_counter_min == 8:  # début à T (temps sans date)
                            begin = ''.join(list(test.group(8, 9, 10, 12))) + str(":" + "%02d" % (0)) + str(":" + "%02d" % (0))
                            end = ''.join(list(test.group(8, 9, 10, 12))) + str(":" + "%02d" % (59)) + str(":" + "%02d" % (59))
                    dicts['type'] = "DURATION"  # TIME devient un DURATIONS
                    dicts['value'] = {'begin': begin, 'end': end}  # Ajout de la nouvelle valeur
        except:
            continue

    # résolution de tous les XXXX
    compteur_dicts = 0
    for dicts in JSON_list:
        if dicts['type'] == "DURATION":
            if 'begin' in dicts['value']:
                if re.search('XXXX', dicts['value']['begin']):
                    year = nearest_year(JSON_list, compteur_dicts)
                    JSON_list[compteur_dicts]['value']['begin'] = re.sub(r'XXXX', year, dicts['value']['begin'])
            if 'end' in dicts['value']:
                if re.search('XXXX', dicts['value']['end']):
                    year = nearest_year(JSON_list, compteur_dicts)
                    JSON_list[compteur_dicts]['value']['end'] = re.sub(r'XXXX', year, dicts['value']['end'])
        elif dicts['type'] == "DATE":
            if re.search('XXXX', dicts['value']):
                year = nearest_year(JSON_list, compteur_dicts)
                JSON_list[compteur_dicts]['value'] = re.sub('XXXX', year, dicts['value'])
        elif dicts['type'] == "TIME":
            if re.search('XXXX', dicts['value']):
                year = nearest_year(JSON_list, compteur_dicts)
                JSON_list[compteur_dicts]['value'] = re.sub('XXXX', year, dicts['value'])
        compteur_dicts += 1

    # correction date lorsque celle ci au format court (YYYY-MM (pas de DD))
    compteur_dicts = 0
    for dicts in JSON_list:
        if dicts['type'] == "DURATION":
            if 'begin' in dicts['value']:
                if re.search('^(([0-9]{4})(-)([0-9]{2}))$', dicts['value']['begin']):
                    dicts['value']['begin'] += '-01'
            if 'end' in dicts['value']:
                if re.search('^(([0-9]{4})(-)([0-9]{2}))$', dicts['value']['end']):
                    dicts['value']['end'] += '-28'
        elif dicts['type'] == "DATE":
            if re.search('^(([0-9]{4})(-)([0-9]{2}))$', dicts['value']):
                dicts['value'] += '-15'
        elif dicts['type'] == "TIME":
            if re.search('^(([0-9]{4})(-)([0-9]{2}))$', dicts['value']):
                dicts['value'] += '-15'
        compteur_dicts += 1

    compteur = 0
    for dicts in JSON_list:
        # ajout de la date la plus proche contenue dans un DATE ou DURATION lorsque l'on est face à une DURATION au format {begin: T<un temp>, end: T<un temp>} (aucune date)
        try:
            if dicts['type'] == "DURATION":
                if 'begin' in dicts['value'] and 'end' in dicts['value']:
                    if re.search("^T.*", dicts['value']['begin']) and re.search("^T.*", dicts['value']['end']):
                        nearest = nearest_date(JSON_list, compteur)
                        if nearest['type'] == "DATE":
                            temp = {'begin': nearest['value'] + dicts['value']['begin'], 'end': nearest['value'] + dicts['value']['end']}
                            dicts['value'] = temp
                        elif nearest['type'] == "DURATION":
                            temp = {'begin': nearest['value']['begin'] + dicts['value']['begin'], 'end': nearest['value']['end'] + dicts['value']['end']}
                            dicts['value'] = temp
                    elif re.search("^T.*", dicts['value']['begin']) and re.search("(([0-9]{4})(-)([0-9]{2})(-)([0-9]{2})).*", dicts['value']['end']):  # cas date dans l'un mais pas dans l'autre
                        temp = {'begin': re.match("(([0-9]{4})(-)([0-9]{2})(-)([0-9]{2})).*", dicts['value']['end']).group(1) + dicts['value']['begin'], 'end': dicts['value']['end']}
                        dicts['value'] = temp
                    elif re.search("^T.*", dicts['value']['end']) and re.search("(([0-9]{4})(-)([0-9]{2})(-)([0-9]{2})).*", dicts['value']['begin']):  # cas date dans l'un mais pas dans l'autre
                        temp = {'begin': dicts['value']['begin'], 'end': re.match("(([0-9]{4})(-)([0-9]{2})(-)([0-9]{2})).*", dicts['value']['begin']).group(1) + dicts['value']['end']}
                        dicts['value'] = temp

        except:
            continue
        compteur += 1

    # CLEAR EMP
    # A la fin du traitement, suppression de tous résultats SUTime qui n'est pas une DURATION
    for dicts in JSON_list:
        if dicts['type'] != "DURATION":
            dicts.clear()
        elif dicts['type'] == "DURATION":
            if re.search("[0-9]{2}-[0-9]{2}$", dicts['value']['begin']) and re.search("[0-9]{2}-[0-9]{2}$", dicts['value']['end']):
                dicts.clear()
    JSON_list = [i for i in JSON_list if i != {}]

    # harmoniser les formats, ramène tous à la miliseconde
    for dicts in JSON_list:
        begin = re.match(
            '((?:[0-9X]{4})?)((?:(\-|\–|\—))?)((?:[0-9]{2})?)((?:(\-|\–|\—))?)((?:[0-9]{2})?)(T)([0-9]{2})((?:(\:))?)((?:[0-9]{2})?)((?:\:)?)((?:[0-9]{2})?)((?:\.)?)((?:[0-9X]{1,4})?)',
            dicts['value']['begin'])
        end = re.match(
            '((?:[0-9X]{4})?)((?:(\-|\–|\—))?)((?:[0-9]{2})?)((?:(\-|\–|\—))?)((?:[0-9]{2})?)(T)([0-9]{2})((?:(\:))?)((?:[0-9]{2})?)((?:\:)?)((?:[0-9]{2})?)((?:\.)?)((?:[0-9X]{1,4})?)',
            dicts['value']['end'])

        try:
            if begin.group(14) == '':
                dicts['value']['begin'] += ':00.000'
            elif begin.group(12) == '':
                dicts['value']['begin'] += ':00:00.000'
            elif begin.group(16) == '':
                dicts['value']['begin'] += '.000'

            if end.group(14) == '':
                dicts['value']['end'] += ':00.000'
            elif end.group(12) == '':
                dicts['value']['end'] += ':00:00.000'
            elif end.group(16) == '':
                dicts['value']['end'] += '.000'
        except:
            continue

    for dicts in JSON_list:
        if not re.search('^([0-9]{4})(-)([0-9]{2})(-)([0-9]{2})(T)([0-9]{2})(:)([0-9]{2})(:)([0-9]{2})(.)([0-9]{3})$', dicts['value']['begin']) or not re.search(
                '^([0-9]{4})(-)([0-9]{2})(-)([0-9]{2})(T)([0-9]{2})(:)([0-9]{2})(:)([0-9]{2})(.)([0-9]{3})$', dicts['value']['end']):
            dicts.clear()
    JSON_list = [i for i in JSON_list if i != {}]

    # CLEAR EMPTY
    for dicts in JSON_list:
        if dicts['type'] != "DURATION":
            dicts.clear()
    JSON_list = [i for i in JSON_list if i != {}]

    file = open(current_OCR_folder + "/" + 'res_sutime_2.json', 'w') # enregistrement dans un fichier à part des résultats transformés. c'est CE fichier qui seras lu pour lié plus tard intervalles/sat/inst/etc.
    file.write(json.dumps(JSON_list, sort_keys=True, indent=4))
    file.close()
