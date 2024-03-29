__author__ = 'SARA'
from flask import current_app as app
from model.audio import Audio
from model.database import db
import os, shutil
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

def saveAudioFile(file, filename):
    folder = getFileFolder()
    if not os._exists(folder):
        os.mkdir(folder)
    file_path = os.path.join(folder, filename)
    file.save(file_path)  # save the file
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
    # print "audio id:" + str(audio_id)
    audio_obj = db.session.query(Audio).filter(Audio.audio_id==audio_id).first()
    # print "audio obj: " + str(audio_obj)
    old_refetch = audio_obj.refetch
    audio_obj.refetch = old_refetch + 1
    # print "old:" + str(old_refetch)
    # print "new:" + str(audio_obj.refetch)
    return db.session.commit()

def get_audio_lowest_refetch(image_id, audio_id):
    # order by asc and first
    return (db.session.query(Audio).filter(Audio.image_id==image_id).filter(Audio.audio_id!=audio_id).order_by(Audio.refetch)).first()

def get_audio_lowest_refetch_image_only(image_id):
    # order by asc and first
    return db.session.query(Audio).filter(Audio.image_id==image_id).order_by(Audio.refetch).first()

def clear_audios_table():
    Audio.query.delete()
    db.session.commit()
    return True

def get_all_audios_record_db():
    return Audio.query.all()

def get_audio_cannot_find_refetch_audio():
    return Audio.query.filter(Audio.audio_id==1).first()

def delete_audio_by_id(input_id):
    Audio.query.filter_by(audio_id=input_id).delete()
    db.session.commit()
    return True

def update_refetch_by_id(audio_id, new_count):
    audio_obj = db.session.query(Audio).filter(Audio.audio_id==audio_id).first()
    audio_obj.refetch = new_count
    return db.session.commit()