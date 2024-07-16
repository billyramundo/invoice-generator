from flask import Flask, jsonify, render_template, send_from_directory, request, send_file
from flask_cors import CORS
import os
import process as process
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='frontend/public')
CORS(app)

app.config['TAX_API_KEY'] = os.getenv('TAX_API_KEY')

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')
    
@app.route('/create_pdf', methods=['POST'])
def create_pdf():
    data = request.json
    print(data.get('url'))
    try:
        pdf_buffer = process.get_details(data)
    except Exception as e:
        return jsonify({"error":str(e)}), 500
    
    return send_file(pdf_buffer, as_attachment=True, download_name='completed-invoice.pdf', mimetype='application/pdf')
    
if __name__ == '__main__':
    app.run(debug=True)