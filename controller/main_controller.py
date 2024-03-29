from PIL import Image

__author__ = 'SARA'
import datetime
from flask import Flask, jsonify, current_app as app
from collections import OrderedDict
from werkzeug import secure_filename
from mstranslator import Translator
import urllib2, urllib, re

from manager import ocr_manager, recognition_manager, s3_manager, image_manager, audio_manager, date_manager

def image_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in set(['PNG', 'png', 'JPG', 'jpg', 'JPEG', 'jpeg', 'GIF', 'gif'])

def audio_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in set(['mp3'])

def getCurrentTimestamp():
    return str(datetime.datetime.now()).split('.')[0].translate(None, '-: ')

def get_all_s3_files():
    bucket = s3_manager.get_all_s3_files()
    arr = []
    count = 0
    for key in bucket:
        dict = {}
        file_name = key.name.decode('utf-8')
        dict['name'] = file_name
        if count != 0:
            dict['date'] = date_manager.convert_datetime(file_name.split('_')[0])
        else:
            dict['date'] = None
        # ts[0:4] + '-' + ts[4:6] + '-' + ts [6:8] + ' ' + ts[8:10] + ':' + ts[10:12] + ':' + ts[12:14]
        arr.append(dict)
        count += 1
    return arr

def elderly_web_file_upload(file):
    print "Check file exist a not"
    if file and image_allowed_file(file.filename):
        image_file_name = getCurrentTimestamp() + '_' + secure_filename(file.filename) #filename and extension
        print "Image file name: " + str(image_file_name)
        image_file_path = image_manager.saveFile(file, image_file_name)
        print "Uploaded file is saved. (" + str(image_file_name) + ")"
        # upload to amazon s3
        image_s3_url = s3_manager.upload_image_audio_to_s3(image_file_name, image_file_path)
        print "Uploaded file url: " + str(image_s3_url)
        # image recognition
        has_existing_image = image_process(image_s3_url)
        print "Existing Image: " + str(has_existing_image)
        if has_existing_image is not None:
            # get the audio
            audio_obj = audio_manager.get_audio_lowest_refetch_image_only(has_existing_image)
            # print "Audio obj:" + str(audio_obj)
            output = ocr_manager.process_image(image_s3_url)
            output_arr = re.split('[ \n\t\r]', output)
            output = " ".join(output_arr)
            chinese_output = translator(output)
            resp = {
                'image_id': str(has_existing_image),
                'audio_id': str(audio_obj.audio_id),
                'audio_url': str(audio_obj.audio_url),
                'output' : chinese_output,
                'message': str('Successful file upload.')
            }
            return resp
        # insert to database
        image_id = image_manager.insert_image_to_db(image_s3_url)
        # process the image via ocr
        output = ocr_manager.process_image(image_s3_url)
        output_arr = re.split('[ \n\t\r]', output)
        output = " ".join(output_arr)
        print str(output)
        # translate ocr output to chinese
        chinese_output = translator(output)
        # print 'Chinese output: ' + chinese_output.encode('utf-8')
        # call js
        audio_file_name = getCurrentTimestamp() + '_' + "output.mp3"
        audio_file_path = audio_manager.getAudioFilePath(audio_file_name)
        audio_dl_file = exec_webspeech(chinese_output, audio_file_path)
        audio_s3_url = s3_manager.upload_image_audio_to_s3(audio_file_name, audio_file_path)
        # insert audio to db
        audio_id = audio_manager.insert_audio_to_db(audio_s3_url, image_id, 1)
        resp = {
            'status': 200,
            'image_id': str(image_id),
            'audio_id': str(audio_id),
            'audio_url': str(audio_s3_url),
            'output' : str(chinese_output),
            'message': str('Successful file upload.')
        }
        # delete file
        image_manager.deleteFile(image_file_path)
        audio_manager.deleteAudioFile(audio_file_path)
        return resp
    else:
        error_resp = {
            'status': 201,
            'message': str('Not process')
        }
        return error_resp

def elderly_file_upload(file):
    if file and image_allowed_file(file.filename):
        image_file_name = getCurrentTimestamp() + '_' + secure_filename(file.filename) #filename and extension
        image_file_path = image_manager.saveFile(file, image_file_name)
        # upload to amazon s3
        image_s3_url = s3_manager.upload_image_audio_to_s3(image_file_name, image_file_path)
        # print image_s3_url
        # image recognition
        has_existing_image = image_process(image_s3_url)
        print "Existing Image: " + str(has_existing_image)
        if has_existing_image is not None:
            # get the audio
            audio_obj = audio_manager.get_audio_lowest_refetch_image_only(has_existing_image)
            # print "Audio obj:" + str(audio_obj)
            resp = jsonify( {
                u'status': 200,
                u'image_id': str(has_existing_image),
                u'audio_id': str(audio_obj.audio_id),
                u'audio_url': str(audio_obj.audio_url),
                u'message': str('Successful file upload.')
            } )
            resp.status_code = 200
            return resp
        # insert to database
        image_id = image_manager.insert_image_to_db(image_s3_url)
        # process the image via ocr
        output = ocr_manager.process_image(image_s3_url)
        output_arr = re.split('[ \n\t\r]', output)
        output = " ".join(output_arr)
        print str(output)
        # translate ocr output to chinese
        chinese_output = translator(output)
        # print 'Chinese output: ' + chinese_output.encode('utf-8')
        # call js
        audio_file_name = getCurrentTimestamp() + '_' + "output.mp3"
        audio_file_path = audio_manager.getAudioFilePath(audio_file_name)
        audio_dl_file = exec_webspeech(chinese_output, audio_file_path)
        audio_s3_url = s3_manager.upload_image_audio_to_s3(audio_file_name, audio_file_path)
        # insert audio to db
        audio_id = audio_manager.insert_audio_to_db(audio_s3_url, image_id, 1)
        resp = jsonify( {
            u'status': 200,
            u'image_id': str(image_id),
            u'audio_id': str(audio_id),
            u'audio_url': str(audio_s3_url),
            u'message': str('Successful file upload.')
        } )
        resp.status_code = 200
        # delete file
        image_manager.deleteFile(image_file_path)
        audio_manager.deleteAudioFile(audio_file_path)
        return resp
    else:
        error_resp = jsonify({
            u'status': 201,
            u'message': str('Not process')
        } )
        error_resp.status_code = 201
        return error_resp

def image_process(new_uploaded_url):
    results = {}
    # retrieve 1 months worth of images from DB
    files_to_compare = image_manager.list_compare_images(30)
    print 'Retrieve data: ' + str(len(files_to_compare))
    if len(files_to_compare) == 0:
        return None
    else:
        for img_obj in files_to_compare:
            img_obj_id = img_obj.image_id
            img_obj_url = img_obj.image_url
            similarity = recognition_manager.get_images_rms_similarity(new_uploaded_url, img_obj_url)
            results[img_obj_id] = similarity
        sort_results = OrderedDict(sorted(results.items(),key=lambda kv: kv[1], reverse=True))
        # get the first element
        image_id, highest_similarity = sort_results.items()[0]
        print "Similarity: " + str(highest_similarity)
        # threshold for similarity
        if highest_similarity >= 95:
            return image_id
    return None

def compareImage(file):
    if file and image_allowed_file(file.filename):
        filename = getCurrentTimestamp() + '_' + secure_filename(file.filename) #filename and extension
        file_path = image_manager.saveFile(file, filename)
        # upload to amazon s3
        s3_url = s3_manager.upload_image_audio_to_s3(filename, file_path)
        return image_process(s3_url)
    return None

def translator(text):
    translator = Translator(app.config['MS_TRANSLATOR_CLIENT_ID'], app.config['MS_TRANSLATOR_CLIENT_SECRET'])
    # return translator.translate(text, "zh-CHT").encode('utf-8')
    return translator.translate(text, None, lang_to='zh-CHT').encode('utf-8')

def exec_webspeech(text, file_path):
    url = 'http://120.24.87.124/cgi-bin/ekho2.pl?cmd=SAVEMP3&voice=EkhoCantonese&speedDelta=0&pitchDelta=0&volumeDelta=0&text=' + text
    f = urllib2.urlopen(url)
    with open(file_path, "wb") as code:
        code.write(f.read())
    return True
    # return urllib.urlretrieve (url, filepath)

def update_web_refetch(image_id, audio_id):
    new_audio_obj = None
    if int(audio_id) == 0:
        print "audio id is 0."
        new_audio_obj = audio_manager.get_audio_lowest_refetch_image_only(image_id)
    else:
        # get audio object and  update audio object
        audio_manager.update_audio_refetch(audio_id)
        # get the next best audio
        new_audio_obj = audio_manager.get_audio_lowest_refetch(image_id, audio_id)
    # print str(new_audio_obj)
    if new_audio_obj is None:
        resp = {
            'status': 200,
            'image_id': str(image_id),
            'audio_id': str(0),
            'audio_url': str('https://s3-ap-southeast-1.amazonaws.com/media2.pi-diddy.herokuapp.com/20151119112202_output.mp3'),
            'message': str('Successful refetch.')
        }
        return resp
    else:
        new_audio_id = new_audio_obj.audio_id
        new_audio_url = new_audio_obj.audio_url
        print str(new_audio_id) + "," + str(new_audio_url)
        resp = {
            'status': 200,
            'image_id': str(image_id),
            'audio_id': str(new_audio_id),
            'audio_url': str(new_audio_url),
            'message': str('Successful refetch.')
        }
        return resp

def update_refetch(image_id, audio_id):
    new_audio_obj = None
    if int(audio_id) == 0:
        print "audio id is 0."
        new_audio_obj = audio_manager.get_audio_lowest_refetch_image_only(image_id)
    else:
        # get audio object and  update audio object
        audio_manager.update_audio_refetch(audio_id)
        # get the next best audio
        new_audio_obj = audio_manager.get_audio_lowest_refetch(image_id, audio_id)
    # print str(new_audio_obj)
    if new_audio_obj is None:
        resp = jsonify( {
            u'status': 200,
            u'image_id': str(image_id),
            u'audio_id': str(0),
            u'audio_url': str('https://s3-ap-southeast-1.amazonaws.com/media2.pi-diddy.herokuapp.com/20151119112202_output.mp3'),
            u'message': str('Successful refetch.')
        })
        return resp
    else:
        new_audio_id = new_audio_obj.audio_id
        new_audio_url = new_audio_obj.audio_url
        print str(new_audio_id) + "," + str(new_audio_url)
        resp = jsonify( {
            u'status': 200,
            u'image_id': str(image_id),
            u'audio_id': str(new_audio_id),
            u'audio_url': str(new_audio_url),
            u'message': str('Successful refetch.')
        } )
        resp.status_code = 200
    return resp

def audioupload(file, image_id):
    if file and audio_allowed_file(file.filename):
        audio_file_name = getCurrentTimestamp() + '_' + secure_filename(file.filename) #filename and extension
        audio_file_path = audio_manager.saveAudioFile(file, audio_file_name)
        audio_s3_url = s3_manager.upload_image_audio_to_s3(audio_file_name, audio_file_path)
        # insert audio to db
        audio_id = audio_manager.insert_audio_to_db(audio_s3_url, image_id, 0)
        resp = jsonify( {
            u'status': 200,
            u'image_id': str(image_id),
            u'audio_id': str(audio_id),
            u'audio_url': str(audio_s3_url),
            u'message': str('Successful file upload.')
        } )
        resp.status_code = 200
        audio_manager.deleteAudioFile(audio_file_path)
        return resp
    return None

def clear_audios_table():
    return audio_manager.clear_audios_table()

def clear_images_table():
    return image_manager.clear_images_table()

def db_all_images_record():
    list = image_manager.get_all_images_record_db()
    arr = []
    for img in list:
        dict = {}
        dict['id'] = img.image_id
        dict['url'] = img.image_url
        dict['create'] = date_manager.convert_time_unix_to_human_timestamp(img.created_on)
        dict['update'] = date_manager.convert_time_unix_to_human_timestamp(img.updated_on)
        arr.append(dict)

    return arr

def db_all_audios_record():
    audio_list = audio_manager.get_all_audios_record_db()
    arr = []
    for img in audio_list:
        dict = {}
        dict['id'] = img.audio_id
        dict['url'] = img.audio_url
        dict['count'] = img.refetch
        dict['iid'] = img.image_id
        dict['create'] = date_manager.convert_time_unix_to_human_timestamp(img.created_on)
        dict['update'] = date_manager.convert_time_unix_to_human_timestamp(img.updated_on)
        arr.append(dict)

    return arr

def db_delete_image_record(id):
    return image_manager.delete_image_by_id(id)

def db_delete_audio_record(id):
    return audio_manager.delete_audio_by_id(id)

def db_update_audio_refetch(audio_id, new_count):
    return audio_manager.update_refetch_by_id(audio_id, new_count)

def test_file_upload(file):
    if file and image_allowed_file(file.filename):
        filename = getCurrentTimestamp() + '_' + secure_filename(file.filename) #filename and extension
        file_path = image_manager.saveFile(file, filename)
        # upload to amazon s3
        s3_url = s3_manager.upload_image_audio_to_s3(filename, file_path)
        # print s3_url
        # insert to database
        # image_id = image_manager.insert_image_to_db(s3_url)
        # print image_id
        # process the image via ocr
        output = ocr_manager.process_image(s3_url)
        output_arr = re.split('[ \n\t\r]', output)
        output = " ".join(output_arr)
        print str(output)
        # translate ocr output to chinese
        # chinese_output = translator(output)
        resp = jsonify( {
            u'status': 200,
            u'message': str(output)
        } )
        resp.status_code = 200
        # delete file
        image_manager.deleteFile(file_path)
        return resp
    else:
        error_resp = jsonify({
            u'status': 200,
            u'message': str('Not process')
        } )
        error_resp.status_code = 200
        return error_resp
