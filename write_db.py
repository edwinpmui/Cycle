""" write to a SQLite database with forms, templates
    add new record, delete a record, edit/update a record
    """

from flask import Flask, render_template, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap

from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField, RadioField, HiddenField, StringField, IntegerField, FloatField
from wtforms.validators import InputRequired, Length, Regexp, NumberRange
from datetime import date

app = Flask(__name__)

# Flask-WTF requires an enryption key - the string can be anything
app.config['SECRET_KEY'] = 'MLXH243GssUWwKdTWS7FDhdwYF56wPj8'

# Flask-Bootstrap requires this line
Bootstrap(app)

# the name of the database; add path if necessary
db_name = 'routes.db'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_name

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# this variable, db, will be used for all SQLAlchemy commands
db = SQLAlchemy(app)

# each table in the database needs a class to be created for it
# db.Model is required - don't change it
# identify all columns by name and data type
class Route(db.Model):
    __tablename__ = 'routes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    start = db.Column(db.String)
    end = db.Column(db.String)
    dangerlevel = db.Column(db.Integer)
    updated = db.Column(db.String)

    def __init__(self, name, start, end, dangerlevel,updated):
        self.name = name
        self.start = start
        self.end = end
        self.dangerlevel = dangerlevel
        self.updated = updated
       

# +++++++++++++++++++++++
# forms with Flask-WTF

# form for add_record and edit_or_delete
# each field includes validation requirements and messages
class AddRecord(FlaskForm):
    # id used only by update/edit
    id_field = HiddenField()
    name = StringField('Route name', [ InputRequired(),])
    start = StringField('Starting Point', [ InputRequired(),])
    end = StringField('Destination', [ InputRequired(),])
    dangerlevel = IntegerField('How dangerous?', [ InputRequired(),
        NumberRange(min=1, max=10, message="Invalid range")
        ])
    
    # updated - date - handled in the route
    updated = HiddenField()
    submit = SubmitField('Add/Update Record')

# small form
class DeleteForm(FlaskForm):
    id_field = HiddenField()
    purpose = HiddenField()
    submit = SubmitField('Delete This Route')

# +++++++++++++++++++++++
# get local date - does not account for time zone
# note: date was imported at top of script
def stringdate():
    today = date.today()
    date_list = str(today).split('-')
    # build string in format 01-01-2000
    date_string = date_list[1] + "-" + date_list[2] + "-" + date_list[0]
    return date_string

# +++++++++++++++++++++++
# routes

@app.route('/<name>')
def index(name):
    routes = Route.query.filter_by(name=name).order_by(Route.name).all()
    return render_template('index.html', routes=routes, name = name)

@app.route('/inventory/<name>')
def inventory(name):
    routes = Route.query.filter_by(name=name).order_by(Route.name).all()
    return render_template('list.html', routes = routes, name = name)


@app.route('/add_record', methods=['GET', 'POST'])
def add_record():
    form1 = AddRecord()
    if form1.validate_on_submit():
        name = request.form['name']
        start = request.form['start']
        end = request.form['end']
        dangerlevel = request.form['dangerlevel']
        # get today's date from function, above all the routes
        updated = stringdate()
        # the data to be inserted into Sock model - the table, socks
        record = Route(name, start, end, dangerlevel, updated)
        # Flask-SQLAlchemy magic adds record to database
        db.session.add(record)
        db.session.commit()
        # create a message to send to the template
        message = f"The data for route {name} has been submitted."
        return render_template('add_record.html', message=message)
    else:
        # show validaton errors
        # see https://pythonprogramming.net/flash-flask-tutorial/
        for field, errors in form1.errors.items():
            for error in errors:
                flash("Error in {}: {}".format(
                    getattr(form1, field).label.text,
                    error
                ), 'error')
        return render_template('add_record.html', form1=form1)

# select a record to edit or delete
@app.route('/select_record/<letters>')
def select_record(letters):
    # alphabetical lists by sock name, chunked by letters between _ and _
    # .between() evaluates first letter of a string
    a, b = list(letters)
    routes = Route.query.filter(Route.name.between(a, b)).order_by(Route.name).all()
    return render_template('select_record.html', routes=routes)

# edit or delete - come here from form in /select_record
@app.route('/edit_or_delete', methods=['POST'])
def edit_or_delete():
    id = request.form['id']
    choice = request.form['choice']
    route = Route.query.filter(Route.id == id).first()
    # two forms in this template
    form1 = AddRecord()
    form2 = DeleteForm()
    return render_template('edit_or_delete.html', route=route, form1=form1, form2=form2, choice=choice)

# result of delete - this function deletes the record
@app.route('/delete_result', methods=['POST'])
def delete_result():
    id = request.form['id_field']
    purpose = request.form['purpose']
    route = Route.query.filter(Route.id == id).first()
    if purpose == 'delete':
        db.session.delete(route)
        db.session.commit()
        message = f"The route {route.name} has been deleted from the database."
        return render_template('result.html', message=message)
    else:
        # this calls an error handler
        abort(405)

# result of edit - this function updates the record
@app.route('/edit_result', methods=['POST'])
def edit_result():
    id = request.form['id_field']
    # call up the record from the database
    route = Route.query.filter(Route.id == id).first()
    # update all values
    route.name = request.form['name']
    route.start = request.form['start']
    route.end = request.form['end']
    route.dangerlevel = request.form['dangerlevel']
    # get today's date from function, above all the routes
    Route.updated = stringdate()

    form1 = AddRecord()
    if form1.validate_on_submit():
        # update database record
        db.session.commit()
        # create a message to send to the template
        message = f"The data for route {Route.name} has been updated."
        return render_template('result.html', message=message)
    else:
        # show validaton errors
        Route.id = id
        # see https://pythonprogramming.net/flash-flask-tutorial/
        for field, errors in form1.errors.items():
            for error in errors:
                flash("Error in {}: {}".format(
                    getattr(form1, field).label.text,
                    error
                ), 'error')
        return render_template('edit_or_delete.html', form1=form1, route=route, choice='edit')


# +++++++++++++++++++++++
# error routes
# https://flask.palletsprojects.com/en/1.1.x/patterns/apierrors/#registering-an-error-handler

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', pagetitle="404 Error - Page Not Found", pageheading="Page not found (Error 404)", error=e), 404

@app.errorhandler(405)
def form_not_posted(e):
    return render_template('error.html', pagetitle="405 Error - Form Not Submitted", pageheading="The form was not submitted (Error 405)", error=e), 405

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', pagetitle="500 Error - Internal Server Error", pageheading="Internal server error (500)", error=e), 500

# +++++++++++++++++++++++

if __name__ == '__main__':
    app.run(debug=True)
