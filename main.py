from flask import Flask, request, jsonify
import jwt

app = Flask(__name__)

@app.route('/auth', methods=['POST'])
def auth_user():

  # Get the username and password from JSON request
  username = request.json['username']
  password = request.json['password']

  # Check if the username and password are not empty
  if username and password:
    if valid_user(username, password):
      token = jwt.encode({'username': username}, 'secret', algorithm='HS256')
      return jsonify({'message': 'success', 'token': token})
  else:
    return jsonify({'message': 'Username and password are required'})

def valid_user(username, password):
  return True

if __name__=='__main__':
  app.run()