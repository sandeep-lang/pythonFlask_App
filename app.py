from bson import ObjectId
from flask import Flask, jsonify, request
from flask_restful import Api
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

app = Flask(__name__)
api = Api(app)

app.config['JWT_SECRET_KEY'] = '33a2ce62c4804b3599ad46725a6f249a' #for JWT
jwt = JWTManager(app)

# Set up MongoDB connection
app.config['MONGO_URI'] = "mongodb+srv://sandeep:sandeepkumar@first.ok2bf5i.mongodb.net/details_db?retryWrites=true&w=majority" #Connection string to connect with the database and tables that are in MongoDB Atlas
mongo = PyMongo(app)


# Registration Function
@app.route('/register',methods=['POST']) #URLendpoint for register
def Register():
    data = request.get_json()
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    password = data.get('password')
    if not first_name or not last_name or not email or not password:
        return {'message': "All fields are required"}, 401
    existing_user = mongo.db.User_Details.find_one({'email': email}) #checking if emial is already present or not
    if existing_user:
        return {'message': 'Already user registered with this Email.Try with new one.'}, 409
    hash_password = generate_password_hash(password)#password hashing 
    mongo.db.User_Details.insert_one({
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'password': hash_password,
        
    })# Inseing Details of the User
    return {'message': 'Registration Successfull. Login to continue.'}, 201

# Login Function
@app.route('/login',methods=['POST'])#URLendpoint for login
def Login():
     data = request.get_json()
     email = data.get('email')
     password = data.get('password')
     if not email or not password:
        return {'message': 'Both fields are required'}, 400
     user = mongo.db.User_Details.find_one({'email': email}) #checking if user is there
     print('user',user)
     if user and check_password_hash(user['password'], password): # if name and password matched
        Token = create_access_token(identity=email)#Creating Token 
        return {'access_token': Token}, 200
     else:
        return {'message': 'Invalid Details'}, 401
    

templates_collection = mongo.db.templates_collection #templates_collection is a collection (Table) in  details_db is database. 
@app.route('/template', methods=['POST']) # URLendpoint for Creating Template
@jwt_required()
def create_template():
    current_user = get_jwt_identity()
    #print('h',current_user)
    users = mongo.db.User_Details
    user = users.find_one({'email': current_user})
    

    if user:
        template_details = request.get_json()
        print(template_details)
        template = template_details.get('template', '')
        #print(template_name)
        subject = template_details.get('subject', '')
        body = template_details.get('body', '')

        user_template = {'email': current_user, 'template': template}
        doc = templates_collection.find_one(user_template)
        if doc:
            return jsonify({'message': 'Template already exists on your profile'}), 400

        
        template_document = {
            'email': current_user,
            'template': template,
            'subject': subject,
            'body': body
        }
        templates_collection.insert_one(template_document)
        return jsonify({'message': 'Template created successfully'}), 200
    else:
        return jsonify({'message': 'User not found'}), 404

@app.route('/template', methods=['GET']) #Getting the template details of logged user by using token
@jwt_required()
def get_user_templates():
    current_user = get_jwt_identity()
    user_templates = templates_collection.find({'email': current_user})
    #print(user_templates)
    
    templates = []
    #print("K")
    for template in user_templates:
        templates.append({
            'id': str(template['_id']),
            'template': template['template'],
            'subject': template['subject'],
            'body': template['body']
            
           
            
        })
        #print(templates)
    if not templates:
        return jsonify({'message': 'No templates found for this user'}), 404
    return jsonify(templates), 200


@app.route('/template/<template_id>', methods=['GET']) #Getting template details of a particular user by using templateid 
@jwt_required()
def GetDetail(template_id):
    current_user = get_jwt_identity()
    user_template = templates_collection.find_one({'_id':ObjectId(template_id),'email':current_user})
    if user_template:
        template_details = {
            '_id': str(user_template['_id']),  # Convert ObjectId to string
            'template': user_template['template'],
            'subject': user_template['subject'],
            'body': user_template['body']
        }
        return jsonify(template_details), 200
    else:
        return jsonify({'message': 'Template not found'}), 404


@app.route('/template/<template_id>', methods=['PUT']) #Updating the template details of a particular user
@jwt_required()
def update_template(template_id):
    current_user = get_jwt_identity()

    # Assuming you have a request with JSON data containing the updated template fields
    updated_data = request.get_json()
    print(updated_data)

    # Update the template in the database
    result = templates_collection.update_one(
        {'_id': ObjectId(template_id), 'email': current_user},
        {'$set': updated_data}
    )

    if result.modified_count == 1:
        return jsonify({'msg': 'Template updated successfully'}), 200
    else:
        return jsonify({'msg': 'Template not found or not authorized to update'}), 404

@app.route('/template/<template_id>', methods=['DELETE']) #Deleting the particular user template details
@jwt_required()
def delete_template(template_id):
    current_user = get_jwt_identity()
    user = templates_collection.delete_one({'_id':ObjectId(template_id),'email':current_user})
    if user.deleted_count ==1:
        return jsonify({'message':'Template deleted succesfully'}),200
    else:
        return jsonify({'Template not found'}),404

if __name__ == '__main__':
    app.run(debug=True)