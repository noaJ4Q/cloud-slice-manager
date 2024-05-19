from flask import Flask, request, jsonify
import jwt

app = Flask(__name__)

USERS = [
  {
    'username': 'branko',
    'password': 'branko',
    'role': 'manager'
  },
  {
    'username': 'mavend',
    'password': 'mavend',
    'role': 'client'
  },
  {
    'username': 'willy',
    'password': 'willy',
    'role': 'admin'
  }
]

@app.route('/auth', methods=['POST'])
def auth_user():

  # Get the username and password from JSON request
  username = request.json['username']
  password = request.json['password']

  user = validate_user(username, password)
  if user: 
    token = jwt.encode({'role': user['role']}, 'secret', algorithm='HS256')
    return jsonify({'message': 'success', 'token': token})
  else:
    return jsonify({'message': 'Invalid username or password'})

def validate_user(username, password):
  for user in USERS:
    if user['username'] == username and user['password'] == password:
      return user
  return None

if __name__=='__main__':
  app.run()