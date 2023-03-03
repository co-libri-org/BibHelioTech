import csv


def catfile_to_rows(cat_file):
    """From a catalog file
       -  read each line, rid of comments
       -  create a hp_event_dict
    @return hpevent_dict list
    """
    hpeventdict_list = []
    with open(cat_file, newline="") as csvfile:
        reader = csv.reader(
            filter(lambda r: r[0] != "#", csvfile), delimiter=" ", quotechar='"'
        )
        for row in reader:
            hpevent_dict = {
                "start_date": row[0],
                "stop_date": row[1],
                "doi": row[2],
                "mission": row[2],
                "instrument": row[2],
                "region": row[2],
            }

            hpeventdict_list.append(hpevent_dict)
    return hpeventdict_list
