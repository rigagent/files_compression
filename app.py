import envoy
import os.path
from datetime import datetime
from flask import Flask, render_template, request, url_for, send_file, redirect
from flask_uploads import UploadSet, configure_uploads, IMAGES
from flask_sqlalchemy import SQLAlchemy

ORIGINAL_FILES_PATH = 'static/images/original_images/'
COMPRESSED_FILES_PATH = 'static/images/compressed_images/'
app = Flask(__name__)
photos = UploadSet('photos', IMAGES)
app.config['UPLOADED_PHOTOS_DEST'] = ORIGINAL_FILES_PATH
configure_uploads(app, photos)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///files.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class NewFile(db.Model):
    f_id = db.Column(db.Integer, primary_key=True)
    f_name = db.Column(db.String(100), nullable=False)
    f_size = db.Column(db.Float, nullable=False)
    f_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<File %r>' % self.f_id


@app.route('/')
@app.route('/main')
def index():
    return render_template('index.html')


@app.route('/jpg_files')
def jpg_files():
    files = NewFile.query.order_by(NewFile.f_date.desc()).all()
    return render_template("jpg_files.html", files=files)


@app.route('/add_jpg_file', methods=['POST', 'GET'])
def add_jpg_file():
    f_name = ""
    f_size = ""
    if request.method == 'POST' and 'photo' in request.files:
        f_name = str(photos.save(request.files['photo']))
        f_size = os.stat('{}{}'.format(ORIGINAL_FILES_PATH, f_name)).st_size / 1000
        new_file = NewFile(f_name=f_name, f_size=f_size)
        try:
            db.session.add(new_file)
            db.session.commit()
            return render_template('add_jpg_file.html', context=[f_name, f_size])
        except:
            return "There was an error when the new JPG file adding..."

    else:
        return render_template('add_jpg_file.html', context=[f_name, f_size])


@app.route('/jpg_files/<int:f_id>/del_jpg_file')
def del_jpg_file(f_id):
    file = NewFile.query.get_or_404(f_id)
    try:
        if os.path.exists("{}{}".format(ORIGINAL_FILES_PATH, file.f_name)):
            envoy.run("rm -r {}{}".format(ORIGINAL_FILES_PATH, file.f_name))
        if os.path.exists("{}{}".format(COMPRESSED_FILES_PATH, file.f_name)):
            envoy.run("rm -r {}{}".format(COMPRESSED_FILES_PATH, file.f_name))
        db.session.delete(file)
        db.session.commit()
        return redirect('/jpg_files')
    except:
        return "There was an error when the file deleting..."


@app.route('/jpg_files/<int:f_id>/compress_jpg_file', methods=['POST', 'GET'])
def compress_jpg_file(f_id):
    file = NewFile.query.get(f_id)
    if request.method == 'POST':
        new_f_size = request.form['size']
        envoy.run("jpegoptim --size={} {}{} -d {}".format(new_f_size, ORIGINAL_FILES_PATH,
                                                          file.f_name, COMPRESSED_FILES_PATH))
    return render_template('compress_jpg_file.html', file=file)


@app.route('/jpg_files/<int:f_id>/download_compressed_jpg_file')
def download_compressed_jpg_file(f_id):
    file = NewFile.query.get(f_id)
    path = "{}{}".format(COMPRESSED_FILES_PATH, file.f_name)
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)
