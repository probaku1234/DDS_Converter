import PySimpleGUI as sg
import os.path
from wand import image
from enum import Enum


def make_full_file_path_with_dds(image_file_name):
    filename_with_dds = os.path.splitext(image_file_name)[0] + '.dds'
    if output_folder_path:
        return os.path.join(output_folder_path, filename_with_dds)
    else:
        return os.path.join(image_folder_path, filename_with_dds)


def convert_image_to_dds():
    i = 0
    for image_file_name in file_names:
        file_full_path = os.path.join(image_folder_path, image_file_name)
        output_full_path = make_full_file_path_with_dds(image_file_name)
        print(output_full_path)

        try:
            with image.Image(filename=fr'${file_full_path}') as img:
                img.compression = 'dxt5'
                img.save(filename=output_full_path)
                i = i + 1
                sg.one_line_progress_meter('Converting Image Files',
                                           i, len(file_names),
                                           orientation='h',
                                           bar_color=('#F47264', '#FFFFFF'))
        except Exception as e:
            sg.popup_error_with_traceback(f'An error happened', e)


class EventKey(Enum):
    IMAGE_FOLDER_CHOSEN = '-IMAGE FOLDER-'
    OUTPUT_FOLDER_CHOSEN = '-OUTPUT FOLDER-'
    FILE_LIST = '-FILE LIST-'
    IMAGE_SHOW = '-IMAGE-'
    IMAGE_NAME_SHOW = '-TOUT-'
    Convert = 'convert'


output_folder_path = ''
image_folder_path = ''
file_names = []

file_list_column = [
    [
        sg.Text("Image Folder"),
        sg.In(size=(25, 1), enable_events=True, key=EventKey.IMAGE_FOLDER_CHOSEN),
        sg.FolderBrowse(),
    ],
    [
        sg.Text("Output Folder"),
        sg.In(size=(25, 1), enable_events=True, key=EventKey.OUTPUT_FOLDER_CHOSEN),
        sg.FolderBrowse(),
    ],
    [
        sg.Listbox(
            values=[], enable_events=True, size=(40, 20), key=EventKey.FILE_LIST
        )
    ],
    [
        sg.Button(button_text=EventKey.Convert.value)
    ]
]

# For now will only show the name of the file that was chosen
image_viewer_column = [
    [sg.Text("Choose an image from list on left:")],
    [sg.Text(size=(40, 1), key="-TOUT-")],
    [sg.Image(key=EventKey.IMAGE_SHOW)],
]

# ----- Full layout -----
layout = [
    [
        sg.Column(file_list_column),
        sg.VSeperator(),
        sg.Column(image_viewer_column),
    ]
]

window = sg.Window("Image Converter", layout, icon='images/logo.ico')

# Run the Event Loop
while True:
    event, values = window.read()
    if event == "Exit" or event == sg.WIN_CLOSED:
        break
    # Folder name was filled in, make a list of files in the folder
    if event == EventKey.IMAGE_FOLDER_CHOSEN:
        folder = values[EventKey.IMAGE_FOLDER_CHOSEN]
        try:
            # Get list of files in folder
            file_list = os.listdir(folder)
        except:
            file_list = []

        fnames = [
            f
            for f in file_list
            if os.path.isfile(os.path.join(folder, f))
            # TODO: add more extensions
            and f.lower().endswith((".png", ".gif"))
        ]
        window[EventKey.FILE_LIST].update(fnames)
        image_folder_path = folder
        file_names = fnames
        print('image folder path: ' + image_folder_path)
        print('file names: ' + file_names.__str__())
    # Output folder was chosen, store path
    elif event == EventKey.OUTPUT_FOLDER_CHOSEN:
        output_folder_path = values[EventKey.OUTPUT_FOLDER_CHOSEN]
        print('output folder path: ' + output_folder_path)
    elif event == EventKey.Convert.value:
        print('Convert!')
        if not image_folder_path:
            sg.popup('No Image Folder Selected!')
        elif not len(file_names):
            sg.popup('No Image Files Found on Folder!')
        else:
            convert_image_to_dds()
            sg.popup('Done!')

    elif event == EventKey.FILE_LIST:  # A file was chosen from the listbox
        try:
            filename = os.path.join(
                values[EventKey.IMAGE_FOLDER_CHOSEN], values[EventKey.FILE_LIST][0]
            )
            window["-TOUT-"].update(filename)
            window[EventKey.IMAGE_SHOW].update(filename=filename)

        except Exception as e:
            sg.popup_error_with_traceback(f'An error happened', e)

window.close()

