# language-debates-chat-system

## Site

Contains a Django project to run the Chat system we developed for the experiment

## Installation

 1. Clone the repository: 

```
git clone https://github.com/facuzeta/chat-room-platform.git
```


 2. Install the requirements: 

```
cd chat-room-platform\site
pip install -r requirements.txt
```

## Local configurations

 1. Create a `.env` file in the folder `mysite`. It must have at least this Key-Value Pairs defined:

```
SECRET_KEY= "YourSecretKey" 
ALLOWED_HOSTS="127.0.0.1 localhost" #You can add any extra hosts
EMAIL_HOST_PASSWORD= "YourEmailPassword" #You may need to change email configurations at settings.py
DEBUG = "TRUE" #It should remain TRUE to run locally
```

 2.  Create the database:

```
python manage.py makemigrations group_manager cms external_raters chat
python manage.py migrate
```

 3.  Some data is needed to run without issues (cms configurations, group_manager experiments).
   You can add the data manually by running the server and going to the admin page, or run this lines to load the data from previous uses of this project:

```
python manage.py loaddata .\cms\fixtures\data_for_spanish_setup.json
python manage.py loaddata .\group_manager\fixtures\data_for_spanish_experiments.json
```


 4. Create a super user: 

```
python manage.py createsuperuser
```

## Run the server with:

```
daphne mysite.asgi:application
```
