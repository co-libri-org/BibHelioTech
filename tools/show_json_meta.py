import json


def show_json(file_path):
    print(f"Looking into {file_path}")
    def show_struct(_s):
        for k, v in _s.items():
            print(f'{k}: {v}', end=' ')
        print('\n')
    with open( file_path) as fp:
        json_list = json.load(fp)
    # get meta
    meta_struct = json_list.pop()
    show_struct(meta_struct)
    # show all meta
    for _i in json_list:
        print(type(_i))
        if type(_i) is list:
            for _s in _i:
                show_struct(_s)
        elif type(_i) is dict:
            show_struct(_i)

def show_json_meta(file_path):
    with open( file_path) as fp:
        json_list = json.load(fp)
    meta_struct=json_list.pop()
    print(meta_struct)

def main(paper_dir, json_type="entities", step_num=None):
    # get all json files for type
    import os
    import glob

    if step_num is not None:
        search_pattern = os.path.join( f'{paper_dir}/', f'raw{step_num}_{json_type}.json' )
    else:
        search_pattern = os.path.join( f'{paper_dir}/', f'raw*_{json_type}.json' )
    json_files = glob.glob(search_pattern, recursive=True)
    if step_num is None:
        json_files.sort()
        for f in json_files:
            show_json_meta(f)
    else:
        show_json(json_files[0])
    # for each file, read json, extract last struc, show it


if __name__ == "__main__":

    import sys
    if len(sys.argv) < 2:
        print("Give dir as arg")
        sys.exit()
    paper_dir = sys.argv[1]
    if len(sys.argv) == 2:
        main(paper_dir)
    if len(sys.argv) == 3:
        step = int(sys.argv[2])
        main(paper_dir, "entities", step)
