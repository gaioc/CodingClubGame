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

class CurrentMusic:
    def __init__(self, name):
        """if name is -1 then automatically replace, else only replace if different"""
        self.name = name

def stopMusic():
    pg.mixer.music.stop()

def playMusic(musicFileName, world, replaceable):
    """
    Start looping music until called again.
    """
    if not(world.get_component(CurrentMusic)):
        world.create_entity(CurrentMusic(-1))
    current = world.get_component(CurrentMusic)[0][1]
    if current.name == -1 or current.name != musicFileName:
        stopMusic()
        if musicFileName:
            pg.mixer.music.load(f"assets/audio/music/{musicFileName}")
            pg.mixer.music.play(-1)
    if replaceable:
        current.name = -1
    else:
        current.name = musicFileName