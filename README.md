# language-debates-chat-system

## Site

This repository contains a Django project to host debate experiments.

## Prerequisites

Make sure you have **Python 3.10+** installed. You can download it from [https://www.python.org/downloads/](https://www.python.org/downloads/).

You’ll also need **pip**, Python’s package manager. It usually comes bundled with Python, but if it’s missing, you can install it by running:

```bash
python -m ensurepip --upgrade
```
Or in Linux or IOS:
```bash
sudo apt install python3-pip
```
```bash
brew install python3
```

### Installation

1. Clone the repository: 

```
git clone https://github.com/facuzeta/chat-room-platform.git
```


2. Install the requirements: 

```
cd chat-room-platform\site
pip install -r requirements.txt
```

### Local configurations

1. Create a `.env` file in the folder `mysite`. It should have this Key-Value Pairs defined:

```
SECRET_KEY= #Required
ALLOWED_HOSTS="127.0.0.1 localhost" #Required, you can add any extra hosts

DEBUG=TRUE #Required, TRUE to run in debug mode, FALSE otherwise

EMAIL_HOST= #Email Variables should be set to invite participants by email
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL=
EMAIL_PORT=
EMAIL_USE_TLS=
EMAIL_ADDRESS=

DOMAIN= #Domain is used to create email invitation links

OPEN_AI_API_KEY= #Only if bots with OpenAI models will be used

EXTERNAL_OLLAMA_URL=#Only if bots with Ollama models will be used in a non-local enviroment
EXTERNAL_OLLAMA_KEY=

REDIS_HOST="localhost"
REDIS_PORT=6379 #Default Redis port

POSTGRES_DB_NAME="chatroom" #This should be set to use postgresql instead of sqlite3
POSTGRES_USERNAME="admin"
POSTGRES_PASSWORD=
POSTGRES_HOSTNAME="localhost"
POSTGRES_PORT=5432 #Default Postgresql port

```


2.  Create the database:

```
python manage.py makemigrations
python manage.py migrate
```

3.  Some data is needed to run without issues. You can add the data manually, or run this lines to load the data from previous uses of this project:

```
python manage.py loaddata .\cms\fixtures\data_for_spanish_setup.json
python manage.py loaddata .\group_manager\fixtures\data_for_spanish_experiments.json
```

4. Create a super user: 

```
python manage.py createsuperuser
```

### Running experiments:
To run experiments, the recommended setup is to have Redis and Postgresql running, and run these commands in the "chat-room-platform/site" folder

1. To serve the page: 
```
python manage.py runserver
```

2. To serve the chat websockets:
```
daphne -b 0.0.0.0 -p 8001 mysite.asgi:application
```
3. If you plan to use bots, have celery workers to handle their tasks:

```
celery -A mysite worker
```

## Site Guide:

This will give an overview of the site and how to use it to run experiments

### Manager Overview:

As an superuser you have access to the manager page, which can be reached by going to "*domain*/manager". 

In the starting manager page you can see currently connected participants, select them, and form groups with them. To select the participants, you may select them manually or pick randomly with random selectors. Then create a group experiment by picking the desired experiment to run. You may also add up to 4 bots by selecting a behaviour for each one before picking the experiment.  

To invite participants, you can use the navigation bar to go to "*domain*/manager/invite_participants". You can create participants individually or in groups or email, set an experiment date and send invites.

To check already formed groups, you can use the navigation bar to go to "*your_domain*/manager/groups_list". You can check the status of the formed groups and its participants.

### Experiment Overview:

As an superuser, in "*domain*/admin" you can create experiments objects, experiments questions and stages. The experiments can then be selected in "*your_domain*/manager/" to create a new group to take part in the experiment.

The steps to create a new experiment are:

1- Create a Experiment object.  
    -**Name**: The name shown to the manager when creating groups.  
    -**Input type**: The type of input of the answers of participants.
    -**Instructions s2**: An text that it's added to the HTML to show instructions before the participants starts the chat. An example of use would be the text of an iframe with src=*video* 
    -**Stages names**: The questions of the experiment are debated in Stages that start with "s2_", you can add or remove stages with "s2_" to make experiments with more or less debates. May need to create more Stages objects.
    -**Num Questions s1**: These are the number of question that participants have to answer in the first stage. It has to be equal or higher than the number of debate stages. If its -1, all the questions for that experiment are selected.
    -**Context prompt**: If bot used in experiment, bots will use the prompt written here to have context of the experiment. Can be left empty

2- Stage times are created automatically for each stage for a new experiment, you can modify the timeout duration of each stage in the experiment.
3- Create Question objects for the experiment, there has to be at least the same number of questions as there are debate stages in the experiment.

### Bot Overview:

As an superuser, in "*domain*/admin" you can create bot objects and configure their settings. These bots can then be selected in "*your_domain*/manager/" to add them as new participants when a group is created.

The available attributes to configure the bot are the following:  
-**Behaviour nickname**: The name shown to the manager when creating groups.  
-**Chatroom nickname**: The name shown in the chatroom to other participants, it's the same of the behavior nickname if not defined.  
-**Make random nickname on create**: If enabled, the chatroom nickname will be created randomly choosen from a list of names.  
-**System Prompt**: The system prompt that will be sent every time it has to generate a reply.  
-**Model**: The LLM model the bot will use to generate replies. The currently supported OpenAi models are "gpt-4o-mini", "gpt-4o-mini-2024-07-18" and if used it will connect using the OpenAi API. If any other model is defined, it will try to connect to a local Ollama. (The code to add more models or change API connection is in the Bot model)  
-**Reply probability**: The probability the bot will generate a reply when polled.  
-**Poll time**: The time in seconds between polls. Each poll the bot checks the chat and will use the reply probability to see if it has to generate a reply.  
-**Know own nickname**: If enabled, the bot nickname is added as a system prompt to reduce name confusions. Useful if random nickname is used.  
-**Use current topic**: If enabled, the current debated topic is added as a system prompt  
-**Use all chat history**: If enabled, all the messages in chat history is used when creating replies. Otherwise only recent the messages of the current topic are used.  
-**Use time left threshold**: If enabled, a system prompt is added if the time left for current topic debate is less than the defined time left threshold. It can be used with the System Prompt attribute to have different replies when closer to the end of debate.  
-**Time left Threshold**: The time in seconds that will define when the current debate is close to end. Only matters if Use time left threshold is enabled.  
-**Use defined arguments**: If enabled, a list of arguments for the bot to use in debate is added to the prompt specific of the current topic. Use current topic must be enabled to be used.
-**Empty replies enabled**: If enabled, a system prompt is added which encourage the LLM to give empty replies. The same effect could be achieved by giving similar instructions on the System Prompt attribute.  
-**Temperature**: An hyperparameter for the LLM that controls the randomness of the reply. Used in OpenAI models.  
-**Max tokens**: Limit the number of tokens the model has to generate the reply.

Arguments can be created for a question, and can have also a bot defined. By default every argument of a question is used by every bot when the question is being debated, but if the bot is defined only that bot will use it. This way you can run an experiment with two bots with different configurations, where each bot use different arguments for the same question, but also have some arguments in common.

