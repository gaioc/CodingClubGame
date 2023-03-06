import pygame as pg

class AudioDict:
    def __init__(self, filename):
        """Read in filename and populate Dict."""
        self.dict = dict()
        with open(filename) as audioData:
            for line in audioData.read().split("\n"):
                name, file = line.split("|")
                self.dict[name] = pg.mixer.Sound(f"assets/audio/sfx/{file}")
    def play(self, name):
        self.dict[name].play()


def stopMusic():
    pg.mixer.music.stop()

def playMusic(musicFileName):
    """
    Start looping music until called again.
    """
    if musicFileName:
        pg.mixer.music.load(f"assets/audio/music/{musicFileName}")
        pg.mixer.music.play(-1)