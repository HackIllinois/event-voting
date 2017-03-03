from flask import Flask, request, jsonify
from config import config
import twilio.twiml
import pyrebase

app = Flask(__name__)

firebase = pyrebase.initialize_app(config)
ref = firebase.database()

LETTERS = ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T')


MENTOR_VOTES = 3
FACULTY_VOTES = 2

MENTOR_MULTIPLIER = 1.5
FACULTY_MULTIPLIER = 2

MAX_TABLE_NUMBER = 200


@app.route('/attendees/3361555f-0ee8-4fef-943a-c5ca80341de3', methods=["POST"])
def attendee():
	from_number = request.values.get('From', None)
	project_id = request.values.get('Body', None)

	resp = twilio.twiml.Response()
	valid_vote = validate_vote(project_id)

	if not valid_vote:
		resp.message("Sorry, the table number is not valid")
	else:
		voted = cast_attendee_vote(project_id, from_number)
		if not voted:
			resp.message("Sorry, you've already voted :(")
		else:
			resp.message("Thanks for voting!")

	return str(resp)

@app.route('/faculty/3361555f-0ee8-4fef-943a-c5ca80341de3', methods=["POST"])
def faculty():
	from_number = request.values.get('From', None)
	project_id = request.values.get('Body', None)

	resp = twilio.twiml.Response()
	valid_vote = validate_vote(project_id)

	if not valid_vote:
		resp.message("Sorry, the table number is not valid")
	else:
		voted = cast_faculty_vote(project_id, from_number)
		if not voted:
			resp.message("Sorry, you've already voted " + str(FACULTY_VOTES) +  " times")
		else:
			resp.message("Thanks for voting!")

	return str(resp)


@app.route('/mentor/3361555f-0ee8-4fef-943a-c5ca80341de3', methods=["POST"])
def mentor():
	from_number = request.values.get('From', None)
	project_id = request.values.get('Body', None)

	resp = twilio.twiml.Response()
	valid_vote = validate_vote(project_id)

	if not valid_vote:
		resp.message("Sorry, the table number is not valid")
	else:
		voted = cast_mentor_vote(project_id, from_number)
		if not voted:
			resp.message("Sorry, you've already voted " + str(MENTOR_VOTES) + " times")
		else:
			resp.message("Thanks for voting!")

	return str(resp)


@app.route('/getprizes', methods=["GET"])
def ranking():
	data = get_top_prize()
	return jsonify(data)

@app.route('/getmentorprizes', methods=["GET"])
def ranking1():
	data = get_top_mentor_prize()
	return jsonify(data)

@app.route('/getfacultyprizes', methods=["GET"])
def ranking2():
	data = get_top_faculty_prize()
	return jsonify(data)



#Check if vote is a letter-integer combo
def validate_vote(message_body):
	if len(message_body) > 2:
		return False
	try:
		column = message_body[0]
		number = int(message_body[1])
		return column.upper() in LETTERS
	except Exception as e:
		return False


###############################################
#Attendees

def cast_attendee_vote(project_id, phone_number):
	#Check if user has already voted
	try:
		ref.child("attendees").order_by_child("number").equal_to(phone_number).get().val()
		return False
	except Exception as e:
		pass		

	#Update vote counts
	try:
		project = ref.child("projects").child(project_id).get()
		attendee_votes = project.val()["attendee_votes"] + 1
		total_score = project.val()["total_score"] + 1
		mentor_votes = project.val()["mentor_votes"]
		faculty_votes = project.val()["faculty_votes"]
	except Exception as e:
		attendee_votes = 1 
		total_score = 1
		mentor_votes = 0
		faculty_votes = 0

	new_project = {"attendee_votes": attendee_votes, "total_score": total_score, "mentor_votes": mentor_votes, "faculty_votes": faculty_votes}
	ref.child("projects").child(project_id).update(new_project)
	
	#Log attendee vote
	ref.child("attendees").push({"number": phone_number})
	return True




###############################################
#Faculty

def cast_faculty_vote(project_id, phone_number):
	#Validate the faculty
	try:
		cur_faculty = ref.child("faculty").child(phone_number).get().val()
		cur_faculty_votes = cur_faculty["votes_made"]
		if cur_faculty_votes >= FACULTY_VOTES:
			return False
	#Faculty doesn't exist currently so create a new one
	except Exception as e:
		cur_faculty_votes = 0

	#Update vote counts
	try:
		project = ref.child("projects").child(project_id).get()
		attendee_votes = project.val()["attendee_votes"]
		total_score = project.val()["total_score"] + FACULTY_MULTIPLIER
		mentor_votes = project.val()["mentor_votes"]
		faculty_votes = project.val()["faculty_votes"] + 1
	except Exception as e:
		attendee_votes = 0 
		total_score = FACULTY_MULTIPLIER
		mentor_votes = 0
		faculty_votes = 1

	new_project = {"attendee_votes": attendee_votes, "total_score": total_score, "mentor_votes": mentor_votes, "faculty_votes": faculty_votes}
	ref.child("projects").child(project_id).update(new_project)

	#Log the faculty member
	ref.child("faculty").child(phone_number).update({"votes_made": cur_faculty_votes+1})
	return True
	


###############################################
#Mentor

def cast_mentor_vote(project_id, phone_number):
	#Validate the mentor
	try:
		cur_mentor = ref.child("mentors").child(phone_number).get().val()
		cur_mentor_votes = cur_mentor["votes_made"]
		if cur_mentor_votes >= MENTOR_VOTES:
			return False
	#Mentor doesn't exist currently so create a new one
	except Exception as e:
		cur_mentor_votes = 0

	#Update vote counts
	try:
		project = ref.child("projects").child(project_id).get()
		attendee_votes = project.val()["attendee_votes"]
		total_score = project.val()["total_score"] + MENTOR_MULTIPLIER
		mentor_votes = project.val()["mentor_votes"] + 1
		faculty_votes = project.val()["faculty_votes"]
	except Exception as e:
		attendee_votes = 0 
		total_score = MENTOR_MULTIPLIER
		mentor_votes = 1
		faculty_votes = 0

	new_project = {"attendee_votes": attendee_votes, "total_score": total_score, "mentor_votes": mentor_votes, "faculty_votes": faculty_votes}
	ref.child("projects").child(project_id).update(new_project)

	#Log the faculty member
	ref.child("mentors").child(phone_number).update({"votes_made": cur_mentor_votes+1})
	return True


def get_top_prize():
	data = ref.child("projects").order_by_child("total_score").get().val()
	projects = []
	for project in data.items():
		projects.append((project[0], project[1]['total_score']))
	return projects

def get_top_mentor_prize():
	data = ref.child("projects").order_by_child("mentor_votes").get().val()
	projects = []
	for project in data.items():
		try:
			projects.append((project[0], project[1]['mentor_votes']))
		except Exception:
			projects.append((project[0], 0))
	return projects

def get_top_faculty_prize():
	data = ref.child("projects").order_by_child("faculty_votes").get().val()
	projects = []
	for project in data.items():
		try:
			projects.append((project[0], project[1]['faculty_votes']))
		except Exception:
			projects.append((project[0], 0))
	return projects



if __name__ == "__main__":
	app.run()
