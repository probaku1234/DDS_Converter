import PySimpleGUI as sg
import os.path
from wand import image
from enum import Enum
import PIL.Image
import io
import base64
import gettext
import webbrowser
import logging
import sys


def make_full_file_path_with_dds(image_file_name):
    filename_with_dds = os.path.splitext(image_file_name)[0] + '.dds'
    if output_folder_path:
        return os.path.join(output_folder_path, filename_with_dds)
    else:
        return os.path.join(image_folder_path, filename_with_dds)


def convert_to_bytes(file_or_bytes, resize=None):
    """
    Will convert into bytes and optionally resize an image that is a file or a base64 bytes object.
    Turns into  PNG format in the process so that can be displayed by tkinter
    :param file_or_bytes: either a string filename or a bytes base64 image object
    :type file_or_bytes:  (Union[str, bytes])
    :param resize:  optional new size
    :type resize: (Tuple[int, int] or None)
    :return: (bytes) a byte-string object
    :rtype: (bytes)
    """
    if isinstance(file_or_bytes, str):
        img = PIL.Image.open(file_or_bytes)
    else:
        try:
            img = PIL.Image.open(io.BytesIO(base64.b64decode(file_or_bytes)))
        except Exception as e:
            data_bytes_io = io.BytesIO(file_or_bytes)
            img = PIL.Image.open(data_bytes_io)

    cur_width, cur_height = img.size
    if resize:
        new_width, new_height = resize
        scale = min(new_height/cur_height, new_width/cur_width)
        img = img.resize((int(cur_width*scale), int(cur_height*scale)), PIL.Image.ANTIALIAS)
    with io.BytesIO() as bio:
        img.save(bio, format="PNG")
        del img
        return bio.getvalue()


def convert_image_to_dds():
    i = 0
    for image_file_name in file_names:
        logging.debug('Converting ' + image_file_name)
        file_full_path = os.path.join(image_folder_path, image_file_name)
        output_full_path = make_full_file_path_with_dds(image_file_name)
        logging.debug('Converting ' + image_file_name + " :: file full path: " + file_full_path)
        logging.debug('Converting ' + image_file_name + " :: output full path: " + output_full_path)

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
            logging.error(e)
            sg.popup_error_with_traceback(f'An error happened', e)


def setup_log_dir():
    if not os.path.isdir(logging_path):
        os.makedirs(logging_path)


class EventKey(Enum):
    IMAGE_FOLDER_CHOSEN = '-IMAGE FOLDER-'
    OUTPUT_FOLDER_CHOSEN = '-OUTPUT FOLDER-'
    FILE_LIST = '-FILE LIST-'
    IMAGE_SHOW = '-IMAGE-'
    IMAGE_NAME_SHOW = '-TOUT-'
    Convert = 'convert'


output_folder_path = ''
image_folder_path = ''
logging_path = os.path.join(os.path.expanduser('~'), 'Documents', 'DDS Converter')
file_names = []

# set up logging
setup_log_dir()
logging.basicConfig(filename=os.path.join(logging_path, 'log.txt'),
                    level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s:%(message)s')


def main_window(my_window=None):
    menu_def = [_('&About'), ['Github']], [_('&Language'), ['&ko', 'en']],
    file_list_column = [
        [
            sg.Menu(menu_def, pad=(10, 10))
        ],
        [
            sg.Text(_("Image Folder")),
            sg.In(size=(25, 1), enable_events=True, key=EventKey.IMAGE_FOLDER_CHOSEN),
            sg.FolderBrowse(),
        ],
        [
            sg.Text(_("Output Folder")),
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
        [sg.Text(_("Choose an image from list on left:"))],
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

    new_window = sg.Window(_("Image Converter"), layout, icon='images/logo.ico')

    if my_window is not None:
        my_window.close()
    return new_window


try:
    localedir = 'locale'
    translate = gettext.translation('messages', localedir=localedir, languages=['ko'])
    _ = translate.gettext
except Exception as e:
    print(e)
    logging.error(e)
    sys.exit(-1)

window = main_window()
logging.info('Window initialized')

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
            and f.lower().endswith((".png", ".tga", ".jpg", "jpeg"))
        ]
        window[EventKey.FILE_LIST].update(fnames)
        image_folder_path = folder
        file_names = fnames
        print('image folder path: ' + image_folder_path)
        print('file names: ' + file_names.__str__())
        logging.debug('file names: ' + file_names.__str__())
        logging.debug('image folder path: ' + image_folder_path)
    # Output folder was chosen, store path
    elif event == EventKey.OUTPUT_FOLDER_CHOSEN:
        output_folder_path = values[EventKey.OUTPUT_FOLDER_CHOSEN]
        print('output folder path: ' + output_folder_path)
        logging.debug('output folder path: ' + output_folder_path)
    elif event == EventKey.Convert.value:
        if not image_folder_path:
            sg.popup(_('No Image Folder Selected!'))
        elif not len(file_names):
            sg.popup(_('No Image Files Found on Folder!'))
        else:
            logging.info('Converting started')
            convert_image_to_dds()
            sg.popup(_('Done!'))
            logging.info('Converting finished')
    elif event == 'ko':
        translate = gettext.translation('messages', localedir=localedir, languages=['ko'])
        _ = translate.gettext
        print(_("Language changed to KO"))
        window = main_window(window)
    elif event == 'en':
        translate = gettext.translation('messages', localedir=localedir, languages=['en'])
        _ = translate.gettext
        print(_("Language changed to EN"))
        window = main_window(window)
    elif event == 'Github':
        webbrowser.open('https://github.com/probaku1234/DDS_Converter')
    elif event == EventKey.FILE_LIST:  # A file was chosen from the listbox
        try:
            filename = os.path.join(
                values[EventKey.IMAGE_FOLDER_CHOSEN], values[EventKey.FILE_LIST][0]
            )
            window["-TOUT-"].update(filename)
            window[EventKey.IMAGE_SHOW].update(data=convert_to_bytes(filename))

        except Exception as e:
            logging.error(e)
            sg.popup_error_with_traceback(f'An error happened', e)

window.close()

