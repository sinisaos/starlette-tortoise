from wtforms import TextAreaField, StringField, Form
from wtforms.validators import InputRequired


class QuestionForm(Form):
    title = StringField("Title", validators=[InputRequired()])
    content = TextAreaField("Content", validators=[InputRequired()])
    tags = StringField("Tags",
                       validators=[InputRequired()])


class AnswerForm(Form):
    content = TextAreaField("Content", validators=[InputRequired()])
