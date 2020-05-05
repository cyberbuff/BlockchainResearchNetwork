from app import db,create_app
app = create_app()
app.run(debug=True)
db.create_all(app=create_app())