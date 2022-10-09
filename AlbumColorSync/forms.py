from wtforms import StringField, SelectField, SubmitField, RadioField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired


class AlbumSelectForm(FlaskForm):
    album_choice = SelectField("Vinyl List", validators=[DataRequired()], coerce=int)
    submit = SubmitField("Select Album")


class VinylUpdateForm(FlaskForm):
    album_name = StringField("Album Name", validators=[DataRequired()])
    artist_name = StringField("Artist Name", validators=[DataRequired()])
    submit = SubmitField("Add New Vinyl")


class SpotifyAlbumForm(FlaskForm):
    album_choices = RadioField("Album Suggestions", validators=[DataRequired()], coerce=int)
    submit = SubmitField()
