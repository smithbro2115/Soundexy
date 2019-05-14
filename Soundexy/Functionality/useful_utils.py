from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QRunnable
import traceback
import sys
import os


def try_to_remove_file(path):
    try:
        os.remove(path)
        return True
    except FileNotFoundError:
        return False


def get_formatted_duration_from_milliseconds(milliseconds):
    duration = milliseconds / 1000
    minutes = duration // 60
    seconds = duration % 60
    return '%02d:%02d' % (minutes, seconds)


def get_yes_no_from_bool(value: bool) -> str:
    if value:
        return 'Yes'
    return 'No'


def get_file_type_from_path(path):
    return os.path.splitext(path)[1]


class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class Worker(QRunnable):

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        self.interrupt = False

        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            if not self.interrupt:
                self.signals.finished.emit()  # Done


def downsample_wav(src, dst, inrate=44100, outrate=16000, inchannels=2, outchannels=1):
    import wave
    import audioop

    if not os.path.exists(src):
        print('Source not found!')
        return False

    if not os.path.exists(os.path.dirname(dst)):
        os.makedirs(os.path.dirname(dst))

    try:
        s_read = wave.open(src, 'r')
        s_write = wave.open(dst, 'w')
    except:
        print('Failed to open files!')
        return False

    n_frames = s_read.getnframes()
    data = s_read.readframes(n_frames)

    try:
        converted = audioop.ratecv(data, 2, inchannels, inrate, outrate, None)
        if outchannels == 1:
            converted = audioop.tomono(converted[0], 2, 1, 0)
    except:
        print('Failed to downsample wav')
        return False

    try:
        s_write.setparams((outchannels, 2, outrate, 0, 'NONE', 'Uncompressed'))
        s_write.writeframes(converted)
    except:
        print('Failed to write wav')
        return False

    try:
        s_read.close()
        s_write.close()
    except:
        print('Failed to close wav files')
        return False

    return True


def clear_folder(folder):
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)


def make_folder_if_it_does_not_exist(src, folder):
    new_src = src.replace('\\', '/')
    directory = f"{new_src}/{folder}"
    try:
        os.mkdir(directory)
    except FileExistsError:
        pass
    return directory


def get_app_data_folder(folder):
    app_data_path = os.getenv('APPDATA')
    soundexy_path = make_folder_if_it_does_not_exist(app_data_path, 'Soundexy')
    return make_folder_if_it_does_not_exist(soundexy_path, folder)


def add_file_if_it_does_not_exist(path):
    open(path, 'a').close()


def check_if_file_exists(path):
    try:
        open(path, 'r')
        return True
    except FileNotFoundError:
        return False


def pickle_obj(path, obj):
    import pickle
    with open(f"{path}.pkl", 'wb') as f:
        try:
            pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)
        except TypeError as e:
            raise AttributeError(e)


def load_pickle_obj(path):
    import pickle
    try:
        with open(path, 'rb') as f:
            return pickle.load(f)
    except EOFError:
        return []


def get_all_file_paths_from_dir(dir):
    for root, dirs, files in os.walk(dir):
        return files
