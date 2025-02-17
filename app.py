from flask import Flask, render_template, request, jsonify
from youtube_captioner import YoutubeCaptioner
from utils import validate_youtube_url
import os
import time
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, URL

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

class YouTubeURLForm(FlaskForm):
    youtube_url = StringField('YouTube URL', validators=[DataRequired(), URL()])

@app.route('/', methods=['GET'])
def index():
    form = YouTubeURLForm()
    return render_template('index.html', form=form)

@app.route('/generate-captions', methods=['POST'])
def generate_captions():
    url = request.form.get('youtube_url')
    if not url or not validate_youtube_url(url):
        return jsonify({
            'error': 'Invalid YouTube URL. Please provide a valid YouTube video URL.'
        }), 400

    try:
        output_file = f'output_{int(time.time())}.srt'
        captioner = YoutubeCaptioner()

        # Start the transcription process
        captioner.generate_captions(url, output_file)

        # Read generated captions
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                captions = f.read()

            # Clean up the file after reading
            try:
                os.remove(output_file)
            except:
                pass  # Ignore cleanup errors

            return jsonify({
                'success': True,
                'captions': captions,
                'message': 'Captions generated successfully!'
            })
        else:
            return jsonify({
                'error': 'Failed to generate captions. Please try again.'
            }), 500

    except Exception as e:
        error_message = str(e)
        return jsonify({
            'error': f'An error occurred: {error_message}'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)