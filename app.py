import os
import subprocess
import sys
import logging
import shutil
from flask import Flask, jsonify, render_template, request

from model.database import db
from controller import main_controller
import json

app = Flask(__name__)
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['TEMP_FOLDER'] = '/tmp'
app.config['OCR_OUTPUT_FILE'] = 'ocr'
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024
# add configuration values
app.config.from_pyfile('config.py')
# set up database
db.init_app(app)
with app.test_request_context():
    # drop all tables
    # db.drop_all()
    # create all table on load
    db.create_all()


@app.errorhandler(404)
def not_found(error):
    resp = jsonify( {
        u'status': 404,
        u'message': u'Resource not found'
    } )
    resp.status_code = 404
    return resp

@app.route('/')
def api_root():
    resp = jsonify( {
        u'status': 200,
        u'message': u'Welcome to our secret APIs'
    } )
    resp.status_code = 200
    return resp

@app.route('/s3/all', methods = ['GET'])
def getAllS3Files():
    bucket =  main_controller.get_all_s3_files()
    return render_template('s3_table.html', bucket = bucket)

@app.route('/file', methods = ['GET'])
def upload():
    # return render_template('upload_file.html', landing_page = 'fileupload')
    return render_template('upload_file.html', landing_page = 'webfileupload')

@app.route('/audio', methods = ['GET'])
def audio_html():
    return render_template('upload_audio.html', landing_page = 'audioupload')
    # return render_template('upload_audio.html')

@app.route('/webfileupload', methods = ['GET', 'POST'])
def elderly_web_fileupload():
    print "Check POST or GET method."
    if request.method == 'POST':
        file = request.files['file']
        print file
        data = main_controller.elderly_web_file_upload(file)
        # print str(data)
        image_id = data['image_id']
        audio_id = data['audio_id']
        audio_url = data['audio_url']
        output = data['output']
        return render_template('play.html', image_id = image_id, audio_id = audio_id,
                               audio_url = audio_url, output=output,
                               url_audiorefetch = 'webaudiorefetch',back='file')

    elif request.method == 'GET':
        resp = jsonify( {
                u'status': 200,
                u'message': str('File Upload: I\'m working.')
            } )
        resp.status_code = 200
        return resp
    return None

@app.route('/fileupload', methods = ['GET', 'POST'])
def elderly_fileupload():
    if request.method == 'POST':
        file = request.files['file']
        # print file
        return main_controller.elderly_file_upload(file)
    elif request.method == 'GET':
        resp = jsonify( {
                u'status': 200,
                u'message': str('File Upload: I\'m working.')
            } )
        resp.status_code = 200
        return resp
    return None

@app.route('/audioupload', methods = ['GET', 'POST'])
def audio_upload():
    if request.method == 'POST':
        dataDict = request.form
        image_id = dataDict['image_id']
        file = request.files['file']
        # print file
        return main_controller.audioupload(file, image_id)
    elif request.method == 'GET':
        resp = jsonify( {
                u'status': 200,
                u'message': str('Audio Upload: I\'m working.')
            } )
        resp.status_code = 200
        return resp
    return None

@app.route('/webaudiorefetch', methods = ['GET', 'POST'])
def update_web_audio_refetch():
    if request.method == 'POST':
        print str(request.form)
        dataDict = request.form
        image_id = dataDict['image_id']
        audio_id = dataDict['audio_id']
        output = dataDict['output'].encode('utf-8')
        print str(image_id) + "," + str(audio_id)
        # print file
        data = main_controller.update_web_refetch(image_id, audio_id)
        # print str(data)
        ret_image_id = data['image_id']
        ret_audio_id = data['audio_id']
        ret_audio_url = data['audio_url']

        return render_template('play.html', image_id = ret_image_id, audio_id = ret_audio_id,
                               audio_url = ret_audio_url, output=output,
                               url_audiorefetch = 'webaudiorefetch', back='file')
    elif request.method == 'GET':
        resp = jsonify( {
                u'status': 200,
                u'message': str('Audio Refetch: I\'m working.')
            } )
        resp.status_code = 200
        return resp
    return None

@app.route('/audiorefetch', methods = ['GET', 'POST'])
def update_audio_refetch():
    if request.method == 'POST':
        # print str(request.form)
        dataDict = request.form
        image_id = dataDict['image_id']
        audio_id = dataDict['audio_id']
        print str(image_id) + "," + str(audio_id)
        # print file
        return main_controller.update_refetch(image_id, audio_id)
    elif request.method == 'GET':
        resp = jsonify( {
                u'status': 200,
                u'message': str('Audio Refetch: I\'m working.')
            } )
        resp.status_code = 200
        return resp
    return None

@app.route('/test/compareimg', methods = ['GET', 'POST'])
def compareImage():
    if request.method == 'POST':
        # files = request.files.getlist("file")
        file = request.files['file']
        resp = jsonify( {
            u'status': 200,
            u'message': str(main_controller.compareImage(file))
        })
        resp.status_code = 200
        return resp
    elif request.method == 'GET':
        resp = jsonify( {
            u'status': 200,
            u'message': str('I\'m working.')
        })
        resp.status_code = 200
        return resp

@app.route('/test/js', methods = ['GET'])
def test_js():
    return main_controller.exec_webspeech('Hello')

@app.route('/test/fileupload', methods = ['GET', 'POST'])
def test_fileUpload():
    if request.method == 'POST':
        file = request.files['file']
        # print file
        return main_controller.test_file_upload(file)
    elif request.method == 'GET':
        resp = jsonify( {
                u'status': 200,
                u'message': str('I\'m working.')
            } )
        resp.status_code = 200
        return resp
    return None

@app.route('/test/translate', methods = ['GET'])
def test_translate():
    return main_controller.translator('Hello')

@app.route('/cls/tmp', methods = ['GET'])
def clear_tmp_directory():
    dirPath = app.config['TEMP_FOLDER']
    if os.path.exists(dirPath):
        fileList = os.listdir(dirPath)
        for fileName in fileList:
         os.remove(dirPath+"/"+fileName)
    return 'Cleared the tmp folder.'

@app.route('/db/clearaudios', methods = ['GET'])
def db_clear_audios_table():
    main_controller.clear_audios_table()
    return 'Cleared audios table data'

@app.route('/db/clearimages', methods = ['GET'])
def db_clear_images_table():
    main_controller.clear_images_table()
    return 'Cleared images table data'

@app.route('/db/images/all', methods = ['GET'])
def db_all_images_table():
    results = main_controller.db_all_images_record()
    return render_template('images_db_table.html', obj_list = results)

@app.route('/db/audios/all', methods = ['GET'])
def db_all_audios_table():
    results = main_controller.db_all_audios_record()
    print str(results)
    return render_template('audios_db_table.html', obj_list = results)

@app.route('/db/images/delete', methods = ['GET'])
def db_delete_image_record():
    id = request.args.get('imageid')
    main_controller.db_delete_image_record(id)
    return 'Image record deleted.'

@app.route('/db/audios/delete', methods = ['GET'])
def db_delete_audio_record():
    id = request.args.get('audioid')
    main_controller.db_delete_audio_record(id)
    return 'Audio record deleted.'

@app.route('/db/audios/update', methods = ['GET'])
def db_update_refetch():
    id = request.args.get('audioid')
    new_count = request.args.get('count')
    main_controller.db_update_audio_refetch(id, new_count)
    return 'Audio record\'s refetch count has been updated.'

if __name__ == '__main__':
    # app.run(debug=True)
    app.run(app.config.get('HOST'), app.config.get('PORT'), app.debug)
