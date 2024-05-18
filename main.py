from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/auth', methods=['POST'])
def auth_user():
  # Get the username and password from JSON request
  username = request.json['username']
  password = request.json['password']
  # Check if the username and password are not empty
  if username and password:
    return jsonify({'message': 'User authenticated successfully'})
  else:
    return jsonify({'message': 'Username and password are required'})

if __name__=='__main__':
  app.run()