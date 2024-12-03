FROM nginx:1.25

RUN rm /etc/nginx/conf.d/default.conf
COPY ./nginx.conf /etc/nginx/conf.d/default.conf

COPY /etc/letsencrypt/live/chat-room-experiment.link/privkey.pem /etc/letsencrypt/live/chat-room-experiment.link/privkey.pem
COPY /etc/letsencrypt/live/chat-room-experiment.link/fullchain.pem /etc/letsencrypt/live/chat-room-experiment.link/fullchain.pem
COPY /etc/letsencrypt/options-ssl-nginx.conf /etc/letsencrypt/options-ssl-nginx.conf
COPY /etc/letsencrypt/ssl-dhparams.pem  /etc/letsencrypt/ssl-dhparams.pem