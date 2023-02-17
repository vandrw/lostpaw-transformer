from flask import Flask, request, jsonify
from PIL import Image
from numpy import array
import argparse
from lostpaw.model import PetViTContrastiveModel

app = Flask(__name__)
model = PetViTContrastiveModel()

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json(force=True)

    # Convert data to numpy array
    data = array(data['data'])

    # Convert data to PIL image
    image = Image.fromarray(data)

    latent_space = model(image)

    output = {'latent_space': latent_space.tolist()}
    return jsonify(output)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, required=True)
    args = parser.parse_args()

    model.load_model(args.model)

    app.run(port=5000, debug=True)