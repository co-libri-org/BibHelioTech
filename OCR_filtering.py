import re

def filter(current_OCR_folder):
    in_file = open(current_OCR_folder+"/"+"out_text.txt", "r") # open the txt file resulting from OCR
    content = in_file.read()
    content = re.sub("\n{1,5}"," ", content) # remove all \n

    content = re.sub(r"UT ", r" UT ", content)  # replace "22:02UT" by "22:02 UT"
    content = re.sub(r" UT ", r"UTC", content)  # replace "22:02 UT" by "22:02 UTC"

    # HHmm to HH:mm
    content = re.sub(r"([0-9]{2})([0-9]{2})(\:[0-9]{2})", r"\1:\2\3", content)
    content = re.sub(r"([0-9]{2})([0-9]{2})((-|–|—)|(-|–|—) | (-|–|—)| (-|–|—) | to | and )([0-9]{2})([0-9]{2})", r"\1:\2 - \8:\9", content)
    content = re.sub(r"([0-9]{2})([0-9]{2}) (UTC)", r"\1:\2\3", content)

    content = re.sub(
        r"((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|(Nov|Dec)(?:ember)?)) ([0-9]{1,2})((?: )?)(,)((?: )?)([0-9]{4})",
        r"\1 \3 \7", content)  # replace "09:30-23:30" by "09:30 - 23:30"
    content = re.sub(r"([0-9]{2}\:[0-9]{2})(\-|\–|\—)([0-9]{2}\:[0-9]{2})", r"\1 \2 \3", content)  # replace "09:30-23:30" by "09:30 - 23:30"
    content = re.sub(r"([0-9]{2}\:[0-9]{2})(\-|\–|\—) ([0-9]{2}\:[0-9]{2})", r"\1 \2 \3", content)  # replace "09:30- 23:30" by "09:30 - 23:30"
    content = re.sub(r"([0-9]{2}\:[0-9]{2}) (\-|\–|\—)([0-9]{2}\:[0-9]{2})", r"\1 \2 \3", content)  # replace "09:30 -23:30" by "09:30 - 23:30"
    content = re.sub(r"([0-9]{2}\:[0-9]{2}\:[0-9]{2}\.[0-9]{1,3})", r"T\1", content)  # replace "10:28:42.950" by "T10:28:42.950"
    content = re.sub(
        r"([0-9]{2})(\/|\–|\-)([0-9]{2}) ((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|(Nov|Dec)(?:ember)?)) ([0-9]{4})",
        r" \1 \4 \6 - \3 \4 \6", content)  # replace "17/18 September 2000" by "17 September 2000 - 18 September 2000"
    content = re.sub(r"([0-9]{4}) ((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|(Nov|Dec)(?:ember)?)) ([0-9]{1,2})",
                     r" \4 \2 \1 ", content)  # replace "2018 Oct 9" by "9 Oct 2018"
    content = re.sub(
        r"([0-9]{1,2}) ((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|(Nov|Dec)(?:ember)?)) ([0-9]{4}) (([0-9]{2}\:){1,2}[0-9]{2}) ([0-9]{1,2}) ((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|(Nov|Dec)(?:ember)?)) ([0-9]{4}) (([0-9]{2}\:){1,2}[0-9]{2})",
        r" \1 \2 \4 at \5 to \7 \8 \10 at \11 ", content)  # replace "2018 Oct 9 12:00 2018 Oct 11 00:00" by "9 Oct 2018 at 12:00 to 11 Oct 2018 at 00:00 "
    content = re.sub(r"UTC", r"", content)  # replace "22:02 UTC" by "22:02"

    content = re.sub(r'References', 'References\n', content)
    content = re.sub(r'REFERENCES', 'REFERENCES\n', content)

    content = re.sub(r'References\n[\s\S]+', '', content)
    content = re.sub(r'REFERENCES\n[\s\S]+', '', content)
    # content = re.sub('Received.*', '', content)
    # content = re.sub('Accepted.*', '', content)
    # content = re.sub('Published.*', '', content)
    # content = re.sub('Suggested.*', '', content)

    content = content.split('. ')

    open(current_OCR_folder+"/"+"out_filtered_text.txt", 'w').close() # erase previous file
    out_file = open(current_OCR_folder+"/"+"out_filtered_text.txt", "a+")
    for lines in content:
        lines = re.sub("((THE ASTROPHYSICAL JOURNAL(?: LETTER)?)(.*)(([0-9]{1,2}) ((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|(Nov|Dec)(?:ember)?)) ([0-9]{4})))","",lines)
        lines = re.sub(" Copyright ([0-9]{4})","",lines)
        out_file.write(lines)
        out_file.write(".\n")

    in_file.close()
    out_file.close()

    out_file = open(current_OCR_folder + "/" + "out_filtered_text.txt", "r")
    content = out_file.read()
    out_file.close()



    # content = content[int(len(content) * (10 / 100)):int(len(content) * (96 / 100))]
    #
    # out_file = open(current_OCR_folder + "/" + "out_filtered_text.txt", "w")
    # out_file.write(content)
    # out_file.close()
