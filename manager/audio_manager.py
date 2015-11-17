__author__ = 'SARA'
from flask import current_app as app
from model.audio import Audio
from model.database import db
import os
from random import randint

def insert_audio_to_db(audio_url, image_id, refetch):
    audio = Audio(audio_url, image_id, refetch)
    audio_add = audio.add(audio)
    if audio_add is not None:
        return audio_add.audio_id
    return False

def getFileFolder():
    # folder = os.path.join(app.config['TEMP_FOLDER'], str(os.getpid()))
    folder = os.path.join(app.config['TEMP_FOLDER'], str(randint(0,100)))
    return folder

def getAudioFilePath(filename):
    folder = getFileFolder()
    if not os._exists(folder):
        os.mkdir(folder)
    file_path = os.path.join(folder, filename)
    return file_path

def deleteAudioFile(file_path):
    # folder = getFileFolder()
    folder = os.path.dirname(os.path.abspath(file_path))
    if os.path.isfile(file_path):
        # delete file only
        os.remove(file_path)
        # delete folder
        os.rmdir(folder)
        return True
    return False

def update_audio_refetch(audio_id):
    audio_obj = Audio.query.get(audio_id)
    old_refetch = audio_obj.refetch
    audio_obj.refetch = old_refetch + 1
    return db.session.commit()

def get_audio_lowest_refetch(image_id, audio_id):
    # order by asc and first
    return db.session.query(Audio).filter_by(Audio.image_id==image_id, Audio.audio_id!=audio_id).order_by(Audio.refetch).one()

def get_audio_lowest_refetch_image_only(image_id):
    # order by asc and first
    return db.session.query(Audio).filter(Audio.image_id==image_id).order_by(Audio.refetch).one()