from mutagen.mp3 import EasyMP3
import pickle
import SearchResults


path = "C:\\Users\\Josh\\Downloads\\audiotools.2.16.tar\\audiotools.2.16\\audiotools-2.16\\test\\flac-disordered.flac"
# file = EasyMP3(path)

file = SearchResults.Local()
file.populate(path, 'loo1')
test_list = [file]

with open('obj\\local_index.pkl', 'wb') as f:
    pickle.dump(test_list, f)

with open('obj\\local_index.pkl', 'rb') as f:
    file = pickle.load(f)
    print(file[0])
