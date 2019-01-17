from mutagen.mp3 import EasyMP3
import pickle
import SearchResults


path = "C:\\Users\\Josh\\Downloads\\Humvee-M998,Pavement,50-MPH,Pass-Bys-x2-Med-Fast,Approach-Pothole,5954_966759.wav"
# file = EasyMP3(path)

file = SearchResults.Local()
file.populate(path, 'loo1')
test_list = [file]

with open('obj\\test_index.pkl', 'wb') as f:
    pickle.dump(test_list, f)

with open('obj\\test_index.pkl', 'rb') as f:
    file = pickle.load(f)
    print(file[0].meta_file.filename)
