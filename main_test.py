from PyQt5.QtCore import QObject, pyqtSignal
from SearchResults import Local


class MainTest(QObject):
    def __init__(self):
        super(MainTest, self).__init__()
        test = Local()
        test.populate("C:\\Users\\Josh\\Downloads\\Tree-Fall-Palm-Tree-Heavy-Slow-Cracking-Fall_GEN-HD3-38085_1398682.mp3",
                      'l00000000')
        test.signals.meta_changed.connect(lambda x: print(x.meta_file()['title']))
        test.set_tag('title', 'jump')


main = MainTest()
